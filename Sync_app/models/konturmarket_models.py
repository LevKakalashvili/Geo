"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
import datetime
import sys
from operator import itemgetter
from typing import TYPE_CHECKING, Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from Sync_app.models.moysklad_models import (
    MoySkladDBGood, MoySkladDBRetailDemand,
)
from Sync_app.moysklad.moysklad_constants import GoodType

if TYPE_CHECKING:
    import Sync_app.konturmarket.konturmarket_class_lib as km_class


class KonturMarketDBProducer(models.Model):
    """Класс описывает модель производителя, продукции в соответствии с терминами ЕГАИС."""

    fsrar = models.CharField(
        primary_key=True,
        max_length=12,
        help_text="Уникальный ЕГАИС идентификатор производителя",
    )

    # ИНН. Для зарубежных производителей может быть пустым
    inn = models.CharField(max_length=12, help_text="ИНН производителя", null=True)

    short_name = models.CharField(
        max_length=200,
        help_text="Короткое наименование производителя",
    )

    full_name = models.CharField(
        max_length=255,
        help_text="Полное наименование производителя",
    )


class KonturMarketDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    class Meta:

        verbose_name = "Товар (Контур.Маркет)"
        verbose_name_plural = "Товары (Контур.Маркет)"

        """Индексы."""

        indexes = [
            models.Index(
                fields=[
                    "full_name",
                ],
            ),
        ]

    # Код алкогольной продукции
    egais_code = models.CharField(
        primary_key=True,
        max_length=19,
        help_text="Код алкогольной продукции (код АП) в ЕГАИС",
    )

    # ЕГАИС наименование
    # Одно и то же пиво может быть с разными кодами алкогольной продукции:
    # 1. разный объем 'Пиво светлое пастеризованное фильтрованное 'Петрюс Блонд' 0,33 и 0,75
    # 2. разные импортеры, дилеры могут поставить разные кода АП
    # поэтому уникальность поля не требуется
    full_name = models.CharField(
        max_length=200,
        help_text="Полное ЕГАИС наименование товара",
    )

    # Объем продукции. Если не указан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    capacity = models.DecimalField(max_digits=5, decimal_places=3, help_text="Емкость тары")

    # Объем продукции. Если не указан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    # Признак разливной продукции. Рассчитываемый параметр: если capacity > 1л, то принимаем что товар разливной -
    # объем расчетный
    is_draft = models.BooleanField(
        # По умолчанию ставим в False
        default=False,
        help_text="Признак разливного пива",
    )

    # Код алкогольной продукции
    kind_code = models.IntegerField(
        default=None,
        help_text="Код вида продукции",
    )

    # Внешний ключ на модель, таблицу производителя
    fsrar = models.ForeignKey(
        KonturMarketDBProducer,
        on_delete=models.CASCADE,
        help_text="Уникальный ЕГАИС идентификатор производителя",
    )

    @staticmethod
    def save_objects_to_db(list_km_goods: List["km_class.StockEGAIS"]) -> bool:
        """Метод сохраняет товары в БД."""
        if not list_km_goods:
            return False

        km_good: km_class.StockEGAIS
        for km_good in list_km_goods:
            producer = KonturMarketDBProducer(
                fsrar=km_good.good.brewery.fsrar_id,
                inn=km_good.good.brewery.inn,
                short_name=km_good.good.brewery.short_name,
                full_name=km_good.good.brewery.full_name,
            )

            good = KonturMarketDBGood(
                egais_code=km_good.good.alco_code,
                full_name=km_good.good.name,
                fsrar=producer,
                # Если нет объема продукции, то считаем, что товар разливной, объемом 99 л
                capacity=km_good.good.capacity if km_good.good.capacity else 99,
                # Т.к. km_good.good.capacity может быть None
                is_draft=True if km_good.good.capacity is None or km_good.good.capacity > 10 else False,
                kind_code=km_good.good.kind_code,
            )

            stock = KonturMarketDBStock(quantity=km_good.quantity_2, egais_code=good)

            producer.save()
            good.save()
            stock.save()

        return True

    @staticmethod
    def get_sales_journal_from_db(date_: datetime.date) -> List[Dict[str, Union[str, int]]]:
        """Метод для получения журнала розничных продаж алкоголя из БД."""

        sales: List[Dict[str, str | int]] = []

        all_sold_ms_goods = (
            MoySkladDBRetailDemand.objects.select_related("uuid")
            .filter(demand_date__exact=date_)
            .filter(uuid__is_draft=False)
            .exclude(uuid__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE])
            .prefetch_related("uuid__egais_code")
            .prefetch_related("uuid__egais_code__konturmarketdbstock")
            .filter(uuid__egais_code__konturmarketdbstock__quantity__gt=0)
        )

        quantity: int = 0

        for good in all_sold_ms_goods:
            for km_good in good.uuid.egais_code.all():
                # Если остаток товара в ЕГАИС = 0
                if not km_good.konturmarketdbstock.quantity:
                    continue

                # Если товара в ЕГАИС больше, чем продано
                if km_good.konturmarketdbstock.quantity >= good.quantity:
                    quantity = good.quantity
                    good.quantity = 0
                    km_good.konturmarketdbstock.quantity -= good.quantity
                # Если товара в ЕГАИС меньше, чем продано
                elif km_good.konturmarketdbstock.quantity < good.quantity:
                    quantity = km_good.konturmarketdbstock.quantity
                    good.quantity -= km_good.konturmarketdbstock.quantity
                    km_good.konturmarketdbstock.quantity = 0

                sales.append(
                    {
                        "commercial_name": good.uuid.full_name,
                        "name": km_good.full_name,
                        "alcCode": km_good.egais_code,
                        "apCode": km_good.kind_code,
                        "volume": km_good.capacity,
                        "quantity": quantity,
                        "price": good.uuid.price,
                    },
                )

        sales = sorted(sales, key=itemgetter("commercial_name"))
        return sales

    def __str__(self):
        return f"{self.full_name}: {self.egais_code}"

class KonturMarketDBStock(models.Model):
    """Класс описывает модель остатка по товару в системе ЕГАИС."""

    # Количество товара на складе
    quantity = models.PositiveSmallIntegerField(
        help_text="Остаток товара на остатках в ЕГАИС на 2ом регистре",
        null=True,
    )

    # Код алкогольной продукции
    egais_code = models.OneToOneField(
        KonturMarketDBGood,
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="Код алкогольной продукции (код АП) в ЕГАИС",
        db_column="egais_code",
    )
