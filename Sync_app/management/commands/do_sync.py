"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
from django.core.management.base import BaseCommand
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import Sync_app.moysklad.moysklad_class_lib as ms_class


class Command(BaseCommand):
    help = "Запуск синхронизации."

    def add_arguments(self, parser):
        parser.add_argument('-ms_assort', '--moysklad_assortment', action='store_true', help='Запустить синхронизацию ассортимента')

    def handle(self, *args, **kwargs):
        moysklad_assortment = kwargs['moysklad_assortment']

        if moysklad_assortment:
            ms: ms_class.MoySklad = ms_class.MoySklad()
            if not ms.sync_assortment():
                self.stdout.write(self.style.ERROR('Ошибка. Не удалось получить данные из сервиса МойСклад.'))
