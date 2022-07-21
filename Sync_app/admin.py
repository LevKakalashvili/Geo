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


class MoySkladDBGoodAdmin(admin.ModelAdmin):
    list_display = ("brewery", "name", "uuid", "is_draft", "capacity")
    list_display_links = ("brewery", "name",)
    search_fields = ("brewery", "name",)
    list_filter = (AlcoListFilter,)
    ordering = ("brewery", "name")

    def changelist_view(self, request, extra_context=None):
        if "HTTP_REFERER" in request.META:
            test = request.META['HTTP_REFERER'].split(request.META['PATH_INFO'])

        if test[-1] and not test[-1].startswith('?'):
            if AlcoListFilter.parameter_name not in request.GET:
                q = request.GET.copy()
                q[AlcoListFilter.parameter_name] = AlcoListFilter.parameter_name
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(MoySkladDBGoodAdmin, self).changelist_view(request, extra_context=extra_context)


class KonturMarketDBGoodAdmin(admin.ModelAdmin):
    pass


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
admin.site.register(KonturMarketDBGood, KonturMarketDBGoodAdmin)
