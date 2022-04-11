"""Инициализация приложении."""
from Sync_app.konturmarket.konturmarket_class_lib import KonturMarket
from Sync_app.moysklad.moysklad_class_lib import MoySklad

# Получаем токен для работы с сервисом МойСклад
ms = MoySklad()
ms.set_token(request_new=True)

# Создаем инстанс сервиса
kmarket = KonturMarket()
kmarket.login()
