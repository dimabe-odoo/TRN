from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    @api.model
    def create(self, vals_list):
        res = super(StockWarehouseOrderpoint, self).create(vals_list)
        if 'product_min_qty' in vals_list.keys():
            res.product_id.product_tmpl_id.write({
                'stock_min_qty': res.product_min_qty
            })
        return res

    def write(self, vals):
        for item in self:
            if 'product_min_qty' in vals.keys():
                item.product_id.product_tmpl_id.write({
                    'stock_min_qty': vals['product_min_qty']
                })
        return super(StockWarehouseOrderpoint, self).write(vals)
