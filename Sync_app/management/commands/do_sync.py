"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
import datetime
import sys
from typing import Any, Dict, Tuple

from django.core.management.base import BaseCommand, CommandParser

import Sync_app.konturmarket.konturmarket_class_lib as km_class
import Sync_app.moysklad.moysklad_class_lib as ms_class
from Sync_app.googledrive.googledrive_class_lib import GoogleSheets


class Command(BaseCommand):  # noqa: D101
    help = "Заполнение БД из сервисов МойСклад, КонтурМаркет. "  # noqa

    def add_arguments(self, parser: CommandParser) -> None:  # noqa: D102

        parser.add_argument(
            "-ma",
            "--moysklad_assortment",
            action="store_true",
            default=False,
            help="Запустить синхронизацию ассортимента из МойСклад.",
        )

        parser.add_argument(
            "-mrd",
            "--moysklad_retaildemand",
            type=datetime.date.fromisoformat,
            nargs='?',
            # Значение даты по умолчанию
            const=datetime.date.today().isoformat(),
            default=False,
            help="Запустить импорт товаров, проданных за указанную дату. Если не указывать, по умолчанию - today.",
        )

        parser.add_argument(
            "-ka",
            "--konturmarket_assortment",
            action="store_true",
            default=False,
            help="Запустить синхронизацию товаров из Контур.Маркет.",
        )

        parser.add_argument(
            "-gct",
            "--google_compl_table",
            action="store_true",
            default=False,
            help="Запустить синхронизацию таблицы соответствия из GoogleSheets.",
        )

    def handle(self, *args: Tuple[str], **kwargs: Dict[str, Any]) -> None:  # noqa: D102

        moysklad_assortment = kwargs["moysklad_assortment"]
        moysklad_retaildemand = kwargs["moysklad_retaildemand"]
        konturmarket_assortment = kwargs["konturmarket_assortment"]
        google_compl_table = kwargs["google_compl_table"]

        ms: ms_class.MoySklad = ms_class.MoySklad()

        # Синхронизация МойСклад
        if moysklad_assortment:

            if ms.sync_assortment():
                self.stdout.write(self.style.SUCCESS("ОК. МойСклад синхронизация товаров."))
            else:
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось получить данные из сервиса МойСклад."))

        # Импорт товаров, проданных за смену
        if moysklad_retaildemand:
            if ms.sync_retail_demand(date_=moysklad_retaildemand):
                self.stdout.write(
                    self.style.SUCCESS(f"ОК. МойСклад розничные продажи за {moysklad_retaildemand.__str__()}.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Ошибка. Не удалось получить товары, проданные за смену из сервиса МойСклад.")
                )

        # Синхронизация КонтурМаркет
        if konturmarket_assortment:
            km: km_class.KonturMarket = km_class.KonturMarket()

            if km.sync_assortment():
                self.stdout.write(self.style.SUCCESS("ОК. Контур.Маркет синхронизация товаров."))
            else:
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось получить данные из сервиса Конур.Маркет."))

        # Синхронизация GoogleSheets
        if google_compl_table:
            gs: GoogleSheets = GoogleSheets()

            if gs.sync_compl_table():
                self.stdout.write(self.style.SUCCESS("ОК. GoogleSheets таблица соответствий."))
            else:
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось создать таблицу соответствий."))
