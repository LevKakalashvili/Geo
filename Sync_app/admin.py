from django.contrib import admin

from Sync_app.models import MoySkladDBGood, KonturMarketDBGood


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "style")

    @admin.display(ordering="brewery")
    def oder_by_brewery_name(self):
        pass


class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    pass


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
