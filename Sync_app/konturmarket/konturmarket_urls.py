"""В модуле хранятся url'ы для сервиса Конутр.Маркет https://market.kontur.ru/."""
from enum import Enum
from typing import Dict, NamedTuple

AUTH_URL = "https://auth.kontur.ru/api/authentication/password/auth-by-password"
EGAIS_ASSORTMENT_URL = (
    "https://market.kontur.ru/api/v105/a095a331-45ed-444e-8977-0a1eb28fee92/ae2fa6c7-dcbb-4c0b"
    "-b4e2-3d63bb6eabd5/055adf4b-e674-4dcd-9095-3e8c31785ac9/Rests/List"
)


class UrlType(Enum):
    """Перечисление для определения, какой тип url необходимо сформировать.

    login - авторизация пользователя.
    egais_assortment - справочник товаров (ЕГАИС наименований)
    """

    LOGIN = 1
    EGAIS_ASSORTMENT = 2


class KonturMarketUrl(NamedTuple):
    """Класс в котором описываются url, заголовки и cookies для передачи в запросе к сервису Контур.Маркет."""

    url: str  # Url для запроса в сервис.

    # Словарь cookies для передачи в запросе к сервису Контур.Маркет
    cookies: Dict[str, str] = {"AntiForgery": "78bc4821-5d13-4744-a103-1a762614ec22"}

    # Словарь заголовков для передачи в запросе к сервису Контур.Маркет.
    headers: Dict[str, str] = {
        "Content-Type": "application/json;charset=utf-8",
        "X-CSRF-Token": "78bc4821-5d13-4744-a103-1a762614ec22",
    }


def get_url(url_type: UrlType) -> KonturMarketUrl:
    """Метод для получения url.

    :param url_type: UrlType.login - url для авторизации в сервисе, UrlType.egais_assortment - url для списка ЕГАИС
    наименований.
    :returns: Возвращается объект Url
    """
    url: KonturMarketUrl

    if url_type == UrlType.LOGIN:
        # Возвращаем ссылку на форму для авторизации в сервисе
        url = KonturMarketUrl(url=AUTH_URL)
    elif url_type == UrlType.EGAIS_ASSORTMENT:
        # Возвращаем ссылку на раздел в Товары/Пиво в сервисе Конутр.Маркет
        url = KonturMarketUrl(url=EGAIS_ASSORTMENT_URL)
    return url
