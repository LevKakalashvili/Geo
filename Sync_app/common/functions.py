"""Модуль для вспомогательных функций."""
from typing import Any, List
from Sync_app.models import MoySkladDBGood, KonturMarketDBGood
from Sync_app.googledrive.googledrive_class_lib import CopmilanceRow


def db_fill_comp_table(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
    """Функция заполняет таблицу Compilance в БД, на основе данных googlesheets_copm_table.
    :param googlesheets_copm_table: Список, элементам которого - список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает список наименований для которых не удалось сделать запись в БД.
    """

    if not googlesheets_copm_table:
        return False

    not_proceeded_good: List[MoySkladDBGood] = []
    ms_db_good: List[MoySkladDBGood] = []
    km_db_good: KonturMarketDBGood = None

    for gs_row in googlesheets_copm_table:
        if gs_row[0] == 'Big Village - Futurology':
            a = 1
        km_db_good = None
        ms_db_good = None
        gs_good = None

        # Если в таблице соответствия из googlesheets, не установлено соответствие - второй элемент gs_good[1]
        # будет пустой, то пропускаем строку.
        if len(gs_row) > 1:
            gs_good = CopmilanceRow(commercial_name=gs_row[0],
                                    egais_code=gs_row[1])

            # В googlesheets указывается только фасованая продкция и не указывается разливное пиво
            km_db_good = KonturMarketDBGood.objects.get(egais_code=gs_good[1])

            # В таблице из googlesheets будут встречаться записи 2ух видов. В нулевом элементе good[0] может быть:
            # 1. 4Пивовара - Вброс, Бакунин - How Much Is Too Much [Raspberry],
            # 1.1 Степь и Ветер - Smoothie Mead: Raspberry, Black Currant, Mint
            # 2. Barbe Ruby
            # 2.1 Barista Chocolate Quad

            # Проверяем на наличие в строке ' - '
            # Вариант 2:
            if gs_good.brewery == '':
                ms_db_good = MoySkladDBGood.objects.\
                    filter(name=gs_good.name).\
                    filter(is_draft=False)
            # Вариант 1:
            else:
                ms_db_good = MoySkladDBGood.objects.\
                    filter(brewery=gs_good.brewery).\
                    filter(name=gs_good.name).\
                    filter(is_draft=False)

            # Если не нашли товар в таблице МойСклад
            if len(ms_db_good) == 0:
                gs_row.append("Не найден в таблице товаров МС. Возможно розлив")
                not_proceeded_good.append(gs_row)
            # Если в выборке из таблицы товаров для МойСклад нашлось товаров больше одного
            elif len(ms_db_good) >= 2:
                # Фильтруем по объему
                ms_db_good =list(
                    filter(
                        lambda element: element.capacity == km_db_good.capacity,
                        ms_db_good
                    )
                )

                # Делаем еще один запрос к таблице товаров и пытаемся сопоставить по объему
                # ms_db_good = MoySkladDBGood.objects.\
                #     filter(brewery=gs_good.brewery).\
                #     filter(name=gs_good.name).\
                #     filter(is_draft=False).\
                #     filter(capacity=km_db_good.capacity)

                # Если опять нашлось более одного товара, исключаем запись из обработки
                if len(ms_db_good) == 1:
                    # Если совпадение нашлось
                    ms_db_good[0].egais_code.add(km_db_good)
                else:
                    # Исключаем запись из обработки
                    not_proceeded_good.append(gs_row)
            # Если товар найден
            else:
                try:
                    # Добавляем связь между товарами МойСклад и товароами из ЕГАИС
                    ms_db_good[0].egais_code.add(km_db_good)
                except Exception:
                    a = 1
        else:
            gs_row.append('Нет кода алкогольной продукции')
            not_proceeded_good.append(gs_row)

    return not_proceeded_good

def string_title(_str: str) -> str:
    """Функция отрабаытывает так же как string.title(), но учитывает, что после апострофа должен идти символ в нижнем регистре."""
    # Т.к. str.title() не корректно обрабатывает апостроф
    if _str.find('\'') != -1:
        _str = string.capwords(_str)
    else:
        _str = _str.title()
    return _str
