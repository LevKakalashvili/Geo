"""Модуль содержит описание моделей для работы с Контур.Маркет."""
from typing import List

from django.db import models

from Sync_app.konturmarket.konturmarket_class_lib import GoodEGAIS as KonturMarketGood

class KonturMarketDBProducer(models.Model):
    """Клаcс описывает модель производителя, продукции в соответствии с терминами ЕГАИС."""

    fsrar_id = models.CharField(primary_key=True,
                                max_length=12,
                                unique=True,
                                help_text='Уникальный ЕГАИС идентификатор производителя')

    # ИНН для зарубежны производителей может быть пустым
    inn = models.CharField(max_length=12, help_text='ИНН производителя')

    short_name = models.CharField(max_length=200, help_text='Короткое наименование производителя')

    full_name = models.CharField(max_length=300, unique=True, help_text='Полное наименование производителя')

class KonturMarketDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    # Код алкогольной продукции
    egais_сode = models.CharField(primary_key=True,
                            max_length=19,
                            unique=True,
                            help_text='Код алкогольной продукции (код АП) в ЕГАИС')

    # ЕГАИС наименование
    full_name = models.CharField(max_length=200, unique=True, help_text='Полное ЕГАИС наименование товара')

    fsrar_id = models.ManyToOneRel()

    @staticmethod
    def save_objects_to_storage(list_km_goods: List[KonturMarketGood]):
        """Метод сохраниния данных о товарах в БД."""
        pass

class KonturMarketDBStock(models.Model):
    """Класс описывает модель остатка по товару в системе ЕГАИС."""

    # Количество товара на складе. Может отсутсвовать, если товар - комплект
    quantity = models.PositiveSmallIntegerField(help_text='Остаток товара на остатках в ЕГАИС')
    # UUID товара
    egais_сode = models.One(MoySkladDBGood,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                db_column='egais_сode',
                                help_text='Код алкогольной продукции (код АП) в ЕГАИС')

