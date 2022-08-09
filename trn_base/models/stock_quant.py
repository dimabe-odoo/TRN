from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, vals_list):
        res = super(StockQuant, self).create(vals_list)
        if 'quantity' in vals_list.keys():
            diff = res.product_id.product_tmpl_id.qty_available - res.product_id.product_tmpl_id.stock_min_qty
            res.product_id.product_tmpl_id.write({
                'stock_diff_qty': diff,
                'state_stock': self.get_state_stock(diff)
            })
        return res

    def write(self, vals):
        res = super(StockQuant, self).write(vals)
        for item in self:
            diff = item.product_id.product_tmpl_id.qty_available - item.product_id.product_tmpl_id.stock_min_qty
            item.product_id.product_tmpl_id.write({
                'stock_diff_qty': diff,
                'state_stock': item.get_state_stock(diff)
            })
        return res

    def get_state_stock(self, diff):
        if diff < 0:
            return 'under_minimum'
        if diff == 0:
            return 'at_minimum'
        if diff > 0:
            return 'over_minimum'
