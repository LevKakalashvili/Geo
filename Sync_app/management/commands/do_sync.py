"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
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
            help="Запустить синхронизацию ассортимента из МойСклад",
        )

        parser.add_argument(
            "-ka",
            "--konturmarket_assortment",
            action="store_true",
            default=False,
            help="Запустить синхронизацию товаров из Контур.Маркет",
        )

        parser.add_argument(
            "-gct",
            "--google_compl_table",
            action="store_true",
            default=False,
            help="Запустить синхронизацию таблицы соответствия из GoogleSheets",
        )

    def handle(self, *args: Tuple[str], **kwargs: Dict[str, Any]) -> None:  # noqa: D102

        moysklad_assortment = kwargs["moysklad_assortment"]
        konturmarket_assortment = kwargs["konturmarket_assortment"]
        google_compl_table = kwargs["google_compl_table"]

        # Синхронизация МойСклад
        if moysklad_assortment:
            ms: ms_class.MoySklad = ms_class.MoySklad()

            if not ms.sync_assortment():
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось получить данные из сервиса МойСклад."))

        # Синхронизация КонтурМаркет
        if konturmarket_assortment:
            km: km_class.KonturMarket = km_class.KonturMarket()

            if not km.sync_assortment():
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось получить данные из сервиса Конур.Маркет."))

        # Синхронизация GoogleSheets
        if google_compl_table:
            gs: GoogleSheets = GoogleSheets()

            if not gs.sync_compl_table():
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось создать таблицу соответствий."))
