from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_custom_report_name(self):
        return '%s %s' % ('Órden de Compra - ', self.name)
