from django.urls import path

import Sync_app.views
from . import views
from django.contrib import admin

admin.site.site_header = 'География'
admin.site.index_title = f"{admin.site.site_header}. Администрирование"
admin.site.site_title = admin.site.site_header

urlpatterns = [
    # path("", Sync_app.views.EgaisView.as_view()),
    # path("<page_name>", views.get_page),
]
