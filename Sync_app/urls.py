from django.urls import path
from . import views

urlpatterns = [
    path("<page_name>", views.get_page),
]
