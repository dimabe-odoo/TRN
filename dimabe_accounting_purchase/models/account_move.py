from odoo import models, fields, api
import re


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_account_line_ids = fields.One2many(
        'account.purchase.line', 'move_id', string="Información OC", )

    purchase_tmp_id = fields.Many2one('purchase.order', string="OC")

    @api.model
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        if res.move_type in ['in_invoice', 'in_refund']:
            res.define_vendor_bill()
        return res

    def define_vendor_bill(self):
        for item in self:
            if len(item.purchase_account_line_ids) > 0:
                item.purchase_account_line_ids.unlink()
            line_oc = self.env['l10n_cl.account.invoice.reference'].sudo().search(
                [('l10n_cl_reference_doc_type_selection', '=', '801'), ('move_id.id', '=', item.id)])
            if line_oc:
                for line in line_oc:
                    oc = line.origin_doc_number if 'P' in line.origin_doc_number \
                        else f'P0{line.origin_doc_number}'
                    oc = oc.replace('O', '0')
                    oc = re.sub(r'[^\w]', ' ', oc).strip()
                    purchase_id = self.env['purchase.order'].sudo().search([
                        ('name', '=', oc)])
                    if purchase_id:
                        # if len(purchase_id.order_line.filtered(
                        #         lambda x: x.display_type not in ['line_section', 'line_note'])) == 1:
                        #     item.invoice_line_ids.write({
                        #         'product_id': purchase_id.order_line.filtered(
                        #             lambda x: x.display_type not in ['line_section', 'line_note'])[0].product_id.id,
                        #         'purchase_line_id': purchase_id.order_line[0].id
                        #     })
                        #     item.write({
                        #         'purchase_tmp_id': purchase_id.id,
                        #     })
                        # if len(purchase_id.order_line) > 1:
                        item.write({
                            'purchase_tmp_id': purchase_id.id,
                        })
                        to_create = []
                        for p_line in purchase_id.order_line.filtered(
                                lambda x: x.display_type not in ['line_section', 'line_note']):
                            unit_price = p_line.price_unit
                            price_subtotal = p_line.price_subtotal
                            if purchase_id.currency_id.id != self.env.company.currency_id.id:
                                date_order = purchase_id.date_order.date()
                                rate = self.env['res.currency.rate'].sudo().search(
                                    [('name', '=', date_order), ('currency_id', '=', purchase_id.currency_id.id)])
                                if rate:
                                    unit_price = purchase_id.currency_id._convert(unit_price, self.env.company.currency_id,
                                                                                  self.env.company, item.date, round=False)
                                    price_subtotal = self.env.company.currency_id.round(
                                        unit_price * p_line.product_uom_qty)
                            to_create.append({
                                'move_id': item.id,
                                'purchase_line_id': p_line.id,
                                'product_id': p_line.product_id.id,
                                'qty': p_line.product_uom_qty,
                                'qty_received': p_line.qty_received,
                                'unit_price': unit_price,
                                'subtotal': price_subtotal,
                                'description': p_line.name,
                            })
                        self.env['account.purchase.line'].sudo().create(
                            to_create)
                        return
