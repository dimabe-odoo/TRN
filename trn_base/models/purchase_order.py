from venv import create
from odoo import fields, models, api
from ..utils.roundformat_clp import round_clp, format_usd, format_qty

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def roundclp(self, value):
        return round_clp(value)

    def format_usd(self, value):
        return format_usd(value)

    def format_qty(self, qty):
        return format_qty(qty)

    def _get_custom_report_name(self):
        return '%s %s' % ('Órden de Compra - ', self.name)
    
    @api.model
    def create(self, values):
        values['notes'] = 'Estimado proveedor, favor realizar el envío de facturas al correo: facturacion@trn.cl'
        res = super(PurchaseOrder, self).create(values)
        return res

