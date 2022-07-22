from django.contrib import admin
from django.db.models import QuerySet

from Sync_app.models import MoySkladDBGood, KonturMarketDBGood


class AlcoListFilter(admin.SimpleListFilter):
    title = ""
    parameter_name = "alco"
    default_value = None
    related_filter_parameter = parameter_name

    def lookups(self, request, model_admin):
        return [
            (self.parameter_name, "Алкогольная продукция"),
        ]

    def queryset(self, request, queryset: QuerySet):
        if self.used_parameters:
            if self.used_parameters.get(self.parameter_name):
                return queryset.exclude(is_alco=False)
        return queryset


class MoySkladDBGoodKonturMarketDBGoodMatches(admin.TabularInline):
    model = MoySkladDBGood.egais_code.through
    extra = 0
    verbose_name = "ЕГАИС наименование"
    verbose_name_plural = "ЕГАИС наименования"
    # raw_id_fields = ("full_name",)


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "uuid", "is_draft", "capacity")
    list_display_links = ("brewery", "name",)
    search_fields = ("brewery", "name",)
    list_filter = (AlcoListFilter,)
    ordering = ("brewery", "name")
    inlines = [MoySkladDBGoodKonturMarketDBGoodMatches, ]

    exclude = ("egais_code",)


class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    fields = ('full_name', 'egais_code')
    inlines = [MoySkladDBGoodKonturMarketDBGoodMatches, ]


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
