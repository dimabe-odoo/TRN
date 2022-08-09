from odoo import fields, models, api
import xlsxwriter


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    unit_amount = fields.Float('Valor Unitario', compute='compute_unit_amount')

    def compute_unit_amount(self):
        for item in self:
            if item.quantity > 0 and item.analytic_account_id:
                item.unit_amount = item.credit / abs(item.quantity)
                return
            if item.quantity < 0 and item.analytic_account_id:
                item.unit_amount = item.debit / abs(item.quantity)
                return
            item.unit_amount = 0


