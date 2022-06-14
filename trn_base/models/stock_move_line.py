from odoo import fields, models, api
from ..utils.lot_generator import generate_lot, get_last_lot


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    analytic_account = fields.Many2one('account.analytic.account', string="Cuenta Analítica")
    product_unit_cost = fields.Float('Costo Unitario')
    product_total_cost = fields.Float('Costo Total')

    def _action_done(self):
        for item in self:
            if item.qty_done == 0:
                print()
            item.write({
                'product_unit_cost': item.product_id.standard_price,
                'product_total_cost': item.product_id.standard_price * item.qty_done
            })
        return super(StockMoveLine, self)._action_done()

    @api.model
    def create(self, vals_list):
        if 'picking_id' in vals_list.keys():
            picking_id = self.env['stock.picking'].sudo().search([('id', '=', vals_list['picking_id'])])
            product_id = self.env['product.product'].sudo().search([('id', '=', vals_list['product_id'])])
            if picking_id.picking_type_id.code == 'incoming' and product_id.tracking == 'lot':
                last_lot_id = get_last_lot()
                if last_lot_id:
                    lot_id = self.env['stock.production.lot'].sudo().create({
                        'name': last_lot_id,
                        'product_id': vals_list['product_id'],
                        'is_auto_lot': True,
                        'company_id': self.env.user.company_id.id,
                    })
                    vals_list['lot_id'] = lot_id.id
                    vals_list['lot_name'] = lot_id.name
        res = super(StockMoveLine, self).create(vals_list)
        return res
