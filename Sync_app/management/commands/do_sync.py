"""Команда запуска синхронизации с МойСклад, КонтурМаркет, GoogleSheets."""
from typing import Dict, Tuple, Any

from django.core.management.base import BaseCommand, CommandParser

import Sync_app.moysklad.moysklad_class_lib as ms_class


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

    def handle(self, *args: Tuple[str], **kwargs: Dict[str, Any]) -> None:  # noqa: D102

        moysklad_assortment = kwargs["moysklad_assortment"]

        if moysklad_assortment:
            ms: ms_class.MoySklad = ms_class.MoySklad()

            if not ms.sync_assortment():
                self.stdout.write(self.style.ERROR("Ошибка. Не удалось получить данные из сервиса МойСклад."))
