from django.urls import path

import Sync_app.views
from . import views

urlpatterns = [
    # path("", Sync_app.views.EgaisView.as_view()),
    path("<page_name>", views.get_page),
]
