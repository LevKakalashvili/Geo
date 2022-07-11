from django.urls import path
from . import views

urlpatterns = [
    path("", views.get_sales_journal_from_db),
    # path("<page_name>", views.get_page),
]
