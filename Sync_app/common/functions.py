"""Модуль для вспомогательных функций."""
import string


def string_title(_str: str) -> str:
    """Функция отрабатывает так же как string.title(), но учитывает, что после апострофа должен идти символ в нижнем
    регистре."""
    # Т.к. str.title() не корректно обрабатывает апостроф
    if type(_str) is list and len(_str) == 1:
        _str = _str[0]

    if '\'' in _str:
        _str = string.capwords(_str)
    else:
        _str = _str.title()

    # Эффект Домино [Ba Cognac]
    if '[Ba ' in _str:
        _str = _str.replace('[Ba ', '[BA ')

    return _str
