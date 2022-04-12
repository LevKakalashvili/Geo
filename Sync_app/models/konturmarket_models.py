"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
from typing import List

from django.db import models

from Sync_app.konturmarket.konturmarket_class_lib import GoodEGAIS as StockEGAIS


class KonturMarketDBProducer(models.Model):
    """Класс описывает модель производителя, продукции в соответствии с терминами ЕГАИС."""

    fsrar_id = models.CharField(primary_key=True,
                                max_length=12,
                                unique=True,
                                db_column='fsrar_id',
                                help_text='Уникальный ЕГАИС идентификатор производителя')

    # ИНН. Для зарубежных производителей может быть пустым
    inn = models.CharField(max_length=12, help_text='ИНН производителя', null=True)

    short_name = models.CharField(max_length=200, help_text='Короткое наименование производителя')

    full_name = models.CharField(max_length=300, unique=True, help_text='Полное наименование производителя')


class KonturMarketDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    # Код алкогольной продукции
    egais_code = models.CharField(primary_key=True,
                                  max_length=19,
                                  unique=True,
                                  db_column='egais_code',
                                  help_text='Код алкогольной продукции (код АП) в ЕГАИС')

    # ЕГАИС наименование
    full_name = models.CharField(max_length=200, unique=True, help_text='Полное ЕГАИС наименование товара')

    # Внешний ключ на модель, таблицу производителя
    fsrar_id = models.ForeignKey(KonturMarketDBProducer,
                                 on_delete=models.CASCADE,
                                 db_column='fsrar_id')

    @staticmethod
    def save_objects_to_storage(list_km_goods: List[StockEGAIS]):
        """Метод сохранения данных о товарах в БД."""
        if list_km_goods:
            for km_good in list_km_goods:
                producer = KonturMarketDBProducer(fsrar_id=km_good.good.brewery.fsrar_id,
                                                  inn=km_good.good.brewery.inn,
                                                  short_name=km_good.good.brewery.short_name,
                                                  full_name=km_good.good.brewery.full_name
                                                  )

                good = KonturMarketDBGood(egais_code=km_good.good.alco_code,
                                          full_name=km_good.good.name,
                                          # fsrar_id=km_good.good.brewery.fsrar_id
                                          fsrar_id=producer
                                          )

                stock = KonturMarketDBStock(quantity=km_good.quantity,
                                            egais_code=good)
                producer.save()
                good.save()
                stock.save()
        pass


class KonturMarketDBStock(models.Model):
    """Класс описывает модель остатка по товару в системе ЕГАИС."""

    # Количество товара на складе
    quantity = models.PositiveSmallIntegerField(help_text='Остаток товара на остатках в ЕГАИС')

    # Код алкогольной продукции
    egais_code = models.OneToOneField(KonturMarketDBGood,
                                      on_delete=models.CASCADE,
                                      primary_key=True,
                                      db_column='egais_code',
                                      help_text='Код алкогольной продукции (код АП) в ЕГАИС')
