"""В модуле хранятся описание классов."""
import datetime
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Optional, Union

import requests
from pydantic import BaseModel, Field

import Sync_app.models.moysklad_models as ms_model
import Sync_app.moysklad.moysklad_urls as ms_urls
from dotenv import load_dotenv
from Sync_app.moysklad.moysklad_constants import (
    _MODIFICATION_SET, _TRASH, Characteristics, GoodType,
)

load_dotenv()


class RetailDemandPosition(NamedTuple):
    """Класс используется только для позиций проданных товаров."""

    # Id товара проданного товара
    good_id: str
    # Количество проданного товара
    quantity: int
    # Дата продажи
    demand_date: str


class RetailReturnedPosition(RetailDemandPosition):
    """Класс используется только для позиций возвратных товаров."""

    pass


class GoodTuple(NamedTuple):
    """Класс используется только для разложения полного наименования товара на составные части.

    Например: Наименование 'Lux In Tenebris - Der Grusel (Sour - Gose - Fruited. OG 11.5%, ABV 4,2%)' вернется кортежем
    (
        brewery = 'Lux In Tenebris',
        name = 'Der Grusel',
        style = 'Sour - Gose - Fruited',
        og = '11.5',
        abv = '4,2',
        ibu = '0'
    )
    """

    brewery: str = ""
    name: str = ""
    style: str = ""
    og: float = 0.0
    abv: float = 0.0
    ibu: int = 0
    is_alco: bool = False
    is_draft: bool = False
    bev_type: str = "".join(GoodType.OTHER.value)
    capacity: float = 0.0


class Attributes(BaseModel):
    """Класс описывает поле аттрибутов. В аттрибутах хранятся: признак розлива и признак алкогольной продукции."""

    name: str
    value: Union[bool, str]


class Price(BaseModel):
    """Класс описывает розничную цену товара."""

    value: int


class Modification(BaseModel):
    """Класс описывает поле модификации в сервисе. В JSON представлении - атрибут 'characteristics'."""

    name: str
    value: str


class MetaParentGood(BaseModel):
    """Класс описывает метаданные родительского объекта, для случая когда используется модификация товара."""

    # Ссылка на родительский товар
    uuidhref: str = Field(alias="uuidHref")


class ParentGood(BaseModel):
    """Класс описывает структуру родительского товара. Это применимо для модификаций товара."""

    # Метаданные родительского товара
    meta: MetaParentGood


