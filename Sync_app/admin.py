from django.contrib import admin

from Sync_app.models import MoySkladDBGood, KonturMarketDBGood


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    pass


class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    pass


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
