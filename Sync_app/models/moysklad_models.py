"""Модуль содержит описание моделей для работы с МойСклад."""
from typing import List

from django.db import models
from Sync_app.models.konturmarket_models import KonturMarketDBGood
from Sync_app.moysklad.moysklad_class_lib import Good as MoySkladGood


class MoySkladDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

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
        help_text="Уникальный идентификатор родительского товара. "
        "Для модификация товаров",
    )
    # Полное наименование товара.
    # Использовать нужно только для связки данных из КонтурМаркет
    full_name = models.CharField(
        max_length=200, unique=True, help_text="Полное имя товара"
    )
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
    is_alco = models.BooleanField(
        help_text="Признак алкогольного напитка", default=False
    )
    # Признак разливного пива
    is_draft = models.BooleanField(help_text="Признак разливного пива", default=False)
    # Признак сидр или нет
    is_cider = models.BooleanField(help_text="Признак сидра", default=False)
    # Признак пиво или нет
    is_beer = models.BooleanField(help_text="Признак пива", default=False)
    # Емкость тары
    capacity = models.DecimalField(max_digits=5, decimal_places=3, help_text="Емкость тары")
    # Код ЕГАИС
    egais_code = models.ManyToManyField(
        KonturMarketDBGood, help_text="Код алкогольной продукции"
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "full_name",
                ]
            ),
            models.Index(
                fields=[
                    "brewery",
                ]
            ),
            models.Index(
                fields=[
                    "name",
                ]
            ),
        ]

    @staticmethod
    def save_objects_to_db(list_ms_goods: List[MoySkladGood]) -> None:
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
                is_cider=parsed_name.is_cider,
                style=parsed_name.style,
                capacity=parsed_name.capacity,
                is_beer=parsed_name.is_beer,
            )
            good.save()
            # Заполняем остатки
            stocks = MoySkladDBStock(
                uuid=good,
                # Если по какой-то причине остаток товара в МойСклад отрицательный в БД сохраняем 0
                quantity=ms_good.quantity if ms_good.quantity >= 0 else 0,
            )
            stocks.save()


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
