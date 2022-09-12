from odoo import models, fields

class MailMail(models.Model):
    
    _inherit = 'mail.mail'
    
    account_invoice_id = fields.Many2one('account.move')

    def define_account_invoice_id(self):
        for item in self:
            item.account_invoice_id = None
            if item.model == 'account.move':
                message_id = self.env['mail.message'].search([('id','=',item.mail_message_id.id), ('invoice_id' ,'!=',False)])
                item.write({
                    'account_invoice_id': message_id.invoice_id.id
                })