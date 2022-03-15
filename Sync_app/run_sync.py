import os
import django

from Sync_app import ms

from Sync_app.moysklad.moysklad_class_lib import Good as ms_Good

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Geo.settings")
django.setup()

from Sync_app.models import Good as db_Good

if __name__ == '__main__':

    # Получаем ассортимент
    goods = ms.get_assortment()
    # Обновляем БД объектами ассортимента
    db_Good.create_and_save_objects_from_list(list_ms_goods=goods)
