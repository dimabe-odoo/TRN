from odoo import fields, models, api

class StockMoveLine(models.Model):
  _inherit = 'stock.move.line'

  analytic_account = fields.Many2one('account.analytic.account', string = "Cuenta Analítica")
  product_unit_cost = fields.Float('Costo Unitario')
  product_total_cost = fields.Float('Costo Total')

  def _action_done(self):
    for item in self:
      item.write({
          'product_unit_cost': item.product_id.standard_price,
          'product_total_cost': item.product_id.standard_price * item.qty_done
      })
    return super(StockMoveLine, self)._action_done()