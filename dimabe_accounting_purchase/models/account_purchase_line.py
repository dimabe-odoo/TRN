from odoo import fields, models, api


class AccountPurchaseLine(models.Model):
    _name = 'account.purchase.line'

    move_id = fields.Many2one('account.move', string='Factura')

    purchase_line_id = fields.Many2one('purchase.order.line', string='Orden de Compra')

    product_id = fields.Many2one('product.product', string='Producto')

    qty = fields.Float('Cantidad')

    qty_received = fields.Float('Cantidad Recibida')

    unit_price = fields.Float('Costo Unitario')

    subtotal = fields.Float('Subtotal')

    line_id = fields.Many2one('account.move.line', string="Apunte Contable")

    line_qty = fields.Float('Cantidad Facturada', compute='compute_line')

    line_price_unit = fields.Float('Precio Unitario Factura', compute='compute_line')

    description = fields.Char('Descripción')

    state = fields.Selection(selection=[('draft', 'Borrador'), ('linked', 'Enlazado')], default='draft',
                             string='Estado')

    def compute_line(self):
        for item in self:
            item.line_qty = item.purchase_line_id.qty_invoiced
            if item.line_id:
                item.line_price_unit = item.line_id.price_unit
                return
            item.line_price_unit = 0

    def associate_line(self):
        wiz_id = self.env['wizard.select.account.line'].sudo().create({
            'purchase_account_line_id': self.id,
        })
        for line in self.move_id.invoice_line_ids:
            self.env['account.move.line.selection'].sudo().create({
                'wiz_id': wiz_id.id,
                'product_id': line.product_id.id,
                'description': line.name,
                'account_id': line.account_id.id,
                'analytic_account_id': line.analytic_account_id.id,
                'analytic_tag_ids': [(4, tag.id) for tag in line.analytic_tag_ids],
                'quantity': line.quantity,
                'product_uom_id': line.product_uom_id.id,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'purchase_line_id': self.purchase_line_id.id,
                'line_id': line.id
            })
        view_id = self.env.ref('dimabe_accounting_purchase.wizard_select_account_line_form')
        return {
            'name': "Asociación de Apunte Contable",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.select.account.line',
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'res_id': wiz_id.id,
            'context': self.env.context
        }

    def unlink_line(self):
        for item in self:
            to_modify_line = {'purchase_line_id': None}
            if item.line_id.product_id:
                to_modify_line['product_id'] = None
            item.line_id.write(to_modify_line)
            item.write({
                'line_id': None,
                'state': 'draft',
            })
