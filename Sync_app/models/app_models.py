"""Общие модели для приложения."""
from django.db import models


class Capacity(models.Model):
    """Модель описывает таблицу емкостей товаров."""

    capacity = models.FloatField(unique=True, help_text="Объем алкогольной продукции")
