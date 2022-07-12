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

        date_ = datetime.date.today() - datetime.timedelta(days=2)
        # Получаем uuid из продаж
        goods = MoySkladDBRetailDemand.objects \
            .select_related() \
            .filter(demand_date=date_) \
            .prefetch_related("uuid__egais_code") \
            .filter(uuid__is_draft=False) \
            .exclude(uuid__bev_type__in=[GoodType.KOMBUCHA, GoodType.OTHER, GoodType.LEMONADE]) \
            .prefetch_related("uuid__egais_code__km_db_stock_good")

        return render(
            request=request,
            context=dict(sales),
            template_name=self.template_name,
        )
