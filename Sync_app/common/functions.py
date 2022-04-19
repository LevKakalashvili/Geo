"""Модуль для вспомогательных функций."""
from Sync_app.models.moysklad_models import MoySkladDBGood as q
from django.db import models

def db_fill_comp_table(googlesheets_copm_table: list[list[str]]) -> bool:
    """Функция заполняет таблицу Compilance в БД, на основе данных googlesheets_copm_table.
    :param googlesheets_copm_table: Список, элементам которого - список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает True в случае удачной записи в БД, False в случае ошибки.
    """

    if not googlesheets_copm_table:
        return False
    for good in googlesheets_copm_table:
        pass
    return False
