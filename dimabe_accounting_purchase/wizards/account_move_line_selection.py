from odoo import models, fields, api


class AccountMoveLineSelection(models.TransientModel):
    _name = 'account.move.line.selection'

    selection_line = fields.Boolean('Selección')

    wiz_id = fields.Many2one('wizard.select.account.line')

    line_id = fields.Many2one('account.move.line', string='Apunte Contable')

    purchase_line_id = fields.Many2one('purchase.order.line', string="Linea de OC")

    product_id = fields.Many2one('product.product', string='Producto')

    description = fields.Char('Descripción')

    account_id = fields.Many2one('account.account', string="Cuenta")

    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta analítica")

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Etiquetas analíticas')

    quantity = fields.Float('Cantidad')

    product_uom_id = fields.Many2one('uom.uom')

    price_unit = fields.Float('Precio')

    tax_ids = fields.Many2many('account.tax', string='Impuestos')

    price_subtotal = fields.Float('Subtotal')
