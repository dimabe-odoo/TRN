from odoo import fields, models, api


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model
    def create(self, vals_list):
        res = super(StockValuationLayer, self).create(vals_list)
        if res.stock_move_id:
            if res.stock_move_id.picking_id:
                if res.stock_move_id.picking_id.delayed_picking:
                    self.env.cr.execute(
                        "UPDATE stock_valuation_layer set create_date = '%s' WHERE id=%s" % (res.stock_move_id.picking_id.date_done, res.id))
        return res