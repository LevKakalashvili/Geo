"""Модуль для вспомогательных функций."""
import string
from typing import Any


def string_title(_str: Any) -> str:
    """Функция отрабатывает так же как string.title(), но учитывает, что после апострофа должен идти символ в нижнем регистре.""" # pylint: disable=line-too-long
    # Т.к. str.title() не корректно обрабатывает апостроф
    if isinstance(_str, list) and len(_str) == 1:
        _str = _str[0]

    if "'" in _str:
        _str = string.capwords(_str)
    else:
        _str = _str.title()

    # Эффект Домино [Ba Cognac]
    if '[Ba ' in _str:
        _str = _str.replace('[Ba ', '[BA ')

    return _str
