from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id,
                                                                description)
        if self._is_out() and not self.picking_id.is_return:
            res.pop(1)
            for line in self.move_line_ids:
                if line.analytic_account:
                    unit_cost = cost / abs(qty)
                    account_id = credit_account_id if self._is_in() else debit_account_id
                    res.append(
                        (0, 0,
                         self.get_data(line.qty_done, description, unit_cost, account_id, line.analytic_account.id)))
        return res

    def get_data(self, qty, description, cost, account_id=False, analytic_account_id=False):
        data = {}
        data['name'] = description
        data['product_id'] = self.product_id.id
        data['quantity'] = qty * -1 if self._is_out() else qty
        data['product_uom_id'] = self.product_uom.id
        data['ref'] = description
        data['partner_id'] = self.picking_id.partner_id.id
        data['debit'] = qty * cost if self._is_out() else 0
        data['credit'] = qty * cost if self._is_in() else 0
        data['account_id'] = account_id
        data['analytic_account_id'] = analytic_account_id
        return data
