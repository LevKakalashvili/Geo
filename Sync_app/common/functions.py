"""Модуль для вспомогательных функций."""
from typing import Any, List
from Sync_app.models import MoySkladDBGood, KonturMarketDBGood


def db_fill_comp_table(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
    """Функция заполняет таблицу Compilance в БД, на основе данных googlesheets_copm_table.
    :param googlesheets_copm_table: Список, элементам которого - список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает список наименований для которых не удалось сделать запись в БД.
    """

    if not googlesheets_copm_table:
        return False

    for good in googlesheets_copm_table:
        not_proceeded_good: List[MoySkladDBGood] = []
        ms_good: List[MoySkladDBGood] = []
        egais_good: KonturMarketDBGood = None

        # Если в таблице соответствия из googlesheets, не установлено соответствие - второй элемент будет пустой,
        # то пропускаем строку.
        if len(good) > 1:
            # В googlesheets не указывается разливное пиво
            egais_good = KonturMarketDBGood.objects.get(egais_code=good[1])

            # В таблице из googlesheets будут встречаться записи 2ух видов. В нулевом элементе good[0] может быть:
            # 1. 4Пивовара - Вброс, Бакунин - How Much Is Too Much [Raspberry],
            # 1.1 Степь и Ветер - Smoothie Mead: Raspberry, Black Currant, Mint
            # 2. Barbe Ruby, Barista Chocolate Quad

            # Проверяем на наличие в строке ' - '
            # Вариант 2:
            if good[0].find(' - ') == -1:
                ms_good = MoySkladDBGood.objects.\
                    filter(name=good[0]).\
                    filter(is_draft=False)
            # Вариант 1:
            else:
                brewery = good[0].split(' - ')[0]
                name = good[0].split(' - ')[1].title()
                ms_good = MoySkladDBGood.objects.\
                    filter(brewery=brewery).\
                    filter(name=name).\
                    filter(is_draft=False)

            # Если в выборке из таблицы товаров для МойСклад нашлось товаров больше одного
            if len(ms_good) > 1:
                # Делаем еще один запрос к таблице товаров и пытаемся сопоставить по объему
                ms_good = MoySkladDBGood.objects.\
                    filter(brewery=brewery).\
                    filter(name=name).\
                    filter(is_draft=False).\
                    filter(capacity=egais_good.capacity)
                # Если опять нашлось более одного товара, исключаем запись из обработки
                if len(ms_good) == 1:
                    # Если совпадение нашлось
                    ms_good[0].egais_code.add(egais_good)
                else:
                    not_proceeded_good.append(good)
            else:
                try:
                    ms_good[0].egais_code.add(egais_good)
                except Exception:
                    a = 1
        else:
            not_proceeded_good.append(good)

    return not_proceeded_good
