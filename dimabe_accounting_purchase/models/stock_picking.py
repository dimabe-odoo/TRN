from odoo import api, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for line in self.move_ids_without_package:
            account_purchase_line = self.env['account.purchase.line'].search([('purchase_line_id', '=', line.purchase_line_id.id)])
            if account_purchase_line:
                account_purchase_line.qty_received = line.purchase_line_id.qty_received
        return res
