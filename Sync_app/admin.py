from django.contrib import admin

from Sync_app.models import MoySkladDBGood, KonturMarketDBGood


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "uuid", "is_draft", "capacity")
    list_display_links = ("brewery", "name",)
    # search_fields = ("brewery", "name",)
    list_filter = ("brewery",)
    ordering = ("brewery",)


class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    pass


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
