from odoo import models, api, fields


class l10n_latam_document_type(models.Model):
    _inherit = 'l10n_latam.document.type'

    last_caf_available = fields.Integer('Último Folio Cargado', compute="_compute_last_caf_available")

    last_caf_consumed = fields.Integer('Último Folio Consumido', compute="_compute_last_caf_consumed")

    remaining_caf = fields.Integer('Folios Disponibles', compute="_compute_remaining_caf")

    cafs_not_loaded = fields.Integer('Folios No Consecutivos', compute="_compute_cafs_not_loaded")

    first_caf_loaded = fields.Integer('Primer Folio Cargado', compute="_compute_first_caf_loaded")

    def _compute_last_caf_available(self):
        for item in self:
            if item.active:
                caf_ids = self.env['l10n_cl.dte.caf'].search(
                    [('l10n_latam_document_type_id.id', '=', item.id), ('status', '=', 'in_use')])
                item.last_caf_available = 0
                if caf_ids:
                    for caf in caf_ids:
                        if caf.final_nb > item.last_caf_available:
                            item.last_caf_available = caf.final_nb
            else:
                item.last_caf_available = 0

    def _compute_last_caf_consumed(self):
        for item in self:
            item.last_caf_consumed = 0
            if item.active:
                if item.code == '52':
                    documents = self.env['stock.picking'].search([('l10n_latam_document_type_id.id', '=', item.id),
                                                                  ('picking_type_id.sequence_code', '=', 'OUT')])
                elif item.code == '61':
                    documents = self.env['account.move'].search(
                        [('l10n_latam_document_type_id.id', '=', item.id), ('move_type', '=', 'out_refund')])
                else:
                    documents = self.env['account.move'].search(
                        [('l10n_latam_document_type_id.id', '=', item.id), ('move_type', '=', 'out_invoice')])

                if documents:
                    for document in documents:
                        if document.l10n_latam_document_number and int(
                                document.l10n_latam_document_number) > item.last_caf_consumed:
                            item.last_caf_consumed = int(document.l10n_latam_document_number)

            else:
                item.last_caf_consumed = 0

    def _compute_remaining_caf(self):
        for item in self:
            if item.active:
                if item.first_caf_loaded == 1:
                    item.remaining_caf = item.last_caf_available - item.last_caf_consumed - item.cafs_not_loaded
                else:
                    if item.last_caf_consumed > 0:
                        item.remaining_caf = item.last_caf_available - item.last_caf_consumed
                    else:
                        if item.last_caf_available > 0:
                            item.remaining_caf = item.last_caf_available - item.first_caf_loaded + 1
                        else:
                            item.remaining_caf = 0
            else:
                item.remaining_caf = 0

    def _compute_cafs_not_loaded(self):
        for item in self:
            caf_ids = self.env['l10n_cl.dte.caf'].search(
                [('l10n_latam_document_type_id.id', '=', item.id), ('status', '=', 'in_use')])
            if caf_ids:
                cafs_loaded = 0
                for caf in caf_ids:
                    cafs_loaded += caf.final_nb - caf.start_nb + 1
                    item.cafs_not_loaded = item.last_caf_available - cafs_loaded
            else:
                item.cafs_not_loaded = 0

    def _compute_first_caf_loaded(self):
        for item in self:
            caf_ids = self.env['l10n_cl.dte.caf'].search(
                [('l10n_latam_document_type_id.id', '=', item.id), ('status', '=', 'in_use')])

            if caf_ids:
                first_caf_loaded = caf_ids[0].start_nb if caf_ids[0].start_nb else 0
                for caf in caf_ids:
                    if caf.start_nb < first_caf_loaded:
                        first_caf_loaded = caf.start_nb

                item.first_caf_loaded = first_caf_loaded
            else:
                item.first_caf_loaded = 0


    # def _is_doc_type_ticket(self):
    #     return True
