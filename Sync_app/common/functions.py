"""Модуль для вспомогательных функций."""
import string
from typing import List


def string_title(list_: List[str]) -> str:
    """Функция отрабатывает так же как string.title(), но учитывает, что после апострофа должен идти символ в нижнем регистре."""
    # Т.к. str.title() не корректно обрабатывает апостроф
    if isinstance(list_, list) and len(list_) == 1:
        str_ = list_[0]

    # Эффект Домино [Ba Cognac]
    if "[Bа Cognac] " in str_:
        str_ = str_.replace("[Bа Cognac]", "[BA Cognac]")
        return str_

    if "'" in str_:
        str_ = string.capwords(list_)
    else:
        str_ = str_.title()

    return str_
