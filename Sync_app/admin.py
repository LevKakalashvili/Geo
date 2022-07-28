from django.contrib import admin
from django.db.models import QuerySet
from django.db import models
from django.forms import TextInput, Textarea

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
    extra = 1
    verbose_name = "ЕГАИС наименование"
    verbose_name_plural = "ЕГАИС наименования"


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "uuid", "is_draft", "capacity",)
    list_display_links = ("brewery", "name",)
    search_fields = ("brewery", "name",)
    list_filter = (AlcoListFilter,)
    ordering = ("brewery", "name")
    autocomplete_fields = ["egais_code"]

    # filter_vertical = ('egais_code',)

    # class Media:
    #     css = {
    #         'all': ("css/resize_widget_filter_vertical.css",),
    #     }

    def get_form(self, request, obj=None, **kwargs):
        form = super(MoySkladDBGoodAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['egais_code'].widget.attrs['style'] = 'width: 100%;'
        return form

class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    fields = ('full_name', 'egais_code')
    search_fields = ['egais_code']

admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
