from odoo import api, fields, models

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    user_ids = fields.Many2many('res.users', string='Usuarios')

