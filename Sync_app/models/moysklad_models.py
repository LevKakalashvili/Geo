"""Модуль содержит описание моделей для работы с МойСклад."""
from typing import List

from django.db import models

from Sync_app.moysklad.moysklad_class_lib import Good as MoySkladGood


class Good(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    # UUID товара
    uuid = models.CharField(primary_key=True,
                            max_length=36,
                            unique=True,
                            help_text='Уникальный идентификатор товара')
    # Родительский UUID товара
    parent_uuid = models.CharField(max_length=36,
                                   help_text='Уникальный идентификатор родительского товара. '
                                             'Для модификация товаров')
    # Полное наименование товара.
    # Использовать нужно только для связки данных из КонутрМаркет
    full_name = models.CharField(max_length=200, unique=True, help_text='Полное имя товара')
    # Путь, папка
    path_name = models.CharField(max_length=100, help_text='Папка товара')
    # Стиль
    style = models.CharField(max_length=100, help_text='Стиль пива, если товар - пиво')
    # Цена товара
    price = models.DecimalField(max_digits=5, decimal_places=2, help_text='Цена товара')
    # Наименование пивоварни
    brewery = models.CharField(max_length=100, help_text='Наименование пивоварни')
    # Наименование пива
    name = models.CharField(max_length=100, help_text='Наименование товара')
    # Содержание алкоголя
    abv = models.FloatField(help_text='Содержание алкоголя')
    # Плотность
    og = models.FloatField(help_text='Начальная плотность')
    # Горечь
    ibu = models.PositiveSmallIntegerField(help_text='Горечь')
    # Признак алкогольной продукции
    is_alco = models.BooleanField(help_text='Признак алкогольного напитка')
    # Признак разливного пива
    is_draft = models.BooleanField(help_text='Признак пива')
    # Признак сидр или нет
    is_cider = models.BooleanField(help_text='Признак розливного пива')

    @staticmethod
    def save_objects_to_storage(list_ms_goods: List[MoySkladGood]):
        """Метод сохраняет объекты, созданные на основе списка list_ms_goods в БД."""
        if list_ms_goods:
            for ms_good in list_ms_goods:
                # Если текущий товар - не комплект из товаров
                # (розливное пиво заведено 0,5л - отдельный товар,
                # а 1л - комплект из двух товаров 0,5
                if ms_good.quantity is not None:
                    parced_name = ms_good.parse_name
                    # Заполняем товар
                    good = Good(
                        uuid=ms_good.id,
                        parent_uuid=ms_good.parent_id,
                        full_name=ms_good.name,
                        # Если модификация товара
                        path_name=ms_good.path_name if ms_good.path_name is not None else '',
                        price=ms_good.price[0].value / 100,
                        brewery=parced_name.brewery,
                        name=parced_name.name,
                        og=parced_name.og,
                        abv=parced_name.abv,
                        ibu=parced_name.ibu,
                        is_alco=parced_name.is_alco,
                        is_draft=parced_name.is_draft,
                        is_cider=parced_name.is_cider,
                        style=parced_name.style,
                    )
                    good.save()
                    # Заполняем остатки
                    stoks = Stock(
                        uuid=good,
                        quantity=ms_good.quantity)
                    stoks.save()


class Stock(models.Model):
    """Класс описывает модель остатка по товару."""

    # Количество товара на складе. Может отсутсвовать, если товар - комплект
    quantity = models.PositiveSmallIntegerField(help_text='Остаток товара на складе')
    # UUID товара
    uuid = models.OneToOneField(Good,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                db_column='uuid',
                                help_text='Уникальный идентификатор товара')
