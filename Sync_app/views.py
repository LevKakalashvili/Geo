from operator import itemgetter
from typing import List, Dict, Union

from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from Sync_app.models import KonturMarketDBGood, KonturMarketDBStock

"""Модуль содержит описание моделей для работы с сервисом Контур.Маркет."""
import datetime

from Sync_app.models.moysklad_models import (
    MoySkladDBRetailDemand,
)
from Sync_app.moysklad.moysklad_constants import GoodType

from django.views.generic import TemplateView


class EgaisView(TemplateView):
    template_name = "Sync_app/egais.html"

    def get(self, request):

        sales: List[Dict[str, str | int]] = []

        date_ = datetime.date.today() - datetime.timedelta(days=1)
        all_sold_ms_goods = MoySkladDBRetailDemand.objects\
            .select_related("uuid") \
            .filter(demand_date__exact=date_)\
            .filter(uuid__is_draft=False) \
            .exclude(uuid__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE])\
            .prefetch_related("uuid__egais_code")\
            .prefetch_related("uuid__egais_code__konturmarketdbstock")\
            .filter(uuid__egais_code__konturmarketdbstock__quantity__gt=0)

        quantity: int = 0
        for good in all_sold_ms_goods:
            quantity = good.quantity
            # TODO: Необходимо учесть в всех случаях ситуацию, что в ЕГАИС остаток меньше, чем нужно списать

            if len(good.uuid.egais_code.all()) < 2:
                sales.append(
                    {
                        "commercial_name": good.uuid.full_name,
                        "name": good.uuid.egais_code.all()[0].full_name,
                        "alcCode": good.uuid.egais_code.all()[0].egais_code,
                        "apCode": good.uuid.egais_code.all()[0].kind_code,
                        "volume": good.uuid.egais_code.all()[0].capacity,
                        # если в БД остаток товара меньше реально проданного, то списываем товар под ноль
                        "quantity": quantity,  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        "price": good.uuid.price,
                    },
                )
            else:
                for km_good in good.uuid.egais_code.all():
                    if km_good.konturmarketdbstock.quantity == 0 or good.quantity == 0:
                        break
                    else:
                        quantity = good.quantity
                        good.quantity = 0

                    sales.append(
                        {
                            "commercial_name": good.uuid.full_name,
                            "name": good.uuid.egais_code.all()[0].full_name,
                            "alcCode": km_good.egais_code,
                            "apCode": km_good.kind_code,
                            "volume": km_good.capacity,
                            # если в БД остаток товара меньше реально проданного, то списываем товар под ноль
                            "quantity": quantity,
                            "price": good.uuid.price,
                        },
                    )

        sales = sorted(sales, key=itemgetter("commercial_name"))

        return render(
            request=request,
            context={"sales": sales},
            template_name=self.template_name,
        )
