from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render


# Create your views here.
def get_page(requests, page_name):
    if page_name == "egais":
        return HttpResponse("Страничка ЕГАИС 1")
    else:
        return HttpResponseNotFound(f"Страница не найдена")

