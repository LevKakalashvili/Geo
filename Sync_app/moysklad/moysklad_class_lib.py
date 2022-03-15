"""В модуле хранятся описание классов."""
import datetime
import logging
import os
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import Sync_app.privatedata.moysklad_privatedata as ms_pvdata
import requests
from pydantic import BaseModel, Field

# from googledrive.googledrive_class_lib import googlesheets
# import googledrive.googlesheets_vars as gs_vars
# import logger_config
import Sync_app.moysklad.moysklad_urls as ms_urls
# from utils.file_utils import save_to_excel

# logging.config.dictConfig(logger_config.LOGGING_CONF)
# Логгер для МойСклад
# logger = logging.getLogger('moysklad')


class GoodsType(Enum):
    """Перечисление для определения, какой тип товаров необходимо получить.

    alco - алкогольная продукция (исключая разливное пиво).
    non_alco - не алкогольная продукция
    snack - закуски
    """

    alco = 1
    non_alco = 2
    snack = 3

class Price(BaseModel):
    value: int

class Modification(BaseModel):
    """"Класс описывает поле модификации в сервисе. В JSON представлении - атрибут 'characteristics'."""
    name: str
    value: str

class MetaParentGood(BaseModel):
    """Класс описывает метаданные родительского объекта, для случая когда используеться модификация товара."""
    # Ссылка на родительский товар
    uuidhref: str = Field(alias='uuidHref')

class ParentGood(BaseModel):
    """Класс описывает структуру родительского товара. Это применимо для модификаций товора."""
    # Метаданные родительского товара
    meta: MetaParentGood

class Good(BaseModel):
    """Класс описывает структуру товара в сервисе МОйСклад."""
    # Уникальный идентификатор товара
    id: str
    # Наименование товара
    name: str
    # Количество товара, может отсутсвовать, если товар - комплект
    quantity: Optional[int]
    # Имя папки товара. Для модификаций этого аттрибута нет, но появляется аттрибут 'characteristics'
    path_name: Optional[str] = Field(alias='pathName')
    # Первый элемент списка - розничная цена * 100
    price: List[Price] = Field(alias='salePrices')
    # Поле модификации в карточке товара
    modifications: Optional[List[Modification]] = Field(alias='characteristics')
    # Ссылка на родильский товар. Применимо только для модификаций товаров
    parent_good_href: Optional[ParentGood] = Field(alias='product')

    @property
    def parent_id(self):
        if self.parent_good_href:
            # Ссылка на товар хранится в виде
            # https://online.moysklad.ru/app/#good/edit?id=09f5f652-269e-11ec-0a80-02c5000e4cc9
            return self.parent_good_href.meta.uuidhref.split('?id=')[1]
        return ''
    # def __post_init__(self) -> None:
    #     if self.convert_name:
    #         self.commercial_name = self._convert_name(self.commercial_name)

    # @staticmethod
    # def _convert_name(name: str) -> str:
    #     """Метод преобразует строку наименования вида.
    #     4Пивовара - Black Jesus White Pepper (Porter - American. OG 17, ABV 6.7%, IBU 69)
    #     к строке вида
    #     4Пивовара - Black Jesus White Pepper.
    #
    #     :param name: Наименование товара.
    #     :type name: str
    #     :rtype: str
    #     """
    #     return name.split(' (')[0].replace('  ', ' ').strip()

    # @property
    # def to_tuple(self) -> Tuple[str, str, int, Decimal]:
    #     return self.commercial_name, self.egais_name, self.quantity, self.price


@dataclass()
class MoySklad:
    """Класс описывает работу с сервисом МойСклад по JSON
    API 1.2 https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api."""

    # токен для работы с сервисом
    # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
    _token: str = ''

    def set_token(self, request_new: bool = True) -> bool:
        """Получение токена для доступа и работы с МС по JSON API 1.2. При успешном ответе возвращаем True,
        в случае ошибок False.
        https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq.

        :param request_new: True, каждый раз будет запрашиваться новый токен,
            если False будет браться из moysklad_privatedata.py
        """
        # logger.debug(f'Получаем токен для работы с сервисом МойСклад. request_new = {request_new}')
        # если необходимо запросить новый токен у сервиса
        if request_new:
            # logger.debug('Пытаемся получить токен у MoySklad')
            # Получаем url запроса
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.token)
            # Получаем заголовок запроса
            header: Dict[str, Any] = ms_urls.get_headers(self._token)

            # отправляем запрос в МС для получения токена
            response = requests.post(url.url, headers=header)
            # если получили ответ
            if response.ok:
                self._token = response.json()['access_token']  # сохраняем токен
            else:
                return False
        else:
            self._token = ms_pvdata.TOKEN
        return True

    def get_assortment(self) -> Good:
        """Функция получения ассортимента товаров"""
        if not self._token:
            return []
        # Т.к. сервис отдает список товаров страницами по 1000, то при запросе необходимо указывать смещение.
        counter: int = 0  # счетчик количества запросов

        # Получаем заголовки для запроса в сервис
        header: Dict[str, Any] = ms_urls.get_headers(self._token)

        need_request: bool = True
        goods: List[Good] = []
        while need_request:
            # Получаем url для отправки запроса в сервис
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.assortment, offset=counter * 1000)

            response = requests.get(url.url, url.request_filter, headers=header)
            if not response.ok:
                return []

            rows: List[Any] = response.json().get('rows')
            # Проверяем получили ли в ответе не пустой список товаров из ассортимента
            if len(rows) == 1000:
                counter += 1  # увеличиваем счетчик смещений
            # Если список товаров меньше 1000, то сбрасываем флаг о необходимости дополнительных запросов
            elif len(rows) < 1000:
                need_request = False
            # Добавляем новые товары к существующим, расширяем список
            goods.extend(rows)

            converted_goods: List[Good] = []

        for good in goods:
            converted_goods.append(Good(**good))
        return converted_goods

