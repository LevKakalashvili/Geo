"""В модуле хранятся описание классов."""
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union, NamedTuple

import Sync_app.privatedata.moysklad_privatedata as ms_pvdata
import requests
from pydantic import BaseModel, Field

# from googledrive.googledrive_class_lib import googlesheets
# import googledrive.googlesheets_vars as gs_vars
# import logger_config
import Sync_app.moysklad.moysklad_urls as ms_urls
from Sync_app.common.functions import string_title

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
    capacity: float = 0.0


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
    """Класс описывает поле аттрибутов. В аттрибутах хранятся: признак розлива и признак алкогольной продукции."""
    name: str
    value: Union[bool, str]


class Price(BaseModel):
    value: int


class Modification(BaseModel):
    """Класс описывает поле модификации в сервисе. В JSON представлении - атрибут 'characteristics'."""
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
    # Количество товара, может отсутствовать, если товар - комплект
    quantity: Optional[int]
    # Имя папки товара. У модификаций этого аттрибута нет, но появляется аттрибут 'characteristics'
    path_name: Optional[str] = Field(alias='pathName')
    # Первый элемент списка - розничная цена * 100
    price: List[Price] = Field(alias='salePrices')
    # Поле модификации в карточке товара
    modifications: Optional[List[Modification]] = Field(alias='characteristics')
    # Ссылка на родительский товар. Применимо только для модификаций товаров
    parent_good_href: Optional[ParentGood] = Field(alias='product')
    # Дополнительные, пользовательские аттрибуты для товара.
    # В текущей версии:
    # Розлив - да, нет
    # Алкогольная продукция - True, False
    attributes: Optional[List[Attributes]] = Field(alias='attributes')
    # Объем продукции
    volume: Optional[float]

    @property
    def parent_id(self):
        """Свойство возвращает uuid родительский товар."""
        if self.parent_good_href:
            # Ссылка на товар хранится в виде
            # https://online.moysklad.ru/app/#good/edit?id=09f5f652-269e-11ec-0a80-02c5000e4cc9
            return self.parent_good_href.meta.uuidhref.split('?id=')[1]
        return ''

    def parse_object(self) -> GoodTuple:
        """Метод возвращает объект типа GoodTuple."""

        if not self:
            return None

        good = self._parse_object()

        return good

    def _parse_object(self) -> GoodTuple:
        if self.name:
            # if self.name == 'Медведевское Бархатное (0,5) (Lager - Dark. ABV 4.1%)':
            #     a = 1
            full_name = _remove_modification_from_name(name=self.name, modification=self.modifications)
            full_name = _remove_trash_from_string(full_name)

            additional_info = _get_additional_info(f_name=full_name)
            bev_type = _get_good_type(additional_info)

            style = _get_style(additional_info)
            is_cider = bev_type.cider
            is_beer = bev_type.beer
            abv = _get_characteristics(_type=Characteristics.ABV, add_info=additional_info)
            is_alco = True if abv > 1 else False
            og = _get_characteristics(_type=Characteristics.OG, add_info=additional_info)
            ibu = _get_characteristics(_type=Characteristics.IBU, add_info=additional_info)
            brewery = _get_brewery(f_name=full_name, add_info=additional_info, parent_path=self.path_name)
            name = _get_name(f_name=full_name, add_info=additional_info, brewery=brewery)

            is_draft = _is_draft(attr=self.attributes)
            capacity = _get_capacity(cap=dict(self).get('volume'), modification=self.modifications)

            return GoodTuple(
                brewery=brewery,
                name=name,
                style=style,
                og=og,
                abv=abv,
                ibu=ibu,
                is_alco=is_alco,
                is_cider=is_cider,
                is_beer=is_beer,
                is_draft=is_draft,
                capacity=capacity
            )
        return None


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


_TRASH: tuple = (
    ' (0,75)',
    ' (0,33)',
    ' Бутылка 0,75',
    ' ж\б',
    ' (ж/б)',
    ' (0,5)',
)

