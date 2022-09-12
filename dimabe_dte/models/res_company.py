from odoo import fields, models, api
import logging
import requests
from odoo.exceptions import UserError
from odoo.tools.translate import _
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class ResCompny(models.Model):
    _inherit = 'res.company'

    copies_qty = fields.Integer(string="Cantidad de copias cedibles")

    notification_remaining_caf = fields.Integer(string="Notificación de Folios Restantes", default=0)

    days_acceptation = fields.Integer('Dias de Aceptacion',help="Dias de acceptacion de cliente")

    dte_get_taxpayer_url = fields.Char('URL', help="URL para obtener correo contribuyentes autorizados y actualizar en los contactos")

    dte_get_taxpayer_hash = fields.Char('ApiKey', help="ApiKey  de la compañia para obtener correo contribuyentes autorizados y actualizar en los contactos")

    dte_get_taxpayer_customer_code = fields.Char('Código Compañia', help="Código de la compañia para obtener correo contribuyentes autorizados y actualizar en los contactos")

    @api.model
    def custom_run_update_currency(self, currency_id, date):
        records = self.search([('currency_next_execution_date', '<=', fields.Date.today())])
        if records and date == fields.Date.today():
            self.run_update_currency()
        else:
            self.custom_update_currency_rates(currency_id, date)


    def custom_update_currency_rates(self, currency_id, date):
        rslt = True
        for (currency_provider, companies) in self._group_by_provider().items():
            parse_results = None
            parse_results = self.custom_parse_mindicador_data(currency_id, date)

            if parse_results == False:
                _logger.warning('Unable to connect to the online exchange rate platform %s. The web service may be temporary down.', currency_provider)
                rslt = False
            else:
                companies._generate_currency_rates(parse_results)

        return rslt


    def custom_parse_mindicador_data(self, currency_id, set_date):
        icp = self.env['ir.config_parameter'].sudo()
        server_url = icp.get_param('mindicador_api_url', False)
        if not server_url:
            server_url = 'https://mindicador.cl/api'
            icp.set_param('mindicador_api_url', server_url)

        all_foreigns = {
            "USD": ["dolar", "Dolares"],
            "EUR": ["euro", "Euros"],
            "UF": ["uf", "UFs"],
            "UTM": ["utm", "UTMs"],
        }

        if currency_id:
            foreigns = {
                currency_id.name: all_foreigns[currency_id.name]
            }
        else:
            foreigns = all_foreigns

        available_currency_name = currency_id.name
        _logger.debug('mindicador: available currency names: %s' % available_currency_name)
        request_date = set_date.strftime('%d-%m-%Y')
        rslt = {
            'CLP': (1.0, set_date.strftime(DEFAULT_SERVER_DATE_FORMAT)),
        }
        for index, currency in foreigns.items():
            if index not in available_currency_name:
                _logger.debug('Index %s not in available currency name' % index)
                continue
            url = server_url + '/%s/%s' % (currency[0], request_date)
            try:
                res = requests.get(url)
                res.raise_for_status()
            except Exception as e:
                return False
            if 'html' in res.text:
                return False
            data_json = res.json()
            if len(data_json['serie']) == 0:
                continue
            date = data_json['serie'][0]['fecha'][:10]
            rate = data_json['serie'][0]['valor']
            rslt[index] = (1.0 / rate,  date)
        return rslt

    def custom_generate_currency_rates(self, parsed_data):
        Currency = self.env['res.currency']
        CurrencyRate = self.env['res.currency.rate']

        today = fields.Date.today()
        for company in self:
            rate_info = parsed_data.get(company.currency_id.name, None)

            if not rate_info:
                raise UserError(_("Your main currency (%s) is not supported by this exchange rate provider. Please choose another one.", company.currency_id.name))

            base_currency_rate = rate_info[0]

            for currency, (rate, date_rate) in parsed_data.items():
                format_date_rate = datetime.datetime.strptime(date_rate, '%d-%m-%Y')
                format_date_rate_str = format_date_rate.strftime('%Y-%m-%d')
                rate_value = rate/base_currency_rate

                currency_object = Currency.search([('name','=',currency)])
                already_existing_rate = CurrencyRate.search([('currency_id', '=', currency_object.id), ('name', '=', format_date_rate_str), ('company_id', '=', company.id)])
                if already_existing_rate:
                    already_existing_rate.rate = rate_value
                else:
                    CurrencyRate.create({'currency_id': currency_object.id, 'rate': rate_value, 'name': format_date_rate_str, 'company_id': company.id})