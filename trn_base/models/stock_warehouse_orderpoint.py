from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    @api.model
    def create(self, vals_list):
        res = super(StockWarehouseOrderpoint, self).create(vals_list)
        if not res.product_id.product_tmpl_id.orderpoint_id:
            res.product_id.product_tmpl_id.write({
                'orderpoint_id': res.id
            })
        return res

    def write(self, vals):
        return super(StockWarehouseOrderpoint, self).write(vals)

    def get_state_stock(self, diff):
        if diff < 0:
            return 'under_minimum'
        if diff == 0:
            return 'at_minimum'
        if diff > 0:
            return 'over_minimum'
