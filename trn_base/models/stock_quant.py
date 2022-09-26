from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    category_id = fields.Many2one('product.category', string='Categoria')

    @api.model
    def create(self, vals_list):
        if 'product_id' in vals_list:
            product = self.env['product.product'].sudo().search([('id', '=', vals_list['product_id'])])
            if product:
                if product.categ_id:
                    vals_list['category_id'] = product.categ_id.id
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
