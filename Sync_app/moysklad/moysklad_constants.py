"""Константы для работы с сервисом МойСклад."""
from enum import Enum
from typing import Dict, Tuple

_TRASH: Tuple[str, ...] = (
    " (0,75)",
    " (0,33)",
    " Бутылка 0,75",
    " ж\\б",
    " (ж/б)",
    " (0,5)",
)

_MODIFICATION_SET: Dict[str, float] = {
    "Банка 0,33": 0.33,
    "Банка 0,45": 0.45,
    "Бутылка 0,33": 0.33,
    "Бутылка 0,375": 0.375,
    "Бутылка 0,5": 0.5,
    "Бутылка 0,75": 0.75,
    "ж.б 0,33": 0.33,
    "ж/б 0,5": 0.5,
}


class GoodType(Enum):
    """Перечисление типов товаров."""

    BEER = ("beer",)
    CIDER = ("cider",)
    KOMBUCHA = ("kombucha",)
    LEMONADE = ("lemonade",)
    MEAD = ("mead",)
    OTHER = ("other",)


class AlcoType(Enum):
    """Перечисление для определения, какой тип товаров необходимо получить.

    alco - алкогольная продукция (исключая разливное пиво).
    non_alco - не алкогольная продукция
    """

    alco = 1
    non_alco = 2


class Characteristics(Enum):
    """Перечисление используемое для получения характеристик продукта при парсинге строки продукта."""

    ABV = "abv"
    OG = "og"
    IBU = "ibu"
