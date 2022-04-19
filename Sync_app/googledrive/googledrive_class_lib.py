"""Модуль для работы с Google Sheets"""
import os
from dataclasses import dataclass
from typing import Any, List

import googleapiclient.discovery
import httplib2
from oauth2client.service_account import ServiceAccountCredentials

import Sync_app.googledrive.googlesheets_vars as gs_vars


@dataclass
class GoogleSheets:
    """Класс для чтения данных из Google Sheets"""

    # Cервисный объект для работы с Google API.
    service: Any = None
    # Переменная устанавливается в True, в случае успешного логина в сервисе.
    connection_ok: bool = False

    def get_access(self) -> bool:
        """"Метод получения доступа сервисного объекта Google API
        :return: Возвращает True если получилось подключиться к Google API, False в противном случае"""

        # Авторизуемся и получаем service — экземпляр доступа к API
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            # все приватные данные храним в папке /Sync_app/privatedata
            os.path.join(os.path.dirname(os.path.dirname(__file__)),  # путь до /privatedata
                         'privatedata',
                         gs_vars.CREDENTIALS_FILE),
            [gs_vars.SPREEDSHEETS_URL, gs_vars.GDRIVE_URL])
        http_auth = credentials.authorize(httplib2.Http())
        self.service = googleapiclient.discovery.build('sheets', 'v4', http=http_auth)
        self.connection_ok = True

        return True

    def get_data(self, spreadsheets_id: str, list_name: str, list_range: str) -> List[List[str]]:
        """Метод получения данных из таблицы GoogleSheets
        :param spreadsheets_id: id таблицы в Google Sheets
        :param list_name: текстовое имя листа
        :param list_range: запрашиваемый диапазон A1:H100
        :return: Возвращает список списков [[], []..]. Каждый элемент списка - список из 2 элементов. 1 - коммерческое
                название, 2 - наименование ЕГАИС. Пустой список в случае не удачи
        """
        if not spreadsheets_id or not list_name or not list_range:
            return []

        values = self.service.spreadsheets().values().get(spreadsheetId=spreadsheets_id,
                                                          range=f'{list_name}!{list_range}',
                                                          majorDimension='ROWS').execute()
        if not values['values']:
            return []

        # googlesheets отдает диапазон, отсекая в запрашиваемом диапазоне пустые ячейки снизу, но пустые строки
        # могут оказаться в середине текста
        # отсортируем, чтобы пустые строки оказались вверху, а потом удалим их
        values = sorted(values['values'])
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
        self.service.spreadsheets().values().clear(spreadsheetId=spreadsheets_id,
                                                   range=f'{list_name}!{list_range}',
                                                   body={}).execute()
        # Записываем данные
        self.service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheets_id,
                                                     body={
                                                         "valueInputOption": "USER_ENTERED",
                                                         "data":
                                                             [
                                                                 {
                                                                     "range": f'{list_name}!{list_range}',
                                                                     "majorDimension": "ROWS",
                                                                     "values": data
                                                                 }
                                                             ]
                                                     }).execute()
        return True
