from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def get_page(requests, page_name):
    if page_name == "egais":
        return egais()


def egais(request):
    return HttpResponse("Страничка ЕГАИС 1")
