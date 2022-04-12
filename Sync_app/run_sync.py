import os
import django

from Sync_app import kmarket
from Sync_app import ms

from Sync_app.konturmarket.konturmarket_class_lib import GoodEGAIS as km_Good
from Sync_app.moysklad.moysklad_class_lib import Good as ms_Good

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Geo.settings")
django.setup()

from Sync_app.models.konturmarket_models import KonturMarketDBGood as db_km_good
from Sync_app.models.moysklad_models import MoySkladDBGood as db_ms_good

if __name__ == '__main__':

    # Получаем ассортимент из МойСклад
    ms_goods = ms.get_assortment()
    # Обновляем БД объектами ассортимента МойСклад
    db_ms_good.save_objects_to_storage(list_ms_goods=ms_goods)

    # Получаем ассортимент КонтурМаркет
    km_goods = kmarket.get_egais_assortment()
    # Обновляем БД объектами справочника из сервиса Контур.Маркет
    db_km_good.save_objects_to_storage(list_km_goods=km_goods)

