from odoo import fields, models, api

class StockMoveLine(models.Model):
  _inherit = 'stock.move.line'
  analytic_account = fields.Many2one('account.analytic.account', string = "Cuenta Analítica")