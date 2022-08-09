from odoo import models, fields, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    is_auto_lot = fields.Boolean('Es un lote generado', default=False)


