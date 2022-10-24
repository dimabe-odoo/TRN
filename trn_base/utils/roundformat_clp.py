from math import floor, ceil
import locale
from odoo.http import request

def round_clp(value):
    value_str = str(value)
    list_value = value_str.split('.')
    if len(list_value) > 1:
        decimal = int(list_value[1][0])
        if decimal == 0:
            return format_clp(int(value))
        elif decimal < 5:
            return format_clp(floor(value))
        else:
            return format_clp(ceil(value))

    else:
        return format_clp(value)


def format_clp(value):
    return '{:,}'.format(value).replace(',', '.')


def format_usd(value):
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
    locale._override_localeconv = {'mon_thousands_sep': '.'}
    value_str = locale.currency(value, symbol=False, grouping=True)
    return value_str

def format_qty(value):
    locale.setlocale(locale.LC_ALL, 'es_ES.utf8')
    locale._override_localeconv = {'mon_thousands_sep': '.'}
    value_str = locale.currency(value, symbol=False, grouping=True)
    if '00' == value_str[-2:]:
        return value_str[:-3]
    return value_str
