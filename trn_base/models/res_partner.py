from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_receivable_id = fields.Many2one('account.account', default=None, tracking=True)

    property_account_payable_id = fields.Many2one('account.account', default=None, tracking=True)
