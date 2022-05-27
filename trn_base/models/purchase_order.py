from odoo import fields, models, api
from ..utils.roundformat_clp import round_clp

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def roundclp(self, value):
        return round_clp(value)

    def _get_custom_report_name(self):
        return '%s %s' % ('Órden de Compra - ', self.name)