_MODIFICATION_SET: dict = {
    'Банка 0,33': 0.33,
    'Банка 0,45': 0.45,
    'Бутылка 0,33': 0.33,
    'Бутылка 0,375': 0.375,
    'Бутылка 0,5': 0.5,
    'Бутылка 0,75': 0.75,
    'ж.б 0,33': 0.33,
    'ж/б 0,5': 0.5
}


def _is_draft(attr: Dict = None) -> bool:
    # Если в сервисе у товара определен аттрибут "Розлив", то индекс аттрибута "Алкогольная продукция",
    # в массиве аттрибутов будет 1, если не определен, то индекс будет 0. это происходит т.к. аттрибут
    # "Алкогольная продукция", является обязательным для всех товаров
    #
    # Признак алкогольной продукции
    # дополнительное поле "Алкогольная продукция" в массиве ['attributes'] - элемент с индексом 1
    # True - чек-бокс установлен, False - не установлен
    # проверяем, что аттрибут "Алкогольная продукция" == True
    # Если есть аттрибут алкогольной продукции
    is_draft: bool = False

    # if len(self.attributes) == 1:
    #     is_alco = self.attributes[0].value
    # Если у товара определен аттрибут розлива
    if attr is not None:
        if len(attr) == 2:
            is_draft = True if attr[0].value.lower() == 'да' else False
    return is_draft


def _remove_trash_from_string(in_str: str) -> str:
    """Метод вырезает из входной строки мусор, определённый в кортеже _TRASH()."""
    for trash_element in _TRASH:
        in_str = in_str.replace(trash_element, '')
    return in_str


def _remove_modification_from_name(name: str = '',
                                   modification=None
                                   ) -> str:
    """Метод удаляет из входной строки название модификации "Тара", определенных в _MODIFICATION_SET()."""

    if modification:
        for mod in modification:
            if mod.name == 'Тара':
                return name.replace(f' ({mod.value})', '')
    return name


def _get_capacity(cap: float = None, modification: Dict = None) -> float:
    """Метод возвращает объем продукции."""
    # Модификации в сервисе не имеют аттрибут объем, но название модификации будет иметь вид
    # Alaska - Нигилист (Lager - IPL (India Pale Lager). OG 16%, ABV 6,8%, IBU 60) (Название модификации)
    # Все модификации сделаны для разделения по объемам
    # if modification is None:
    #     a = 1
    capacity: float = 0.0
    if cap is not None:
        return cap

    if modification[0].name == 'Тара':
        for _capacity in _MODIFICATION_SET:
            if _capacity == modification[0].value:
                capacity = float(_MODIFICATION_SET[_capacity])
    return capacity


class Characteristics(Enum):
    ABV = 'abv'
    OG = 'og'
    IBU = 'ibu'


class BeverageType(NamedTuple):
    beer: bool
    cider: bool
    kombucha: bool
    other: bool


def _get_additional_info(f_name: str = '') -> str:
    """Метод возвращает строку информации, содержащей стиль, плотность, содержание алкоголя.
    Например:
    'Coven - GLAM (Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15)' вернется 'Lager - IPL (India Pale Lager). ABV 5.5%,IBU 15',
    'Molson Coors (UK) - Carling Original (Lager - Pale. ABV 3,7%)' вернется 'Lager - Pale. ABV 3,7%',
    'Barista Chocolate Quad (Belgian Quadrupel. ABV 11%)' вернется 'Belgian Quadrupel. ABV 11%',
    """
    add_info: str

    if f_name != '':
        regex = r'\(([^()]*(?:\([^()]*\)[^()]*)*)\)$'
        matches = re.findall(regex, f_name)
        if len(matches) != 0:
            add_info = matches[0]
            return add_info
    return ''


