from odoo import fields, models, api

class StockMoveLine(models.Model):
  _inherit = 'stock.move.line'

  analytic_account = fields.Many2one('account.analytic.account', string = "Cuenta Analítica")
  product_unit_cost = fields.Float('Costo Unitario')
  product_total_cost = fields.Float('Costo Total')

  def _action_done(self):
    res = super(StockMoveLine, self)._action_done()
    self.write({
        'product_unit_cost': self.product_id.standard_price,
        'product_total_cost': self.product_id.standard_price * self.qty_done
    })
    return res