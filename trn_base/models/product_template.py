from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_min_qty_company = fields.Float('Stock Minimo', company_dependent=True)

    stock_diff_qty_company = fields.Float('Diferencia', company_dependent=True)

    state_stock_company = fields.Selection([('under_minimum', 'Bajo stock critico'), ('at_minimum', 'En el minimo'),
                                            ('seek_at_minimum', 'Cercano al minimo'),
                                            ('over_minimum', 'Sobre el minimo'),
                                            ('without_minimum', 'Sin Minimo')], default='without_minimum',
                                           string="Estado del Stock minimo", company_dependent=True)

    order_point_id = fields.Many2one('stock.warehouse.orderpoint', string='Stock Minimo', company_dependent=True)

    def write(self, vals):
        if 'order_point_id' in vals.keys():
            order_point_id = self.env['stock.warehouse.orderpoint'].sudo().search(
                [('id', '=', vals['order_point_id']), ('company_id', '=', self.env.company.id)])
            vals.update(self.set_qty_company(order_point_id))
        return super(ProductTemplate, self).write(vals)

    def set_qty_company(self, order_point):
        stock_company = self.env['stock.quant'].sudo().search(
            [('product_id.product_tmpl_id.id', '=', self.id), ('company_id', '=', self.env.company.id)])
        total_stock = sum(stock.quantity for stock in stock_company)
        diff = total_stock - order_point.product_min_qty
        state_stock = self.get_state_stock(diff)
        return {
            'stock_min_qty_company': order_point.product_min_qty,
            'stock_diff_qty_company': diff,
            'state_stock_company': state_stock
        }

    def get_state_stock(self, diff):
        if diff < 0:
            return 'under_minimum'
        if diff == 0:
            return 'at_minimum'
        if diff > 0:
            return 'over_minimum'

    def set_orderpoint_in_product(self):
        order_point_ids = self.env['stock.warehouse.orderpoint'].sudo().search(
            [('company_id', '=', self.env.company.id)])
        for point in order_point_ids:
            point.product_id.product_tmpl_id.sudo().write({
                'order_point_id': point.id
            })
