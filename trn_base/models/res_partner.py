from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_receivable_id = fields.Many2one('account.account', default=None, tracking=True)

    property_account_payable_id = fields.Many2one('account.account', default=None, tracking=True)

    @api.model
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        if res.property_account_receivable_id.deprecated:
            res.property_account_receivable_id = None
        if res.property_account_payable_id.deprecated:
            res.property_account_payable_id = None
        return res
