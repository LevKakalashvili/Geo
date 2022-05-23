"""Общие модели для приложения."""
from django.db import models


class Capacity(models.Model):
    """Модель описывает таблицу емкостей товаров."""

    capacity = models.DecimalField(
        primary_key=True,
        max_digits=5,
        decimal_places=3,
        help_text="Объем алкогольной продукции",
    )
