from odoo import models, api, fields
from ..utils.rut_helper import RutHelper
from datetime import date
import requests
import json

class ResPartner(models.Model):
    _inherit = 'res.partner'
    l10n_cl_dte_email_update_at = fields.Date('Fecha de actualización correo intercambio')

    @api.model
    def create(self, values):
        if isinstance(values, list):
            for val in values:
                if 'parent_id' in val.keys():
                    parent_id = self.env['res.partner'].search([('id', '=', val['parent_id'])])
                    if parent_id.l10n_cl_dte_email and parent_id.l10n_cl_dte_email != '':
                        val['l10n_cl_dte_email'] = parent_id.l10n_cl_dte_email
                        val['l10n_cl_activity_description'] = parent_id.l10n_cl_activity_description
        else:
            if 'parent_id' in values.keys():
                parent_id = self.env['res.partner'].search([('id', '=', values['parent_id'])])
                if parent_id.l10n_cl_dte_email and parent_id.l10n_cl_dte_email != '':
                    values['l10n_cl_dte_email'] = parent_id.l10n_cl_dte_email
                    values['l10n_cl_activity_description'] = parent_id.l10n_cl_activity_description

        return super(ResPartner, self).create(values)

    def check_update_taxpayer_mail(self):
        if not self.l10n_cl_dte_email or not self.l10n_cl_dte_email_update_at or (date.today() - self.l10n_cl_dte_email_update_at).days > 5:
            self.get_taxpayer_mail()

    def get_taxpayer_mail(self):
        if not self.env.user.company_id.dte_get_taxpayer_url:
            raise models.ValidationError('No es posible obtener la url del servicio para actualizar el email de intercambio')
        url = f'{self.env.user.company_id.dte_get_taxpayer_url}?rut={self.vat.strip()}'
        headers = {
            "apiKey": self.env.user.company_id.dte_get_taxpayer_hash,
            "CustomerCode": self.env.user.company_id.dte_get_taxpayer_customer_code
        }
        try:
            r = requests.get(url, headers=headers, verify=False)
            jr = json.loads(r.text)
            if r.status_code == 200:
                self.write({
                    'l10n_cl_dte_email': jr['email'],
                    'l10n_cl_dte_email_update_at': date.today()
                })
            if r.status_code == 404:
                raise models.ValidationError(f'No se ha encontrado información del contribuyente con rut {self.vat}')
            if r.status_code >= 300:
                raise models.ValidationError('Ha ocurrido un problema para obtener la información desde el servicio: ' + r.text)
        except Exception as e:
            raise models.ValidationError(str(e))