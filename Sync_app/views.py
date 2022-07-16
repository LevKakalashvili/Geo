import datetime
from operator import itemgetter
from typing import Dict, List

from django.shortcuts import render
from django.views.generic import TemplateView

from Sync_app.models.moysklad_models import MoySkladDBRetailDemand
from Sync_app.moysklad.moysklad_constants import GoodType


class EgaisView(TemplateView):
    template_name = "Sync_app/egais.html"

    def get(self, request):

        sales: List[Dict[str, str | int]] = []

        date_ = datetime.date.today() - datetime.timedelta(days=2)
        all_sold_ms_goods = (
            MoySkladDBRetailDemand.objects.select_related("uuid")
            .filter(demand_date__exact=date_)
            .filter(uuid__is_draft=False)
            .exclude(uuid__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE])
            .prefetch_related("uuid__egais_code")
            .prefetch_related("uuid__egais_code__konturmarketdbstock")
            .filter(uuid__egais_code__konturmarketdbstock__quantity__gt=0)
        )

        quantity: int = 0

        for good in all_sold_ms_goods:
            for km_good in good.uuid.egais_code.all():
                # Если остаток товара в ЕГАИС = 0
                if not km_good.konturmarketdbstock.quantity:
                    continue

                # Если товара в ЕГАИС больше, чем продано
                if km_good.konturmarketdbstock.quantity >= good.quantity:
                    quantity = good.quantity
                    good.quantity = 0
                    km_good.konturmarketdbstock.quantity -= good.quantity
                # Если товара в ЕГАИС меньше, чем продано
                elif km_good.konturmarketdbstock.quantity < good.quantity:
                    quantity = km_good.konturmarketdbstock.quantity
                    good.quantity -= km_good.konturmarketdbstock.quantity
                    km_good.konturmarketdbstock.quantity = 0

                sales.append(
                    {
                        "commercial_name": good.uuid.full_name,
                        "name": km_good.full_name,
                        "alcCode": km_good.egais_code,
                        "apCode": km_good.kind_code,
                        "volume": km_good.capacity,
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
