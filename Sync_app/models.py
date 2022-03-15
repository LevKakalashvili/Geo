from django.db import models
from Sync_app.moysklad.moysklad_class_lib import Good as MoySkladGood
from typing import List

class Good(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад"""
    # UUID товара
    uuid = models.CharField(primary_key=True, max_length=36, unique=True)
    # Родительский UUID товара
    parent_uuid = models.CharField(max_length=36)
    # Наименование товара
    name = models.CharField(max_length=200, unique=True)
    # Путь, папка
    path_name = models.CharField(max_length=100)
    # Цена товара
    price = models.DecimalField(max_digits=5, decimal_places=2)
    # Количество товара на складе. может отсутсвовать, если товар - комплект
    quantity = models.PositiveSmallIntegerField()

    @staticmethod
    def create_and_save_objects_from_list(list_ms_goods: List[MoySkladGood]):
        """Метод создает и сохраняет объекты, созданные на основе списка list_ms_goods."""
        if not list_ms_goods:
            return []

        for ms_good in list_ms_goods:
            # Если текущий товар - не комплект из товаров
            # (розливное пиво заведено 0,5л - отдельный товар, а 1л - комплект из двух товаров 0,5
            if ms_good.quantity is not None:
                # Если модификация товрва
                good = Good(
                    uuid=ms_good.id,
                    parent_uuid=ms_good.parent_id,
                    name=ms_good.name,
                    path_name=ms_good.path_name if ms_good.path_name is not None else '',
                    price=ms_good.price[0].value/100,
                    quantity=ms_good.quantity
                )
                good.save()
