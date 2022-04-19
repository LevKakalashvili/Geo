"""Модуль для вспомогательных функций."""
from Sync_app.models import MoySkladDBGood
from django.db import models

def db_fill_comp_table(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
    """Функция заполняет таблицу Compilance в БД, на основе данных googlesheets_copm_table.
    :param googlesheets_copm_table: Список, элементам которого - список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает список наименований для которых не удалось сделать запись в БД.
    """

    if not googlesheets_copm_table:
        return False
    # Если в таблице соотвествия из googlesheets, не усnановлено соотвествие - второй элемент будет пустой,
    # то пропускаем строку.
    # Сначала нужно узнать отностится ли данный код АП к розливному пиву или к фасвке. Дл этого нужно сделать запрос
    # в таблицe ЕГАИС и узнать емкость продукта по коду АП
    # Потом пытаемся найти uuid, с учетом емкости товарной еденицы, для наименования, если нашли сохраняем в БД соотвествие, иначе добавляем
    # в возвращаемый список
    for good in googlesheets_copm_table:
        brewery = good[0].split(' - ')[0]
        name = good[0].split(' - ')[1]
        a = MoySkladDBGood.objects\
            .filter(brewery=brewery)\
            .filter(name=name)
        b = 1

    return False
