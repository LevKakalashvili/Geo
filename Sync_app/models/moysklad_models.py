"""Модуль содержит описание моделей для работы с МойСклад."""
from typing import TYPE_CHECKING, List

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.utils import IntegrityError

import Sync_app.moysklad.moysklad_constants as ms_const

if TYPE_CHECKING:
    import Sync_app.moysklad.moysklad_class_lib as ms_class


class MoySkladDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    class Meta:
        """Индексы и ограничения для таблицы."""

        indexes = [
            models.Index(
                fields=[
                    "full_name",
                ],
            ),
            models.Index(
                fields=[
                    "brewery",
                ],
            ),
            models.Index(
                fields=[
                    "name",
                ],
            ),
        ]

        constraints = [
            CheckConstraint(
                check=Q(bev_type__in=["".join(element.value) for element in ms_const.GoodType]),
                name="valid_good_type",
            ),
        ]

    # UUID товара
    uuid = models.CharField(
        primary_key=True,
        max_length=36,
        unique=True,
        help_text="Уникальный идентификатор товара",
    )
    # Родительский UUID товара
    parent_uuid = models.CharField(
        max_length=36,
        help_text="Уникальный идентификатор родительского товара. " "Для модификация товаров",
    )
    # Полное наименование товара.
    # Использовать нужно только для связки данных из КонтурМаркет
    full_name = models.CharField(max_length=200, unique=True, help_text="Полное имя товара")
    # Путь, папка
    path_name = models.CharField(max_length=100, help_text="Папка товара")
    # Стиль
    style = models.CharField(max_length=100, help_text="Стиль пива, если товар - пиво")
    # Цена товара
    price = models.DecimalField(max_digits=5, decimal_places=2, help_text="Цена товара")
    # Наименование пивоварни
    brewery = models.CharField(max_length=100, help_text="Наименование пивоварни")
    # Наименование пива
    name = models.CharField(max_length=100, help_text="Наименование товара")
    # Содержание алкоголя
    abv = models.FloatField(help_text="Содержание алкоголя")
    # Плотность
    og = models.FloatField(help_text="Начальная плотность")
    # Горечь
    ibu = models.PositiveSmallIntegerField(help_text="Горечь")
    # Признак алкогольной продукции
    is_alco = models.BooleanField(help_text="Признак алкогольного напитка", default=False)
    # Признак разливного пива
    is_draft = models.BooleanField(help_text="Признак разливного пива", default=False)
    # Тип продукта (пиво, сидр, медовуха, комбуча, лимонад)
    bev_type = models.CharField(
        max_length=8,
        choices=[("".join(element.value), "".join(element.value)) for element in ms_const.GoodType],
        help_text="Тип продукта",
    )
    # Емкость тары
    capacity = models.DecimalField(max_digits=5, decimal_places=3, help_text="Емкость тары")
    # Код ЕГАИС
    egais_code = models.ManyToManyField(
        "KonturMarketDBGood", help_text="Код алкогольной продукции", related_name="goods",
    )

    @staticmethod
    def save_objects_to_db(list_ms_goods: List["ms_class.Good"]) -> bool:
        """Метод сохраняет объекты, созданные на основе списка list_ms_goods в БД."""
        for ms_good in list_ms_goods:
            # Если текущий товар - не комплект из товаров
            # (разливное пиво заведено как отдельный товар с припиской (0,5),
            # а 1л - комплект из двух товаров 0,5
            if ms_good.quantity is None:
                continue

            parsed_name = ms_good.parse_object()

            # Заполняем товар
            good = MoySkladDBGood(
                uuid=ms_good.good_id,
                parent_uuid=ms_good.parent_id,
                full_name=ms_good.name,
                # Если модификация товара
                path_name=ms_good.path_name or "",
                price=ms_good.price[0].value / 100,
                brewery=parsed_name.brewery,
                name=parsed_name.name,
                og=parsed_name.og,
                abv=parsed_name.abv,
                ibu=parsed_name.ibu,
                is_alco=parsed_name.is_alco,
                is_draft=parsed_name.is_draft,
                bev_type=parsed_name.bev_type,
                style=parsed_name.style,
                capacity=parsed_name.capacity,
            )

            stocks = MoySkladDBStock(
                uuid=good,
                # Если по какой-то причине остаток товара в МойСклад отрицательный в БД сохраняем 0
                quantity=ms_good.quantity if ms_good.quantity >= 0 else 0,
            )
            try:
                # Сохраняем товары в таблицу
                good.save()
                # Сохраняем остатки в таблицу
                stocks.save()
            except IntegrityError as error:
                # TODO: переделать на логгер или Sentry
                print(f"\nWARNING! {error.args[1]}")
        return True


class MoySkladDBStock(models.Model):
    """Класс описывает модель остатка по товару."""

    # Количество товара на складе. Может отсутствовать, если товар - комплект
    quantity = models.PositiveSmallIntegerField(help_text="Остаток товара на складе")
    # UUID товара
    uuid = models.OneToOneField(
        MoySkladDBGood,
        on_delete=models.CASCADE,
        primary_key=True,
        help_text="Уникальный идентификатор товара",
    )


class MoySkladDBRetailDemand(models.Model):
    """Класс описывает модель розничной продажи продаж."""

    # Дата продажи
    demand_date = models.DateField(null=True, blank=True, default=None, help_text="Дата продажи")

    # Количество проданного товара
    quantity = models.PositiveSmallIntegerField(help_text="Остаток товара на складе")

    # UUID проданного товара
    uuid = models.ForeignKey(
        MoySkladDBGood,
        help_text="Идентификатор проданного товара",
        on_delete=models.DO_NOTHING,
        db_column="uuid",
    )

    @staticmethod
    def save_objects_to_db(list_retail_demand: List["ms_class.RetailDemandPosition"]) -> bool:
        """Метод сохраняет объекты, созданные на основе списка list_retail_demand в БД."""
        if not list_retail_demand:
            return False

        # Получаем список всех проданного пива
        sold_goods = MoySkladDBGood.objects.filter(uuid__in=[_.good_id for _ in list_retail_demand])
        # Чистим таблицу
        MoySkladDBRetailDemand.objects.all().delete()
        save_list: List[MoySkladDBRetailDemand] = []
        # Сохраняем проданные товары
        for good in list_retail_demand:
            try:
                save_list.append(
                    MoySkladDBRetailDemand(
                        uuid=sold_goods.get(uuid=good.good_id),
                        quantity=good.quantity,
                        demand_date=good.demand_date,
                    ),
                )
            except ObjectDoesNotExist:
                continue
        # Сохраняем продажи в БД
        MoySkladDBRetailDemand.objects.bulk_create(save_list)
        return True
