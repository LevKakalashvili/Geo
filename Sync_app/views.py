from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from Sync_app.models import KonturMarketDBGood, KonturMarketDBStock

"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
import datetime
import sys
from operator import itemgetter
from typing import TYPE_CHECKING, Dict, List, Union

from django.core.exceptions import ObjectDoesNotExist
from Sync_app.models.moysklad_models import (
    MoySkladDBGood, MoySkladDBRetailDemand,
)
from Sync_app.moysklad.moysklad_constants import GoodType


def get_sales_journal_from_db(request):
    """Метод для получения журнала розничных продаж алкоголя из БД."""
    sales: List[Dict[str, Union[str, int]]] = []
    date_ = datetime.date.today() - datetime.timedelta(days=1)
    # TODO: Переделать запросы в цикле на select_related/prefetch_related
    # Получаем uuid из продаж
    for retail_demand in MoySkladDBRetailDemand.objects.select_related().filter(demand_date=date_).only("uuid_id", "quantity"):

        # Если к коммерческому товару привязано несколько товаров ЕГАИС, и остаток всех товаров ЕГАИС не нулевое
        # то, KonturMarketDBGood.objects.filter(goods__uuid__exact=retail_demand.uuid_id, goods__is_draft=False)
        # вернет список длиной больше 1
        # Нужно проверить, если количество проданного товара, меньше либо равно остатку текущего остатка ЕГАИС,
        # то списываем и брейком выходим из цикла
        # Если количество проданного товара, больше, чем остаток текущего элемента ЕГАИС, то нужно добавить текущий
        # элемент ЕГАИС в список для списания, уменьшить количество проданного товара и перейти к следующему элементу ЕГАИС

        # Получаем все объекты ЕГАИС связанные c текущим товаром МойСклад
        km_goods = KonturMarketDBGood.objects.select_related("konturmarketdbstock").filter(
            goods__uuid__exact=retail_demand.uuid_id,
            goods__is_draft=False,
            # Исключаем комбуча, лимонады и прочее
        ).exclude(
            goods__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE]
        ).only("full_name", "egais_code", "kind_code", "capacity").filter(goods__goods_related__quantity__gt=0)

        for km_good in km_goods:
            # Проверяем товар по таблице остатков ЕГАИС
            # Если не удалось найти товар с таким ЕГАИС кодом и положительным остатком
            # пропускаем товар
            try:
                km_stock = KonturMarketDBStock.objects.get(egais_code__exact=km_good.egais_code, quantity__gt=0)
            except ObjectDoesNotExist:
                # TODO: переделать на логгер
                sys.stdout.write(
                    f"Предупреждение. Не удалось получить ЕГАИС остаток для кода: {km_good.egais_code}, товара: {retail_demand.uuid.full_name}.\n",
                )
                continue

            # Если списали все количество за раз, выходим из цикла. Списали все, что нужно
            if retail_demand.quantity == 0:
                break

            quantity: int = 0
            # Если остаток ЕГАИС больше или равен количеству проданного товара
            if km_stock.quantity >= retail_demand.quantity:
                quantity = retail_demand.quantity
                retail_demand.quantity -= 0
            else:
                quantity = km_stock.quantity
                retail_demand.quantity -= km_stock.quantity

            sales.append(
                {
                    "commercial_name": retail_demand.uuid.full_name,
                    "name": km_good.full_name,
                    "alcCode": km_good.egais_code,
                    "apCode": km_good.kind_code,
                    "volume": km_good.capacity,
                    # если в БД остаток товара меньше реально проданного, то списываем товар под ноль
                    "quantity": quantity,
                    "price": retail_demand.uuid.price,
                },
            )

    sales = sorted(sales, key=itemgetter("commercial_name"))
    return render(
        request=request,
        template_name="Sync_app/egais.html",
        context={
            "sales": sales,
            }
        )

# Create your views here.
def get_page(request):
    # if page_name == "":
    return render(request, "Sync_app/egais.html")
    # else:
    #     return HttpResponseNotFound(f"Страница не найдена")
