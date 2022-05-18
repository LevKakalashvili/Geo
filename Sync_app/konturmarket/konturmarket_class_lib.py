"""В модуле описаны классы для работы с сервисом Контур.Маркет https://market.kontur.ru/."""
import json
from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Tuple

import requests
from pydantic import BaseModel
from pydantic import Field

import Sync_app.privatedata.kontrurmarket_privatedata as km_pvdata
from Sync_app.konturmarket.konturmarket_urls import Url
from Sync_app.konturmarket.konturmarket_urls import UrlType
from Sync_app.konturmarket.konturmarket_urls import get_url


session = requests.Session()


class Brewery(BaseModel):
    """Класс описывает структуру компании производителя, продукции в соответствии с терминами ЕГАИС. Словарь 'producer' в JSON представлении."""

    # Короткое наименование производителя
    short_name: str = Field(alias="shortName")
    # Полное наименование производителя
    full_name: str = Field(alias="name")
    # ИНН производителя
    inn: Optional[str]
    # Уникальный ЕГАИС идентификатор производителя
    fsrar_id: str = Field(alias="fsrarId")


class GoodEGAIS(BaseModel):
    """Класс описывает структуру товара, продукции в соответствии с терминами ЕГАИС. Словарь 'productInfo' в JSON представлении."""

    # ЕГАИС наименование
    name: str = Field(alias="fullName")

    # Код алкогольной продукции (код АП) в ЕГАИС. Уникальный 19-ти значный код. Если значащих цифр в
    # коде меньше 19-ти, то вперед дописываются нули. Это при строковом
    # представлении
    alco_code: str = Field(alias="egaisCode")

    # Емкость тары. Не обязательный параметр. Отсутствие этого параметра
    # говорит о том, что товар разливной
    capacity: Optional[float] = None

    # Описание производителя
    brewery: Brewery = Field(alias="producer")

    def to_tuple(self) -> Tuple[str, str, str]:
        """Метод возвращает кортеж вида (ЕГАИС_НАИМЕНОВАНИЕ, ЕГАИС_КОД)."""
        return self.name, self.alco_code, self.brewery.short_name

    def get_description(self) -> str:
        """Метод возвращает кортеж с наименованием товара."""
        return f"Пивоварня: {self.brewery.short_name}  Наименование: {self.name}  Код: {self.alco_code}"


class StockEGAIS(BaseModel):
    """Класс описывает структуру остатка товара, продукции в соответствии с терминами ЕГАИС."""

    # Количество товара на остатках ЕГАИС в 1ом регистре.
    quantity_1: Optional[float] = Field(alias="quantity")

    # Количество товара на остатках ЕГАИС в 2ом регистре.
    quantity_2: Optional[float] = Field(alias="shopQuantity")

    # Структура товара ЕГАИС
    good: GoodEGAIS = Field(alias="productInfo")


@dataclass()
class KonturMarket:
    """Класс описывает работу с сервисом Контур.Маркет https://market.kontur.ru/."""

    # Переменная устанавливается в True, в случае успешного логина в сервисе
    connection_ok: bool = False

    @staticmethod
    def get_egais_assortment() -> List[GoodEGAIS]:
        """Метод возвращает список инстансов GoodEGAIS, полученных из сервиса."""
        goods_list: List[GoodEGAIS] = []
        url: Url = get_url(UrlType.EGAIS_ASSORTMENT)
        response = session.get(url.url)

        goods = dict(response.json()).get("list")
        # Если получили успешный ответ и есть список товаров
        if response.ok and goods:
            # Проходим по всему списку товаров, наименований.
            for good in goods:
                # Получаем словарь с информацией о товаре
                goods_list.append(StockEGAIS(**good))

            # Сортировка по названию пивоварни
            goods_list = sorted(
                goods_list, key=lambda element: element.good.brewery.short_name
            )
            return goods_list
        return []

    def login(self) -> bool:
        """Метод для логина в сервисе Контур.Маркет."""
        auth_data = {
            "Login": km_pvdata.USER,
            "Password": km_pvdata.PASSWORD,
            "Remember": False,
        }
        # Пытаемся залогиниться на сайте
        url: Url = get_url(UrlType.LOGIN)
        response = session.post(
            url=url.url,
            data=json.dumps(auth_data),
            headers=url.headers,
            cookies=url.cookies,
        )
        self.connection_ok = response.ok

        return response.ok
