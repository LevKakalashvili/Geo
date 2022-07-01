"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
import datetime
import sys

from django.core.management.base import BaseCommand

import Sync_app.konturmarket.konturmarket_class_lib as km_class


class Command(BaseCommand):  # noqa: D101
    help = "Заполнение журнала продаж в КонтурМаркет. "  # noqa

    def add_arguments(self, parser):
        parser.add_argument(
            "date",
            type=datetime.date.fromisoformat,
            nargs='?',
            default=datetime.date.today().isoformat(),
            help="Создать журнал за выбранную дату. Если не указывать, по умолчанию - today.",
        )

    def handle(self, *args, **kwargs):
        journal_date = kwargs["date"]

        km: km_class.KonturMarket = km_class.KonturMarket()

        if km.create_sales_journal(date_=journal_date):
            self.stdout.write(self.style.SUCCESS(f"ОК. Контур.Маркет журнал продаж {str(journal_date)}."))
        else:
            self.stdout.write(self.style.ERROR("Ошибка. Не удалось создать журнал продаж в сервисе Конур.Маркет."))
