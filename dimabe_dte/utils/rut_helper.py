import re

class RutHelper:

    @staticmethod
    def format_rut(rut):
        rut = re.sub('\D+(?!$)', '', rut)
        return rut[:-1]+'-'+rut[-1]

    def format_rut_dotted(rut):
        t = rut.split('-')
        t = '{:,}'.format(int(t[0])).replace(',', '.') + '-' + str(t[1])
        return t