def _get_style(add_info: str = '') -> str:
    """Метод возвращает строку информации, содержащей стиль.
    Например:
    'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15' вернется 'Lager - IPL (India Pale Lager)',
    'Lager - Pale. ABV 3,7%' вернется 'Lager - Pale',
    'Belgian Quadrupel. ABV 11%' вернется 'Belgian Quadrupel',
    """
    if add_info != '':
        return add_info.split('. ')[0]
    return ''


def _get_characteristics(_type: Characteristics, add_info: str = '') -> float:
    """Метод возвращает число - количественный параметр, выбранный из параметра add_info в зависимости от переданного параметра _type.
    Например:
    _type = ABV
    add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
    вернется 5.5
    _type = IBU
    add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
    вернется 15
    _type = OG
    add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
    вернется 0
    """
    if add_info != '':
        if len(add_info.split('. ')) != 1:
            add_info = add_info.split('. ')[1].split(', ')
            for _info in add_info:
                if _info.lower().find(_type.value) != -1:
                    return float(_info.lower().replace(f'{_type.value} ', '').replace(',', '.').replace('%', ''))
    return 0


def _get_brewery(f_name: str = '', add_info: str = '', parent_path: str = '') -> str:
    """Метод возвращает название пивоварни, вырезанной из строки f_name.
    'Кер Сари Пшеничное (Wheat Beer - Other. ABV 4,5%)' вернет '',
    'Butch & Dutch - IPA 100 IBU (IPA - International. ABV 7%, IBU 100)' вернет 'Butch & Dutch',
    'Trappistes Rochefort 6 (Belgian Dubbel. ABV 7,5%, IBU 22)' вернет '',
    'Fournier - Frères Producteurs - Eleveurs - Cidre Rose (Cider - Rose. ABV 3%)' вернет parent_path,
    'Shepherd Neame - Classic Collection - India Pale Ale (IPA - English. OG 14,6%, ABV 6,1%)' вернет parent_path
    """
    brewery: str = ''
    if add_info != '' and f_name != '':
        f_name = f_name.replace(f' ({add_info})', '')
        if f_name.count(' - ') == 1:
            brewery = ''.join(f_name.split(' - ')[:-1])
        # elif f_name.count(' - ') > 2 and parent_path != '':
        elif parent_path is not None:
            brewery = parent_path.split('/')[-1]
    return brewery


def _get_name(f_name: str = '', add_info: str = '', brewery: str = '') -> str:
    """Метод возвращает название продукта, вырезанной из строки f_name.
    'Кер Сари Пшеничное (Wheat Beer - Other. ABV 4,5%)' вернет 'Кер Сари Пшеничное',
    'Butch & Dutch - IPA 100 IBU (IPA - International. ABV 7%, IBU 100)' вернет 'IPA 100 IBU',
    'Trappistes Rochefort 6 (Belgian Dubbel. ABV 7,5%, IBU 22)' вернет 'Trappistes Rochefort 6',
    'Fournier - Frères Producteurs - Eleveurs - Cidre Rose (Cider - Rose. ABV 3%)' вернет '',
    'Shepherd Neame - Classic Collection - India Pale Ale (IPA - English. OG 14,6%, ABV 6,1%)' вернет ''
    """
    name = ''
    if add_info != '' and f_name != '':
        name = f_name.replace(f' ({add_info})', '')
        if brewery:
            name = name.replace(f'{brewery} - ', '')
    return name


def _get_good_type(add_info: str = '') -> BeverageType:
    """Метод возвращает тип продукта пиво, сидр, комбуча, вырезанной из строки add_info."""
    if add_info != '':
        if add_info.lower().find('cider') != -1:
            bev_type = BeverageType(beer=False, cider=True, kombucha=False, other=False)
        elif add_info.lower().find('kombucha') != -1:
            bev_type = BeverageType(beer=False, cider=False, kombucha=True, other=False)
        else:
            bev_type = BeverageType(beer=True, cider=False, kombucha=False, other=False)
    else:
        bev_type = BeverageType(beer=False, cider=False, kombucha=False, other=True)
    return bev_type
