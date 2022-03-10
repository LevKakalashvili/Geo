from Sync_app.moysklad.moysklad_class_lib import MoySklad

# Получаем токен для работы с сервисом МойСклад
ms = MoySklad()
ms.set_token(request_new=False)
