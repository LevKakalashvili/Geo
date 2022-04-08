"""Модуль содержит описание моделей для работы с Контур.Маркет."""
from typing import List

from django.db import models

from Sync_app.konturmarket.konturmarket_class_lib import GoodEGAIS as KonturMarketGood

class Good(models.Model):
    """Класс описывает модель для работы с товарами из сервиса МойСклад."""

    @staticmethod
    def save_objects_to_storage(list_km_goods: List[KonturMarketGood]):
        """Метод сохраниния данных о товарах в БД."""
        pass
