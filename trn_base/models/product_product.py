from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def write(self, vals):
        if 'categ_id' in vals.keys():
            if self.categ_id.id != vals['categ_id']:
                quant_ids = self.env['stock.quant'].sudo().search([('product_id.id', '=', self.id)])
                line_ids = self.env['stock.move.line'].sudo().search([('product_id.id', '=', self.id)])
                quant_ids.write({
                    'category_id': vals['categ_id']
                })
                line_ids.write({
                    'category_id': vals['categ_id']
                })
        return super(ProductProduct, self).write(vals)
