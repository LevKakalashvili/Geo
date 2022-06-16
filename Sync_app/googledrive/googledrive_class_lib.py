"""Модуль для работы с Google Sheets."""
import os
from dataclasses import dataclass
from typing import Any, List, NamedTuple

import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials

import Sync_app.googledrive.googlesheets_constants as gs_const
import Sync_app.models.konturmarket_models as km_model
import Sync_app.models.moysklad_models as ms_model
from Sync_app.common.functions import string_title


class CompilanceRow(NamedTuple):
    """Вспомогательный класс для хранения записи из таблицы соответствия, описанной в googlesheets."""

    commercial_name: str
    egais_code: str

    @property
    def brewery(self) -> str:
        """Название пивоварни."""
        return self.commercial_name.split(" - ")[0] if len(self.commercial_name.split(" - ")) > 1 else ""

    @property
    def name(self) -> str:
        """Название продукта."""
        separator = " - "
        count = self.commercial_name.count(separator)
        name: str
        if count == 0:
            name = self.commercial_name
        else:
            name = "".join(self.commercial_name.split(separator)[1:])

        return string_title(list_=name)


@dataclass
class GoogleSheets:
    """Класс для чтения данных из Google Sheets."""

    # Cервисный объект для работы с Google API.
    service: Any = None
    # Переменная устанавливается в True, в случае успешного логина в сервисе.
    connection_ok: bool = False

    @staticmethod
    def db_set_matches(googlesheets_copm_table: list[list[str]]) -> list[list[str]]:
        """Функция устанавливает соответствия между товарами в таблице БД moyskladdbgood и таблицей БД konturmarketdbgood.

        Связи устанавливаются на основе таблицы "Соответствия" в googlesheets, передаваемой
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
                km_db_good = km_model.KonturMarketDBGood.objects.get(egais_code=gs_good[1])

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

    def get_access(self) -> bool:
        """Метод получения доступа сервисного объекта Google API.

        :return: Возвращает True если получилось подключиться к Google API, False в противном случае. # pylint: disable=line-too-long
        """
        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            # все приватные данные храним в папке /Sync_app/privatedata
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),  # путь до /privatedata
                "privatedata",
                gs_const.CREDENTIALS_FILE,
            ),
            [gs_const.SPREEDSHEETS_URL, gs_const.GDRIVE_URL],
        )
        http_auth = credentials.authorize(httplib2.Http())
        self.service = googleapiclient.discovery.build("sheets", "v4", http=http_auth)
        self.connection_ok = True

        return True

    def get_data(self, spreadsheets_id: str, list_name: str, list_range: str) -> List[List[str]]:
        """Метод получения данных из таблицы GoogleSheets.

        :param spreadsheets_id: id таблицы в Google Sheets
        :param list_name: текстовое имя листа
        :param list_range: запрашиваемый диапазон A1:H100
        :return: Возвращает список списков [[], []..]. Каждый элемент списка - список из 2 элементов.
            1 - коммерческое # pylint: disable=line-too-long название,
            2 - наименование ЕГАИС. Пустой список в случае не удачи.
        """
        if not spreadsheets_id or not list_name or not list_range:
            return []

        values = (
            self.service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheets_id,
                range=f"{list_name}!{list_range}",
                majorDimension="ROWS",
            )
            .execute()
        )
        if not values["values"]:
            return []

        # googlesheets отдает диапазон, отсекая в запрашиваемом диапазоне пустые ячейки снизу,
        # но пустые строки # pylint: disable=line-too-long
        # могут оказаться в середине текста
        # отсортируем, чтобы пустые строки оказались вверху, а потом удалим их
        values = sorted(values["values"])
        i = 0
        while not values[i]:
            i += 1
        return values[i:]

    def send_data(self, data: List[Any], spreadsheets_id: str, list_name: str, list_range: str) -> bool:
        """Метод записи данных в таблицу GoogleSheets.

        :param data: Данные для записи.
        :param spreadsheets_id: id таблицы в Google Sheets
        :param list_name: Текстовое имя листа.
        :param list_range: Запрашиваемый диапазон A1:H100.
        :return: Возвращает True в случае удачной записи, False в случае ошибки.
        """
        # В начале очищаем диапазон.
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/clear?hl=ru
        self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheets_id,
            range=f"{list_name}!{list_range}",
            body={},
        ).execute()
        # Записываем данные
        self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheets_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {
                        "range": f"{list_name}!{list_range}",
                        "majorDimension": "ROWS",
                        "values": data,
                    },
                ],
            },
        ).execute()
        return True

    def sync_compl_table(self) -> bool:
        """Метод заполняет таблицу соответствия."""
        if not self.get_access():
            return False

        compl_table: List[List[str]] = self.get_data(
            spreadsheets_id=gs_const.SPREEDSHEET_ID_EGAIS,
            list_name=gs_const.LIST_NAME_EGAIS,
            list_range=f"{gs_const.FIRST_CELL_EGAIS}:{gs_const.LAST_COLUMN_EGAIS}",
        )
        # Оставляем только коммерческое название и код алкогольной продукции
        compl_table = [i[: len(i) : 2] for i in compl_table]  # noqa
        self.db_set_matches(googlesheets_copm_table=compl_table)

        return True
