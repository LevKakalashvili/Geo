"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
import datetime

from django.core.management.base import BaseCommand

import Sync_app.konturmarket.konturmarket_class_lib as km_class


class Command(BaseCommand):  # noqa: D101
    help = "Заполнение журнала продаж в КонтурМаркет. "  # noqa

    def add_arguments(self, parser):
        parser.add_argument(
            "date",
            type=lambda date_: datetime.datetime.strptime(date_, "%Y-%m-%d").date(),
            nargs='?',
            default=datetime.datetime.today().strftime('%Y-%m-%d'),
            help="Создать журнал за выбранную дату. Если не указывать, по умолчанию - today.",
        )

    def handle(self, *args, **kwargs):
        journal_date = kwargs["date"]

        if journal_date:
            km: km_class.KonturMarket = km_class.KonturMarket()

            if not km.create_sales_journal(date_=journal_date):
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось создать журнал продаж в сервисе Конур.Маркет."))
            else:
                self.stdout.write(self.style.SUCCESS(f"ОК. Контур.Маркет журнал продаж {journal_date.__str__()}."))
