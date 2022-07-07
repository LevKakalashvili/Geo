from django.urls import path
from Sync_app.views import egais

urlpatterns = [
    path("<egais>", egais),
]
