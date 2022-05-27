"""Модуль для вспомогательных функций."""
import string
from typing import List, Optional


def string_title(list_: Optional[List[str]]) -> str:
    """Функция отрабатывает так же как string.title(), но учитывает, что после апострофа должен идти символ в нижнем регистре."""
    str_: str = ""
    # Т.к. str.title() не корректно обрабатывает апостроф
    if isinstance(list_, list) and len(list_) == 1:
        str_ = "".join(list_)
    else:
        str_ = str(list_)

    # Эффект Домино [Ba Cognac]
    if "[Bа Cognac] " in str_:
        str_ = str_.replace("[Bа Cognac]", "[BA Cognac]")
        return str_

    if "'" in str_:
        str_ = string.capwords(str_)
    else:
        str_ = str_.title()

    return str_
