"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
from typing import List

from django.db import models
from Sync_app.konturmarket.konturmarket_class_lib import StockEGAIS
from Sync_app.models.app_models import Capacity


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
        max_length=200, help_text="Короткое наименование производителя"
    )

    full_name = models.CharField(
        max_length=255, help_text="Полное наименование производителя"
    )


class KonturMarketDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

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
        max_length=200, help_text="Полное ЕГАИС наименование товара"
    )

    # Внешний ключ на модель, таблицу производителя
    fsrar = models.ForeignKey(
        KonturMarketDBProducer,
        on_delete=models.CASCADE,
        help_text="Уникальный ЕГАИС идентификатор производителя",
    )

    # Объем продукции. Если не указан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    capacity = models.ForeignKey(
        Capacity,
        help_text="Емкость тары",
        on_delete=models.PROTECT,
    )

    # Объем продукции. Если не указан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    # Признак разливной продукции. Рассчитываемый параметр: если capacity > 1л, то принимаем что товар разливной -
    # объем расчетный
    is_draft = models.BooleanField(
        # По умолчанию ставим в False
        default=False,
        help_text="Признак разливного пива",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "full_name",
                ]
            ),
        ]

    @staticmethod
    def save_objects_to_db(list_km_goods: List[StockEGAIS]) -> None:
        """Метод сохранения данных о товарах в БД."""
        if not list_km_goods:
            return

        km_good: StockEGAIS
        for km_good in list_km_goods:
            producer = KonturMarketDBProducer(
                fsrar=km_good.good.brewery.fsrar_id,
                inn=km_good.good.brewery.inn,
                short_name=km_good.good.brewery.short_name,
                full_name=km_good.good.brewery.full_name,
            )

            # Если нет объема продукции, то считаем, что товар разливной, объемом 99 л
            capacity = None
            if km_good.good.capacity is None:
                # Проверяем есть запись в таблице емкостей
                # если такой записи все еще нет в таблице, то создаем ее
                capacity = Capacity.objects.get_or_create(capacity=99)
            else:
                # Проверяем есть запись в таблице емкостей
                # если такой записи все еще нет в таблице, то создаем ее
                capacity = Capacity.objects.get_or_create(
                    capacity=km_good.good.capacity
                )

            good = KonturMarketDBGood(
                egais_code=km_good.good.alco_code,
                full_name=km_good.good.name,
                fsrar=producer,
                capacity=capacity,
                is_draft=capacity.capacity > 10,
            )

            stock = KonturMarketDBStock(quantity=km_good.quantity_2, egais_code=good)

            producer.save()
            good.save()
            stock.save()


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
    )
