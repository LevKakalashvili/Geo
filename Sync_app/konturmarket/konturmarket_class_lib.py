"""В модуле описаны классы для работы с сервисом Контур.Маркет https://market.kontur.ru/."""
import datetime
import json
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
from pydantic import BaseModel, Field

import Sync_app.models.konturmarket_models as km_models
import Sync_app.privatedata.kontrurmarket_privatedata as km_pvdata
from Sync_app.konturmarket.konturmarket_urls import (
    KonturMarketUrl, UrlType, get_url,
)


class Brewery(BaseModel):
    """Класс описывает структуру производителя продукции в соответствии с терминами ЕГАИС. Словарь 'producer' в JSON представлении."""

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

    # Код вида продукции
    kind_code: int = Field(alias="productKindCode")

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

    def __init__(self) -> None:
        """Конструктор."""
        # Переменная устанавливается в True, в случае успешного логина в сервисе
        self._session = requests.Session()

    def get_egais_assortment(self) -> List[StockEGAIS]:
        """Метод возвращает список инстансов GoodEGAIS, полученных из сервиса."""
        goods_list: List[StockEGAIS] = []
        url: KonturMarketUrl = get_url(UrlType.EGAIS_ASSORTMENT)
        response = self._session.get(url.url)

        if not response.ok:
            return []

        goods = response.json().get("list", [])
        # Проходим по всему списку товаров, наименований.
        for good in goods:
            # Получаем словарь с информацией о товаре
            goods_list.append(StockEGAIS(**good))

        # Сортировка по названию пивоварни
        goods_list = sorted(goods_list, key=lambda element: element.good.brewery.short_name)
        return goods_list

    def login(self) -> bool:
        """Метод для логина в сервисе Контур.Маркет."""
        auth_data = {
            "Login": km_pvdata.USER,
            "Password": km_pvdata.PASSWORD,
            "Remember": False,
        }
        # Пытаемся залогиниться на сайте
        url: KonturMarketUrl = get_url(UrlType.LOGIN)
        response = self._session.post(
            url=url.url,
            data=json.dumps(auth_data),
            headers=url.headers,
            cookies=url.cookies,
        )
        return response.ok

    def sync_assortment(self) -> bool:
        """Метод заполняет БД товарами из сервиса КонтурМаркет."""
        if not self.login():
            return False

        km_goods = self.get_egais_assortment()
        if km_goods:
            return km_models.KonturMarketDBGood.save_objects_to_db(list_km_goods=km_goods)

        return True

    def create_sales_journal(self, date_: datetime.date) -> bool:
        """Создание журнала розничных продаж в системе ЕГАИС."""
        if not self.login():
            return False

        url_sales_read: KonturMarketUrl = get_url(UrlType.EGAIS_SALES_JOURNAL_READ)
        response = self._session.get(
            url=url_sales_read.url,
            params={
                "date": str(date_),
            },
        )

        # Если получили ответ журнал не содержит записи
        if response.ok and not response.json().get("day", {}).get("rows", {}):
            journals = km_models.KonturMarketDBGood.get_sales_journal_from_db(date_=date_)
            if journals:
                journal_json = {
                    "day": {
                        "day": str(date_),
                        "rows": [
                            {
                                "rowId": str(count + 1),
                                "alcCode": journal["alcCode"],
                                "apCode": str(journal["apCode"]),
                                "volume": str(journal["volume"]),
                                "quantity": int(journal["quantity"]),
                                "price": int(journal["price"]),
                                "rowType": "New",
                            }
                            for count, journal in enumerate(journals)
                        ],
                    },
                    "writeAutoRows": False,
                }

                #  TODO: При записи журнала в сервисе не пишутся сумма списаний за день и общее количество списываемой
                #   продукции. Надо разобраться
                url_sales_write: KonturMarketUrl = get_url(UrlType.EGAIS_SALES_JOURNAL_WRITE)
                response = self._session.post(url=url_sales_write.url, json=journal_json)
                if response.ok:
                    return True
        return False
