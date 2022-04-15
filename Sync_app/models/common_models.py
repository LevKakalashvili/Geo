"""Модуль содержит описание моделей для работы самого сервиса, приложения."""
from django.db import models
from Sync_app.models.konturmarket_models import KonturMarketDBGood
from Sync_app.models.moysklad_models import MoySkladDBGood


class Compilance(models.Model):
    """Класс описывает модель таблицы соотвествия, кодов товаров и кодов алкогольной продукции.
    Коды товаров - коды товаров из сервиса МойСклад.
    Коды алкгольной продукции ЕГАИС - коды товаров из сервиса Контур.Маркет."""

    # Внешний ключ на модель товара Контур.Маркета
    egais_code = models.ForeignKey(KonturMarketDBGood,
                                   on_delete=models.CASCADE,
                                   db_column='egais_code',
                                   help_text='Код алкогольной продукции (код АП) в ЕГАИС',
                                   )

    # Внешний ключ на модель товара МойСклад
    uuid = models.ForeignKey(MoySkladDBGood,
                                   on_delete=models.CASCADE,
                                   db_column='uuid',
                                   help_text='Уникальный идентификатор товара',
                                   )


