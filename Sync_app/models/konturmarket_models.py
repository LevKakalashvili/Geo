"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
from typing import List

from django.db import models

from Sync_app.konturmarket.konturmarket_class_lib import StockEGAIS


class KonturMarketDBProducer(models.Model):
    """Класс описывает модель производителя, продукции в соответствии с терминами ЕГАИС."""

    fsrar_id = models.CharField(primary_key=True,
                                max_length=12,
                                unique=True,
                                db_column='fsrar_id',
                                help_text='Уникальный ЕГАИС идентификатор производителя')

    # ИНН. Для зарубежных производителей может быть пустым
    inn = models.CharField(max_length=12,
                           help_text='ИНН производителя',
                           null=True)

    short_name = models.CharField(max_length=200,
                                  help_text='Короткое наименование производителя')

    full_name = models.CharField(max_length=255,
                                 # unique=True,
                                 help_text='Полное наименование производителя')


class KonturMarketDBGood(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    # Код алкогольной продукции
    egais_code = models.CharField(primary_key=True,
                                  max_length=19,
                                  unique=True,
                                  db_column='egais_code',
                                  help_text='Код алкогольной продукции (код АП) в ЕГАИС')

    # ЕГАИС наименование
    # Одно и то же пиво может быть с разными кодами алкогольной продукции:
    # 1. разный объем 'Пиво светлое пастеризованное фильтрованное 'Петрюс Блонд' 0,33 и 0,75
    # 2. разные импортеры, дилеры могут поставить разные кода АП
    # поэтому уникальность поля не требуется
    full_name = models.CharField(max_length=200,
                                 help_text='Полное ЕГАИС наименование товара')

    # Внешний ключ на модель, таблицу производителя
    fsrar_id = models.ForeignKey(KonturMarketDBProducer,
                                 on_delete=models.CASCADE,
                                 db_column='fsrar_id')

    # Объем продукции. Если не укзан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    capacity = models.FloatField(db_column='capacity',
                                 null=True,
                                 help_text='Объем алкогольной продукции')

    # Объем продукции. Если не укзан, то считаем, что позиция разливная и нужно выставить флаг,
    # что объем расчетный
    is_calculated = models.BooleanField(db_column='is_calculated',
                                        # По умолчанию ставим в False
                                        default=False,
                                        help_text='Признак того, что объем был рассчитан, f не прочитан из Контур.Маркет')

    # Признак разливной продукции. Расчитываемый параметр: если capacity > 1л, то принимаем что товар разливной
    # что объем расчетный
    is_draft = models.BooleanField(db_column='is_draft',
                                        # По умолчанию ставим в False
                                        default=False,
                                        help_text='Признак разливного пива')

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
                                          fsrar_id=producer,
                                          # Если нет объема продукции, то считаем, что товар разливной, объемом 30л
                                          capacity=km_good.good.capacity if (km_good.good.capacity is not None) else 30,
                                          # Если нет объема продукции, то считаем, что товар разливной, объемом 30л
                                          # и выставляем признак, что объем расчетный
                                          # т.к. розлив может быть и 20л и 30л и 50л
                                          is_calculated= True if (km_good.good.capacity is None) else False,
                                          is_draft=True if (km_good.good.capacity is not None) and
                                                           (km_good.good.capacity > 1) else False
                                          )

                stock = KonturMarketDBStock(quantity=km_good.quantity_2,
                                            egais_code=good)

                producer.save()
                good.save()
                stock.save()


class KonturMarketDBStock(models.Model):
    """Класс описывает модель остатка по товару в системе ЕГАИС."""

    # Количество товара на складе
    quantity = models.PositiveSmallIntegerField(help_text='Остаток товара на остатках в ЕГАИС на 2ом регистре',
                                                null=True
                                                )

    # Код алкогольной продукции
    egais_code = models.OneToOneField(KonturMarketDBGood,
                                      on_delete=models.CASCADE,
                                      primary_key=True,
                                      db_column='egais_code',
                                      help_text='Код алкогольной продукции (код АП) в ЕГАИС')
