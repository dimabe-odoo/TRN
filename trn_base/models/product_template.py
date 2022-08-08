from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_min_qty = fields.Float('Stock Minimo')

    stock_diff_qty = fields.Float('Diferencia')

    state_stock = fields.Selection([('under_minimum', 'Bajo stock critico'), ('at_minimum', 'En el minimo'),
                                    ('seek_at_minimum', 'Cercano al minimo'), ('over_minimum', 'Sobre el minimo'),
                                    ('without_minimum', 'Sin Minimo')], default='without_minimum',
                                   string="Estado del Stock minimo")