class Good(BaseModel):
    """Класс описывает структуру товара в сервисе МОйСклад."""

    # Уникальный идентификатор товара
    good_id: str = Field(alias="id")
    # Наименование товара. Например Lux In Tenebris - Der Grusel (Sour - Gose
    # - Fruited. OG 11.5%, ABV 4,2%)
    name: str
    # Количество товара, может отсутствовать, если товар - комплект
    quantity: Optional[int]
    # Имя папки товара. У модификаций этого аттрибута нет, но появляется
    # аттрибут 'characteristics'
    path_name: Optional[str] = Field(alias="pathName")
    # Первый элемент списка - розничная цена * 100
    price: List[Price] = Field(alias="salePrices")
    # Поле модификации в карточке товара
    modifications: Optional[List[Modification]] = Field(alias="characteristics")
    # Ссылка на родительский товар. Применимо только для модификаций товаров
    parent_good_href: Optional[ParentGood] = Field(alias="product")
    # Дополнительные, пользовательские аттрибуты для товара.
    # В текущей версии:
    # Розлив - да, нет
    # Алкогольная продукция - True, False
    attributes: Optional[List[Attributes]] = Field(alias="attributes")
    # Объем продукции
    volume: Optional[float]

    @property
    def parent_id(self) -> str:
        """Свойство возвращает uuid родительский товар."""
        if self.parent_good_href:
            # Ссылка на товар хранится в виде
            # https://online.moysklad.ru/app/#good/edit?id=09f5f652-269e-11ec-0a80-02c5000e4cc9
            return self.parent_good_href.meta.uuidhref.split("?id=")[1]
        return ""

    @staticmethod
    def _is_draft(attr: List[Attributes] = None) -> bool:
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

        # Если у товара определен аттрибут розлива
        if attr is not None:
            if len(attr) == 2:
                is_draft = True if str(attr[0].value).lower() == "да" else False
        return is_draft

    @staticmethod
    def _remove_trash_from_string(in_str: str) -> str:
        """Метод вырезает из входной строки мусор, определённый в кортеже _TRASH()."""
        for trash_element in _TRASH:
            in_str = in_str.replace(trash_element, "")
        return in_str

    @staticmethod
    def _remove_modification_from_name(name: str = "", modification: List[Modification] = None) -> str:
        """Метод удаляет из входной строки название модификации "Тара", определенных в _MODIFICATION_SET()."""
        if modification:
            for mod in modification:
                if mod.name == "Тара":
                    return name.replace(f" ({mod.value})", "")
        return name

    @staticmethod
    def _get_capacity(cap: float = None, modification: List[Modification] = None) -> float:
        """Метод возвращает объем продукции."""
        # Модификации в сервисе не имеют аттрибут объем, но название модификации будет иметь вид
        # Alaska - Нигилист (Lager - IPL (India Pale Lager). OG 16%, ABV 6,8%, IBU 60) (Название модификации)
        # Все модификации сделаны для разделения по объемам
        capacity: float = 0.0
        if cap is not None:
            return cap

        if modification is not None and modification[0].name == "Тара":
            for _capacity in _MODIFICATION_SET:
                if _capacity == modification[0].value:
                    capacity = float(_MODIFICATION_SET[_capacity])
        return capacity

    @staticmethod
    def _get_additional_info(f_name: str = "") -> str:
        """Метод возвращает строку информации, содержащей стиль, плотность, содержание алкоголя.

        Например:
        'Coven - GLAM (Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15)' вернется 'Lager - IPL (India Pale Lager).
        ABV 5.5%,IBU 15',
        'Molson Coors (UK) - Carling Original (Lager - Pale. ABV 3,7%)' вернется 'Lager - Pale. ABV 3,7%',
        'Barista Chocolate Quad (Belgian Quadrupel. ABV 11%)' вернется 'Belgian Quadrupel. ABV 11%',
        """
        add_info: str

        if f_name != "":
            regex = r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)$"
            matches = re.findall(regex, f_name)
            if len(matches) != 0:
                add_info = matches[0]
                return add_info
        return ""

    @staticmethod
    def _get_style(add_info: str = "") -> str:
        """Метод возвращает строку информации, содержащей стиль.

        Например:
        'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15' вернется 'Lager - IPL (India Pale Lager)',
        'Lager - Pale. ABV 3,7%' вернется 'Lager - Pale',
        'Belgian Quadrupel. ABV 11%' вернется 'Belgian Quadrupel',
        """
        if add_info != "":
            return add_info.split(". ")[0]
        return ""

    @staticmethod
    def _get_characteristics(type_: Characteristics, add_info: str = "") -> float:
        """Метод возвращает число - количественный параметр, выбранный из параметра add_info в зависимости от переданного параметра type_.

        Например:
        type_ = ABV
        add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
        вернется 5.5
        type_ = IBU
        add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
        вернется 15
        type_ = OG
        add_info = 'Lager - IPL (India Pale Lager). ABV 5.5%, IBU 15'
        вернется 0
        """
        if not add_info or (". " not in add_info):
            return 0

        for _info in add_info.split(". ")[1].split(", "):
            if _info.lower().find(type_.value) != -1:
                return float(_info.lower().replace(f"{type_.value} ", "").replace(",", ".").replace("%", ""))
        return 0

    @staticmethod
    def _get_brewery(f_name: str = "", add_info: str = "", parent_path: str = "") -> str:
        """Метод возвращает название пивоварни, вырезанной из строки f_name.

        'Кер Сари Пшеничное (Wheat Beer - Other. ABV 4,5%)' вернет '',
        'Butch & Dutch - IPA 100 IBU (IPA - International. ABV 7%, IBU 100)' вернет 'Butch & Dutch',
        'Trappistes Rochefort 6 (Belgian Dubbel. ABV 7,5%, IBU 22)' вернет '',
        'Fournier - Frères Producteurs - Eleveurs - Cidre Rose (Cider - Rose. ABV 3%)' вернет parent_path,
        'Shepherd Neame - Classic Collection - India Pale Ale (IPA - English. OG 14,6%, ABV 6,1%)' вернет parent_path
        """
        brewery: str = ""
        if add_info != "" and f_name != "":
            f_name = f_name.replace(f" ({add_info})", "")
            if f_name.count(" - ") == 1:
                brewery = "".join(f_name.split(" - ")[:-1])
            elif parent_path is not None:
                brewery = parent_path.split("/")[-1]
        return brewery

    @staticmethod
    def _get_name(f_name: str = "", add_info: str = "", brewery: str = "") -> str:
        """Метод возвращает название продукта, вырезанной из строки f_name.

        'Кер Сари Пшеничное (Wheat Beer - Other. ABV 4,5%)' вернет 'Кер Сари Пшеничное',
        'Butch & Dutch - IPA 100 IBU (IPA - International. ABV 7%, IBU 100)' вернет 'IPA 100 IBU',
        'Trappistes Rochefort 6 (Belgian Dubbel. ABV 7,5%, IBU 22)' вернет 'Trappistes Rochefort 6',
        'Fournier - Frères Producteurs - Eleveurs - Cidre Rose (Cider - Rose. ABV 3%)' вернет '',
        'Shepherd Neame - Classic Collection - India Pale Ale (IPA - English. OG 14,6%, ABV 6,1%)' вернет ''
        """
        name = ""
        if add_info != "" and f_name != "":
            name = f_name.replace(f" ({add_info})", "")
            if brewery:
                name = name.replace(f"{brewery} - ", "")
        return name

    @staticmethod
    def _get_good_type(add_info: str = "") -> str:
        """Метод возвращает тип продукта пиво, сидр, комбуча, вырезанной из строки add_info."""
        bev_type: GoodType = GoodType.OTHER
        if add_info != "":
            if "".join(GoodType.CIDER.value) in add_info.lower():
                bev_type = GoodType.CIDER
            elif "".join(GoodType.MEAD.value) in add_info.lower():
                bev_type = GoodType.MEAD
            elif "".join(GoodType.KOMBUCHA.value) in add_info.lower():
                bev_type = GoodType.KOMBUCHA
            elif "".join(GoodType.LEMONADE.value) in add_info.lower():
                bev_type = GoodType.LEMONADE
            else:
                bev_type = GoodType.BEER
        return "".join(bev_type.value)

    def parse_object(self) -> GoodTuple:
        """Метод возвращает объект типа GoodTuple."""
        if not self:
            return GoodTuple()

        good = self._parse_object()

        return good

    def _parse_object(self) -> GoodTuple:
        if self.name:
            full_name = self._remove_modification_from_name(name=self.name, modification=self.modifications)
            full_name = self._remove_trash_from_string(full_name)

            additional_info = self._get_additional_info(f_name=full_name)
            bev_type = self._get_good_type(additional_info)

            style = self._get_style(additional_info)
            abv = self._get_characteristics(type_=Characteristics.ABV, add_info=additional_info)
            is_alco = True if abv > 1 else False
            og = self._get_characteristics(type_=Characteristics.OG, add_info=additional_info)
            ibu = self._get_characteristics(type_=Characteristics.IBU, add_info=additional_info)
            brewery = self._get_brewery(
                f_name=full_name,
                add_info=additional_info,
                parent_path=self.path_name if self.path_name else "",
            )
            name = self._get_name(f_name=full_name, add_info=additional_info, brewery=brewery)

            is_draft = self._is_draft(attr=self.attributes)
            capacity = self._get_capacity(cap=dict(self).get("volume"), modification=self.modifications)

            return GoodTuple(
                brewery=brewery,
                name=name,
                style=style,
                og=og,
                abv=abv,
                ibu=int(ibu),
                is_alco=is_alco,
                bev_type=bev_type,
                is_draft=is_draft,
                capacity=capacity,
            )
        return GoodTuple()


