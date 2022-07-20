from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    @api.model
    def create(self, vals_list):
        res = super(StockWarehouseOrderpoint, self).create(vals_list)
        if 'product_min_qty' in vals_list.keys():
            diff = res.product_id.product_tmpl_id.qty_available - res.product_min_qty
            res.product_id.product_tmpl_id.write({
                'stock_min_qty': res.product_min_qty,
                'stock_diff_qty': diff,
                'state_stock': self.get_state_stock(diff)
            })
        return res

    def write(self, vals):
        for item in self:
            if 'product_min_qty' in vals.keys():
                diff = item.product_id.product_tmpl_id.qty_available - vals['product_min_qty']
                item.product_id.product_tmpl_id.write({
                    'stock_min_qty': vals['product_min_qty'],
                    'stock_diff_qty': diff,
                    'state_stock': self.get_state_stock(diff)
                })
        return super(StockWarehouseOrderpoint, self).write(vals)

    def get_state_stock(self, diff):
        if diff < 0:
            return 'under_minimum'
        if diff == 0:
            return 'at_minimum'
        if diff > 0:
            return 'over_minimum'
