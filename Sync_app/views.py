from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render


# Create your views here.
def get_page(request, page_name):
    if page_name == "egais":
        return render(request, "Sync_app/egais.html")
    else:
        return HttpResponseNotFound(f"Страница не найдена")
