from odoo import fields, models
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id,
                                                                description)
        if qty == 0:
            return res
        if self._is_out():
            res.pop(1)
            total = 0
            for line in self.move_line_ids:
                if line.analytic_account:
                    unit_cost = cost / abs(qty)
                    account_id = credit_account_id if self._is_in() else debit_account_id
                    line_data = self.get_data(line.qty_done, description, unit_cost, account_id,
                                              line.analytic_account.id)
                    res.append((0, 0, line_data))
                    total += line_data['debit']
            if res[0][2]['credit'] != total:
                diff = res[0][2]['credit'] - total
                line_diff_cost = self.get_data(1, 'Diferencia', account_id=self.env.company.account_diff_id.id if self.env.company.account_diff_id else debit_account_id,
                                               analytic_account_id=self.env.company.analytic_account_diff_id.id,
                                               diff=diff)
                res.append((0, 0, line_diff_cost))         
        return res

    def get_data(self, qty, description, cost=False, account_id=False, analytic_account_id=False, diff=False):
        data = {}
        data['name'] = description
        data['product_id'] = self.product_id.id
        data['quantity'] = qty * -1 if self._is_out() else qty
        data['product_uom_id'] = self.product_uom.id
        data['ref'] = description
        data['partner_id'] = self.picking_id.partner_id.id
        if cost and not diff:
            data['debit'] = round(qty * cost) if self._is_out() else 0
            data['credit'] = round(qty * cost) if self._is_in() else 0
        if not cost and diff:
            data['debit'] = abs(diff) if diff > 0 else 0
            data['credit'] = abs(diff) if diff < 0 else 0
        data['account_id'] = account_id
        data['analytic_account_id'] = analytic_account_id
        data['currency_id'] = self.env.company.currency_id.id
        return data
