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
        sales = []

        date_ = datetime.date.today() - datetime.timedelta(days=4)
        all_sold_goods = MoySkladDBRetailDemand.objects \
            .select_related("uuid") \
            .filter(uuid__is_draft=False) \
            .exclude(uuid__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE])\
            .prefetch_related("uuid__egais_code")\
            .prefetch_related("uuid__egais_code__konturmarketdbstock")\
            .filter(uuid__egais_code__konturmarketdbstock__quantity__gt=0)

        # all_km_goods = KonturMarketDBGood.objects.all(). \
        #     filter()

        for sold_good in all_sold_goods:
            a = sold_good.uuid.egais_code.all().__len__()
            if a > 1:
                b = 2
            #     list(sold_good.uuid.egais_code.all())[1].konturmarketdbstock.quantity
            # pass

        return render(
            request=request,
            context=dict(sales),
            template_name=self.template_name,
        )
