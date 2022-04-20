"""Модуль для вспомогательных функций."""
from Sync_app.models import MoySkladDBGood, KonturMarketDBGood
from django.db import models

def db_fill_comp_table(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
    """Функция заполняет таблицу Compilance в БД, на основе данных googlesheets_copm_table.
    :param googlesheets_copm_table: Список, элементам которого - список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает список наименований для которых не удалось сделать запись в БД.
    """

    if not googlesheets_copm_table:
        return False

    for good in googlesheets_copm_table:
        # Если в таблице соотвествия из googlesheets, не усnановлено соотвествие - второй элемент будет пустой,
        # то пропускаем строку.
        if len(good) > 1:
            # Будет встречаться 2 вида записей
            # 1. 4Пивовара - Вброс, Бакунин - How Much Is Too Much [Raspberry],
            # Степь и Ветер - Smoothie Mead: Raspberry, Black Currant, Mint
            # 2 Barbe Ruby, Barista Chocolate Quad
            # Проверяем на наличие в строке ' - '
            if good[0].find(' - ') == -1:
                ms_good = MoySkladDBGood.objects.filter(name=name).filter(is_draft=False)
            else:
                brewery = good[0].split(' - ')[0]
                name = good[0].split(' - ')[1]
                ms_good = MoySkladDBGood.objects.filter(brewery=brewery).filter(name=name).filter(is_draft=False)

            # В googlesheets не указыватеся разливное пиво
            try:
                egias_good = KonturMarketDBGood.objects.get(egais_code=good[1])
            except Exception:
                a = 1
            if not egias_good.is_draft:
                a=1


    return False
