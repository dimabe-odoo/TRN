import locale
from datetime import datetime


def get_date_spanish(date_to_search):
    locale.setlocale(locale.LC_TIME, 'es_CL.utf8')
    datetime_data = datetime(date_to_search.year, date_to_search.month, date_to_search.day)
    return datetime_data.strftime('%B-%y')
