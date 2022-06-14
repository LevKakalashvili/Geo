"""Модуль вспомогательных функций для работы с БД."""

from Sync_app.googledrive.googledrive_class_lib import CompilanceRow
import Sync_app.models.moysklad_models as ms_model
import Sync_app.models.konturmarket_models as km_model


def db_set_matches(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
    """Функция устанавливает соответствия между товарами в таблице БД moyskladdbgood и таблицей
    БД konturmarketdbgood. Связи устанавливаются на основе таблицы "Соответствия" в googlesheets, передаваемой
    параметром googlesheets_copm_table.
    :param googlesheets_copm_table: Список вида:
    ['Коммерческое название', 'Код алкогольной продукции'].
    :return: Возвращает список наименований для которых не удалось сделать запись в БД.
    """

    if not googlesheets_copm_table:
        return []

    not_proceeded_good = []
    # TODO: разобраться с QuerySet
    # ms_db_good: QuerySet
    km_db_good: km_model.KonturMarketDBGood

    for gs_row in googlesheets_copm_table:
        # Если в таблице соответствия из googlesheets, не установлено соответствие - второй элемент gs_good[1]
        # будет пустой, то пропускаем строку.
        if len(gs_row) > 1:
            gs_good = CompilanceRow(commercial_name=gs_row[0], egais_code=gs_row[1])

            # В googlesheets указывается только фасованная продукция и не указывается разливное пиво
            km_db_good = km_model.onturMarketDBGood.objects.get(egais_code=gs_good[1])

            # В таблице из googlesheets будут встречаться записи 2ух видов. В нулевом элементе good[0] может быть:
            # 1. 4Пивовара - Вброс, Бакунин - How Much Is Too Much [Raspberry],
            # 1.1 Степь и Ветер - Smoothie Mead: Raspberry, Black Currant, Mint
            # 2. Barbe Ruby
            # 2.1 Barista Chocolate Quad

            # Вариант 2:
            ms_db_good = ms_model.MoySkladDBGood.objects.filter(name=gs_good.name).filter(is_draft=False)
            if gs_good.brewery:
                # Вариант 1:
                ms_db_good = ms_db_good.filter(brewery=gs_good.brewery)

            # Если не нашли товар в таблице МойСклад
            if len(ms_db_good) == 0:
                not_proceeded_good.append(gs_row)

            # Если в выборке из таблицы товаров для МойСклад нашлось товаров больше одного
            elif len(ms_db_good) >= 2:
                # Фильтруем по объему
                ms_db_good = [good for good in ms_db_good if good.capacity == km_db_good.capacity]

                # Если опять нашлось более одного товара, исключаем запись из обработки
                if len(ms_db_good):
                    # Если нашлись совпадения
                    for element in ms_db_good:
                        element.egais_code.add(km_db_good)
                else:
                    # Исключаем запись из обработки
                    not_proceeded_good.append(gs_row)
            # Если товар найден
            else:
                # Добавляем связь между товарами МойСклад и товарами из ЕГАИС
                ms_db_good.first().egais_code.add(km_db_good)
        else:
            not_proceeded_good.append(gs_row)

    return not_proceeded_good
