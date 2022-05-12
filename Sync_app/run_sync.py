import os
import django
from typing import List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Geo.settings")
django.setup()

from Sync_app import googlesheets, ms, kmarket
import Sync_app.models.app_models_func as db_func

import Sync_app.googledrive.googlesheets_vars as gs_vars
from Sync_app.models.konturmarket_models import KonturMarketDBGood as db_km_good
from Sync_app.models.moysklad_models import MoySkladDBGood as db_ms_good


if __name__ == '__main__':
    # Получаем ассортимент из МойСклад
    ms_goods = ms.get_assortment()

    # Обновляем БД объектами ассортимента МойСклад
    db_ms_good.save_objects_to_db(list_ms_goods=ms_goods)

    # Получаем ассортимент КонтурМаркет
    km_goods = kmarket.get_egais_assortment()
    # Обновляем БД объектами справочника из сервиса КонтурМаркет
    db_km_good.save_objects_to_db(list_km_goods=km_goods)

    # Получаем таблицу соответствий из google таблицы
    compl_table: List[List[str]] = googlesheets.get_data(
        spreadsheets_id=gs_vars.SPREEDSHEET_ID_EGAIS,
        list_name=gs_vars.LIST_NAME_EGAIS,
        list_range=f'{gs_vars.FIRST_CELL_EGAIS}:{gs_vars.LAST_COLUMN_EGAIS}'
        )
    # Оставляем только коммерческое название и код алкогольной продукции
    compl_table = [i[:len(i):2] for i in compl_table]
    a = db_func.db_set_matches(googlesheets_copm_table=compl_table)
    # a = db_ms_good.objects.all()
    b = 1