class Position(BaseModel):
    """Класс описывает единицу товара, входящей в продажу."""

    # Уникальный идентификатор товара в продаже
    uuid: str = Field(alias="id")
    # Количество товаров в позиции
    quantity: float
    # Проданный товар
    good: Good = Field(alias="assortment")


class DemandPositions(BaseModel):
    """Класс описывает список товаров, входящей в продажу."""

    all_: List[Position] = Field(alias="rows")


class RetailDemand(BaseModel):
    """Класс описывает структуру одной продажи (чека)."""

    # Уникальный идентификатор продажи
    rd_id: str = Field(alias="id")
    # Номер, имя продажи
    name: str
    # Дата создания продажи
    created: datetime.datetime
    # Товары входящие в продажу, чек
    positions: Optional[DemandPositions]


# noinspection PyProtectedMember
@dataclass()
class MoySklad:
    """Класс описывает работу с сервисом МойСклад по JSON API 1.2 https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api."""

    # токен для работы с сервисом
    # https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api-obschie-swedeniq-autentifikaciq
    _token: str = ""

    @staticmethod
    def _exclude_returned_goods(
            sold_goods: list[RetailDemandPosition], returned_goods: list[RetailReturnedPosition],
    ) -> list[RetailDemandPosition]:
        """Метод удаляет количество товара из списка returned_goods, в списке sold_goods."""
        sold_goods_dict = {good.good_id: good for good in sold_goods}
        for ret in returned_goods:
            if sold_goods := sold_goods_dict.get(ret.good_id):
                if sold_goods.quantity - ret.quantity < 1:
                    del sold_goods_dict[ret.good_id]
                else:
                    sold_goods_dict[ret.good_id] = sold_goods._replace(quantity=(sold_goods.quantity - ret.quantity))
        return list(sold_goods_dict.values())

    def set_token(self, request_new: bool = True) -> bool:
        """Получение токена для доступа и работы с МС по JSON API 1.2. При успешном ответе возвращаем True, в случае ошибок False.

        :param request_new: True, каждый раз будет запрашиваться новый токен,
            если False будет браться из moysklad_privatedata.py
        """
        if self._token:
            return True

        # если необходимо запросить новый токен у сервиса
        if request_new:
            # Получаем url запроса
            url: ms_urls.MoySkladUrl = ms_urls.get_url(
                ms_urls.UrlType.TOKEN,
                start_period=datetime.date.today(),
                end_period=None,
                offset=0,
            )
            # Получаем заголовок запроса
            header: Dict[str, Any] = ms_urls.get_headers(self._token)

            # отправляем запрос в МС для получения токена
            response = requests.post(url.url, headers=header)
            # если получили ответ
            if response.ok:
                # сохраняем токен
                self._token = response.json()["access_token"]
            else:
                return False
        else:
            self._token = os.getenv("MOYSKLAD_TOKEN")
        return True

    def get_assortment(self) -> List[Good]:
        """Функция получения ассортимента товаров."""
        if not self._token:
            return []
        # Т.к. сервис отдает список товаров страницами по 1000, то при запросе
        # необходимо указывать смещение.
        counter: int = 0  # счетчик количества запросов

        # Получаем заголовки для запроса в сервис
        header: Dict[str, Any] = ms_urls.get_headers(self._token)

        need_request: bool = True
        goods: List[Dict[str, Any]] = []

        while need_request:
            # Получаем url для отправки запроса в сервис
            url: ms_urls.MoySkladUrl = ms_urls.get_url(
                ms_urls.UrlType.ASSORTMENT,
                start_period=None,
                end_period=None,
                offset=counter * 1000,
            )

            response = requests.get(url.url, url.request_filter, headers=header)
            if not response.ok:
                return []

            rows: List[Dict[str, Any]] = response.json().get("rows")
            # Проверяем получили ли в ответе не пустой список товаров из
            # ассортимента
            if len(rows) == 1000:
                counter += 1  # увеличиваем счетчик смещений
            # Если список товаров меньше 1000, то сбрасываем флаг о
            # необходимости дополнительных запросов
            elif len(rows) < 1000:
                need_request = False
            # Добавляем новые товары к существующим, расширяем список
            goods.extend(rows)

        return [Good(**good) for good in goods]

    def sync_assortment(self) -> bool:
        """Метод заполняет БД товарами из сервиса МойСклад."""
        # Получаем токен для работы с сервисом МойСклад
        if not self.set_token(request_new=True):
            return False

        # Получаем ассортимент из МойСклад
        ms_goods = self.get_assortment()
        # Обновляем БД объектами ассортимента МойСклад
        if not ms_goods:
            return False

        return ms_model.MoySkladDBGood.save_objects_to_db(list_ms_goods=ms_goods)

    def sync_retail_demand(self, date_: datetime.date) -> bool:
        """Метод импортирует товары из сервиса МойСклад, проданные за текущую дату."""
        # Получаем токен для работы с сервисом МойСклад
        if not self.set_token(request_new=True):
            return False

        # Получаем ассортимент из МойСклад
        ms_sold_goods = self.get_retail_demand_by_period(
            start_period=date_,
            end_period=None,
        )

        ms_returned_goods = self.get_retail_sales_return_by_period(
            start_period=date_,
            end_period=None,
        )

        # Обновляем БД объектами ассортимента МойСклад
        if not ms_sold_goods:
            return False

        if ms_returned_goods:
            ms_sold_goods = self._exclude_returned_goods(sold_goods=ms_sold_goods, returned_goods=ms_returned_goods)

        return ms_model.MoySkladDBRetailDemand.save_objects_to_db(list_retail_demand=ms_sold_goods)

    def get_retail_demand_by_period(
        self,
        start_period: Optional[datetime.date],
        end_period: Optional[datetime.date],
    ) -> List[RetailDemandPosition]:
        """Метод возвращает список, проданных товаров за период.

        :param start_period: начало запрашиваемого периода start_period 00:00:00.
        :param end_period: конец запрашиваемого периода end_period 23:59:00.
        """
        rows: List[Dict[str, Any]] = self._get_retail_data_by_period(
            start_period=start_period, end_period=end_period, data_type=ms_urls.UrlType.RETAIL_DEMAND,
        )

        goods: Dict[str, RetailDemandPosition] = {}

        for retail_demand in rows:
            for position in RetailDemand(**retail_demand).positions.all_:
                if not goods.get(position.good.good_id):
                    goods[position.good.good_id] = RetailDemandPosition(
                        good_id=position.good.good_id,
                        quantity=int(position.quantity),
                        demand_date=RetailDemand(**retail_demand).created.strftime("%Y-%m-%d"),
                    )
                else:
                    goods[position.good.good_id] = goods[position.good.good_id]._replace(
                        quantity=goods[position.good.good_id].quantity + int(position.quantity),
                    )
        return list(goods.values())

    def get_retail_sales_return_by_period(
        self,
        start_period: Optional[datetime.date] = None,
        end_period: Optional[datetime.date] = None,
    ) -> List[RetailReturnedPosition]:
        """Метод возвращает список, возвращенных товаров за период.

        :param start_period: начало запрашиваемого периода start_period 00:00:00.
        :param end_period: конец запрашиваемого периода end_period 23:59:00.
        """
        rows: List[Dict[str, Any]] = self._get_retail_data_by_period(
            start_period=start_period, end_period=end_period, data_type=ms_urls.UrlType.RETAIL_RETURN,
        )

        goods: Dict[str, RetailReturnedPosition] = {}

        for retail_returns in rows:
            for position in RetailDemand(**retail_returns).positions.all_:
                if not goods.get(position.good.good_id):
                    goods[position.good.good_id] = RetailReturnedPosition(
                        good_id=position.good.good_id,
                        quantity=int(position.quantity),
                        demand_date=RetailDemand(**retail_returns).created.isoformat(),
                    )
                else:
                    goods[position.good.good_id] = goods[position.good.good_id]._replace(
                        quantity=goods[position.good.good_id].quantity + int(position.quantity),
                    )
        return list(goods.values())

    def _get_retail_data_by_period(
            self, start_period: Optional[datetime.date], end_period: Optional[datetime.date],
            data_type: ms_urls.UrlType,
    ) -> List[Dict[str, Any]]:
        """Метод возвращает список, проданных или списанных товаров за период.

        :param start_period: начало запрашиваемого периода start_period 00:00:00.
        :param end_period: конец запрашиваемого периода end_period 23:59:00.
        :param data_type: тип запрашиваемых данных RETAIL_DEMAND - розничные продажи, RETAIL_RETURN - возвраты
        """
        if not self._token and (
                data_type != ms_urls.UrlType.RETAIL_DEMAND or data_type != ms_urls.UrlType.RETAIL_RETURN
        ):
            return []

        # Получаем заголовки для запроса в сервис
        header: Dict[str, Any] = ms_urls.get_headers(self._token)

        # Получаем url для отправки запроса в сервис
        url: ms_urls.MoySkladUrl = ms_urls.get_url(
            _type=data_type,
            start_period=start_period,
            end_period=end_period,
            offset=0,
        )
        response = requests.get(url.url, url.request_filter, headers=header)
        if not response.ok:
            return []

        rows: List[Dict[str, Any]] | None = response.json().get("rows")

        return rows
