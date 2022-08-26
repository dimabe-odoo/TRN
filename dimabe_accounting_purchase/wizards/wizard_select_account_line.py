from odoo import fields, models, api


class WizardSelectAccountLine(models.TransientModel):
    _name = 'wizard.select.account.line'

    purchase_account_line_id = fields.Many2one('account.purchase.line', string="Información OC")

    account_move_line_ids = fields.One2many('account.move.line.selection', 'wiz_id', string="Linea Factura")

    message = fields.Text('Mensaje', compute='compute_message')

    def compute_message(self):
        for item in self:
            message = f'No existe un apunte que coincida con el producto' \
                      f' {self.purchase_account_line_id.product_id.display_name} ' \
                      f'de la OC {self.purchase_account_line_id.purchase_line_id.order_id.name} \n'
            message += f'Se debe seleccionar una apunte de la factura {self.purchase_account_line_id.move_id.name} \n'
            item.message = message

    def associate_selection(self):
        for item in self:
            for line in item.account_move_line_ids.filtered(lambda x: x.selection_line):
                line.line_id.sudo().write({
                    'product_id': item.purchase_account_line_id.product_id.id,
                    'purchase_line_id': line.purchase_line_id.id
                })
                item.purchase_account_line_id.write({
                    'line_id': line.line_id.id,
                    'state': 'linked',
                })
