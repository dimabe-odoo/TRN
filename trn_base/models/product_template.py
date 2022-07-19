from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_min_qty = fields.Float('Stock Minimo', compute='compute_stock_min_qty')

    def compute_stock_min_qty(self):
        for item in self:
            order_point_id = self.env['stock.warehouse.orderpoint'].sudo().search(
                [('product_id.product_tmpl_id.id', '=', item.id)], limit=1)
            if order_point_id:
                item.stock_min_qty = order_point_id.product_min_qty
                return
            item.stock_min_qty = 0
            return
