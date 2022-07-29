from django.contrib import admin
from django.db.models import QuerySet

from Sync_app.models import MoySkladDBGood


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
    class Media:
        css = {
            "all": ("css/resize_widget_filter_vertical.css",),
        }

    list_display = (
        "brewery",
        "name",
        "uuid",
        "is_draft",
        "capacity",
    )
    list_display_links = (
        "brewery",
        "name",
    )
    search_fields = (
        "brewery",
        "name",
    )
    list_filter = (AlcoListFilter,)
    ordering = ("brewery", "name")

    save_on_top = True

    readonly_fields = (
        "uuid",
        "parent_uuid",
        "full_name",
        "path_name",
        "style",
        "price",
        "brewery",
        "name",
        "abv",
        "og",
        "ibu",
        "is_alco",
        "is_draft",
        "bev_type",
        "capacity",
    )

    filter_vertical = ("egais_code",)


admin.site.register(MoySkladDBGood, MoySkladDBGoodAdmin)
