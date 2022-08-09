from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    analytic_account_diff_id = fields.Many2one('account.analytic.account',
                                                            string="Cuenta analítica de Diferencia en Valorización")

    account_diff_id = fields.Many2one('account.account', string="Cuenta de diferencia de valorización")