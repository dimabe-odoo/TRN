from odoo import models, fields, api


class MailMessage(models.Model):
    _inherit = 'mail.message'

    invoice_id = fields.Many2one('account.move')

    def define_mail(self):
        for item in self:
            item.invoice_id = None
            if item.model == 'account.move' and item.message_type == 'email':
                invoice_id = self.env['account.move'].search([('id', '=', item.res_id)])
                item.write({
                    'invoice_id': invoice_id.id
                })
