from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def l10n_cl_confirm_draft_delivery_guide(self):
        res = super(StockPicking, self).l10n_cl_confirm_draft_delivery_guide()
        if self.l10n_latam_document_number:
            reference_id = self.sale_id.mapped('custom_file_ids').filtered(lambda x: x.name == self.l10n_latam_document_number and x.file_date == self.date_done and x.file_type == '52')
            if not reference_id:
                self.env['custom.sale.order.file'].create({
                    'name': self.l10n_latam_document_number,
                    'file_type': '52',
                    'file_date': self.date_done,
                    'sale_id': self.sale_id.id
                })

            for invoice_id in self.sale_id.mapped('invoice_ids'):
                if invoice_id.state == 'draft':
                    invoice_id.update_cl_reference()
                        
        return res

