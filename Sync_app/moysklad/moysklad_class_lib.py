"""В модуле хранятся описание классов."""
import datetime
import logging
import os
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, NamedTuple

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

class GoodTuple(NamedTuple):
    """Класс используется только для разложения полного ноименоавния товара на состоавные части.
    Например: Наименование 'Lux In Tenebris - Der Grusel (Sour - Gose - Fruited. OG 11.5%, ABV 4,2%)' вернется котрежем
    (
        brewery = 'Lux In Tenebris',
        name = 'Der Grusel',
        style = 'Sour - Gose - Fruited',
        og = '11.5',
        abv = '4,2',
        ibu = '0'
    )
    """
    brewery: str = ''
    name: str = ''
    style: str = ''
    og: float = 0.0
    abv: float = 0.0
    ibu: int = 0
    is_alco: bool = False
    is_draft: bool = False
    is_cider: bool = False
    is_beer: bool = False

class GoodsType(Enum):
    """Перечисление для определения, какой тип товаров необходимо получить.

    alco - алкогольная продукция (исключая разливное пиво).
    non_alco - не алкогольная продукция
    snack - закуски
    """

    alco = 1
    non_alco = 2
    snack = 3

class Attributes(BaseModel):
    """Класс описывает поле аттрибутов. В аттрибутах храняться: признак розлива и признак алкогольной продукции."""
    name: str
    value: Union[bool, str]

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
    # Наименование товара. Например Lux In Tenebris - Der Grusel (Sour - Gose - Fruited. OG 11.5%, ABV 4,2%)
    name: str
    # Количество товара, может отсутсвовать, если товар - комплект
    quantity: Optional[int]
    # Имя папки товара. У модификаций этого аттрибута нет, но появляется аттрибут 'characteristics'
    path_name: Optional[str] = Field(alias='pathName')
    # Первый элемент списка - розничная цена * 100
    price: List[Price] = Field(alias='salePrices')
    # Поле модификации в карточке товара
    modifications: Optional[List[Modification]] = Field(alias='characteristics')
    # Ссылка на родильский товар. Применимо только для модификаций товаров
    parent_good_href: Optional[ParentGood] = Field(alias='product')
    # Дополнительные, пользовательсике аттрибуты для товаоа.
    # В текущей версии:
    # Розлив - да, нет
    # Алкогольная продукция - True, False
    attributes: Optional[List[Attributes]] = Field(alias='attributes')

    @property
    def parent_id(self):
        """Свойство возвращает uuid родительской товар."""
        if self.parent_good_href:
            # Ссылка на товар хранится в виде
            # https://online.moysklad.ru/app/#good/edit?id=09f5f652-269e-11ec-0a80-02c5000e4cc9
            return self.parent_good_href.meta.uuidhref.split('?id=')[1]
        return ''

    @property
    def parse_name(self):
        """Метод возвращает объект типа GoodTuple."""
        full_name: str = self.name
        brewery: str = ''
        name: str = ''
        style: str = ''
        is_draft: bool = False
        is_alco: bool = False
        is_cider: bool = False
        og: float = 0.0
        abv: float = 0.0
        ibu: int = 0

        # Если товар - модификация
        # Alaska - Стаутский советник (Stout - Imperial / Double Milk. OG 16,5%, ABV 10,5%) (Банка 0,33)
        if self.name.find('Василеостровская - Сидр (Cider. ABV 4,7%) (Бутылка 0,33)') != -1:
            a = 1

        try:
            if self.modifications:
                full_name = full_name.replace(f' ({self.modifications[0].value})', '')
                # Устанавливаем флаг в True, т.к. при проверке на алко (ниже по коду) модификации тоже нужно обработать и выставить флаги пиво, сидр, безалко
                is_modification = True
            # Самы рабочий варинат, но не красивый в использовании.
            # Т.к. не все модификации товара заведены, как модификации просто удаляем из названия мусор.
            # 'Barista Chocolate Quad (Belgian Quadrupel. ABV 11%) (0,75)'
            full_name = full_name.replace(' (0,75)', '').replace(' (0,33)', '')
        except Exception:
            a = 1

        try:
            # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
            # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. это происходит т.к. аттрибут
            # "Алкогольная продукция", является обязательным для всех товаров
            #
            # Признак алкогольной продукции
            # дополнительное поле "Алкогольная продукция" в массиве ['attributes'] - элемент с индексом 1
            # True - чек-бокс установлен, False - не установлен
            # проверяем, что аттрибут "Алкогольная продукция" == True
            # if hasattr(self, 'attributes'):
            if (self.attributes is not None) or is_modification:
                # Если модификация, то принимаем, что продукт алкогольный
                if is_modification:
                    is_alco = True
                else:
                    # Если есть аттрибут алкогольной продукции
                    if len(self.attributes) == 1:
                        is_alco = self.attributes[0].value
                    # Если у товара определен аттрибут розлива
                    elif len(self.attributes) == 2:
                        is_draft = True if self.attributes[0].value.lower() == 'да' else False
                        is_alco = self.attributes[1].value
            # Если пиво розливное, нужно убрать (0,5) из наименования
            if is_draft:
                brewery_and_name = full_name.replace(' (0,5)', '')
        except Exception:
            a = 1

        try:
            # Получаем название пивоварни
            # Варианты наименований:
            # вариант 1. 4Пивовара - Black Jesus White Pepper (Porter - American. OG 17, ABV 6.7%, IBU 69)
            # вариант 2. 4Пивовара - Ether [Melon] (Sour - Farmhouse IPA OG 17, ABV 6.5%, IBU 40)
            # вариант 3. Кер Сари Пшеничное (Wheat Beer - Other. ABV 4,5%)
            # вариант 4. Butch & Dutch - IPA 100 IBU (0,5) (IPA - International. ABV 7%, IBU 100)
            # вариант 5. Trappistes Rochefort 6 (Belgian Dubbel. ABV 7,5%, IBU 22)
            # вариант 6. Fournier - Frères Producteurs - Eleveurs - Cidre Rosé (Cider - Rosé. ABV 3%)
            # Убираем все что в (...)
            brewery_and_name = full_name.split(' (')[0]
            # Если вариант 3 или 5
            if len(brewery_and_name.split(' - ')) == 1:
                # Если модификация, то папка будет пустой а parent_id будет содержать uuid родительского товара
                if not self.parent_id:
                    brewery = self.path_name.split('/')[-1]
                name = brewery_and_name
            # Если вариант 1 и 4
            elif len(brewery_and_name.split(' - ')) == 2:
                brewery = brewery_and_name.split(' - ')[0]
                name = brewery_and_name.split(' - ')[1]
            # Вариант 6
            else:
                brewery = ' - '.join(brewery_and_name.split(' - ')[:-1])
                name = brewery_and_name.split(' - ')[-1]
            brewery = brewery.title()
            name = name.title()
        except Exception:
            a = 1

        if is_alco:
            # Убираем пивоварню из полного имени
            try:
                additional_info = full_name.split(' (')[-1].replace(')', '')
                # Получаем стиль пива/сидра
                style = additional_info.split('.')[0]
                # Если в стиле указа ни сидр, то это сидр
                if style.lower().find('cider') != -1:
                    is_beer = False
                    is_cider = True
                else:
                    is_beer = True
                    is_cider = False
            except Exception:
                a = 1
            try:
                additional_info = additional_info.split('. ')[1].split(', ')
            except Exception:
                a = 1
            try:
                for info in additional_info:
                    if info.lower().find('og') != -1:
                        og = float(info.lower().replace('og ', '').replace(',','.').replace('%', ''))
                    elif info.lower().find('abv') != -1:
                        abv = float(info.lower().replace('abv ', '').replace(',','.').replace('%', ''))
                    elif info.lower().find('ibu') != -1:
                        ibu = int(info.lower().replace('ibu ', ''))
            except Exception:
                a = 1

        return GoodTuple(
            brewery=brewery,
            name=name,
            style=style,
            og=og,
            abv=abv,
            ibu=ibu,
            is_draft=is_draft,
            is_alco=is_alco,
            is_cider=is_cider,
            is_beer=is_cider
        )



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
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.TOKEN)
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
        """Функция получения ассортимента товаров."""
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
            url: ms_urls.Url = ms_urls.get_url(ms_urls.UrlType.ASSORTMENT, offset=counter * 1000)

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

