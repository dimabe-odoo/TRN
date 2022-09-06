from odoo import models, api, fields
from ..utils.generate_notification import send_notification
import re
from lxml import etree
import datetime
from py_linq import Enumerable
from ..utils.roundformat_clp import round_clp
from ..utils.roundformat_clp import format_clp
from ..utils.get_remaining_caf import get_remaining_caf
from pdf417 import encode, render_image
import base64
from io import BytesIO
from ..utils.rut_helper import RutHelper

class AccountMove(models.Model):    
    _inherit = 'account.move'

    subtotal_amount = fields.Float('Subtotal', compute="_compute_subtotal_amount")

    net_amount = fields.Float('Total Neto', compute="_compute_net_amount")

    total_exempt = fields.Float('Total Exento', compute="_compute_total_exempt")

    ted = fields.Binary('TED')  

    message_sended_ids = fields.One2many('mail.message', 'invoice_id', 'Mensaje',
                                         domain=[('model', '=', 'account.move'), ('message_type', '=', 'email'), ])

    email_sended_ids = fields.One2many('mail.mail', 'account_invoice_id', 'Envios de correo DTE')

    state_send_email_dte = fields.Selection(
        [('outgoing', 'Saliente'), ('sent', 'Enviado'), ('received', 'Recibido'),
         ('exception', 'Entrega Fallida'), ('cancel', 'Cancelado')],
        'Estado Envío Email DTE', compute="_compute_state_send_email_dte", store=True)

    invoice_event_ids = fields.One2many(
        'sii.event.dte', 'invoice_id',
        string='Eventos del DTE',
        required=False)

    sii_code_response = fields.Char('SII Respuesta Recepcion')

    sii_last_event_dte = fields.Many2one('sii.event.dte', string="Ultimo Evento Registrado desde SII",
                                         compute='compute_last_event')

    l10n_cl_dte_acceptation_status = fields.Selection(
        selection_add=[('factoring', 'Cedido'), ('no_events', 'Sin Eventos')])

    has_return = fields.Boolean('Tiene Retorno')

    reason_id = fields.Many2one(
        comodel_name='custom.reason',
        string='Motivo de Devolucion',
        required=False)

    document_number = fields.Char('Número de Documento')

    is_jump_number = fields.Boolean('Se omitiran folios')

    uf_date = fields.Date('Fecha UF')

    uf_value = fields.Float('Valor UF', digits=[16, 2])

    #Change uf date - value
    @api.onchange('invoice_date')
    def onchange_date(self):
        for item in self:
            if item.move_type == 'out_invoice':
                if item.invoice_date:
                    item.write({
                        'uf_date': item.invoice_date
                    })
                    self.onchange_uf_date()

    @api.onchange('uf_date')
    def onchange_uf_date(self):
        for item in self:
            if item.state == 'draft':
                if item.move_type == 'out_invoice':
                    uf_value = 0
                    if item.uf_date:
                        currency_id = self.env['res.currency'].search([('name', '=', 'UF')])
                        date_rate_id = self.get_currency_rate(currency_id, item.uf_date)
                        if date_rate_id:
                            item.uf_date = date_rate_id.name
                            if date_rate_id:
                                uf_value = 1 / date_rate_id.rate
                        else:
                            uf_value = 0
                    item.write({
                        'uf_value': uf_value
                    })
                    self.custom_update_move_line()

    def custom_update_move_line(self):
        for item in self:
            sum_debit = 0
            for line in item.line_ids.filtered(lambda x: not x.display_type).sorted(key=lambda x: x.debit).sorted(key=lambda x: x.product_id, reverse=True):
                if line.debit > 0:
                    line.price_unit = sum_debit
                    line.debit = sum_debit
                if line.tax_line_id:
                    tax_amount = self.get_custom_tax_amount(line.tax_line_id, item.invoice_line_ids.filtered(lambda x: x.product_id and line.tax_line_id.id in x.tax_ids.ids and not x.display_type))
                    line.price_unit = tax_amount[0]
                    line.credit = tax_amount[0]
                    line.tax_base_amount = tax_amount[1]
                    sum_debit += tax_amount[0]
                if line.currency_origin_id.id == self.env['res.currency'].search([('name', '=', 'UF')]).id:
                    new_price = int(str(round_clp(line.currency_origin_price_unit * item.uf_value).replace('.','')))
                    line.price_unit = new_price
                    line.credit = new_price
                    sum_debit += new_price


    def get_custom_tax_amount(self, tax_line, line_ids):
        tax_base_amount = sum(line.price_unit * line.quantity for line in line_ids)
        price_unit = (tax_base_amount * tax_line.amount) / 100
        return int(round_clp(price_unit).replace('.','')), tax_base_amount


    def get_currency_rate(self, origin_currency_id, uf_date):
        currency_rate = origin_currency_id.rate_ids.filtered(lambda x: x.name == uf_date)

        if not currency_rate:
            self.company_id.custom_run_update_currency(origin_currency_id, uf_date)
            currency_rate = origin_currency_id.rate_ids.filtered(lambda x: x.name == uf_date)

        if not currency_rate:
            currency_rates = origin_currency_id.rate_ids.sorted(lambda x: x.name, reverse=True).filtered(lambda x: x.name <= uf_date)
            if len(currency_rates) > 0:
                currency_rate = currency_rates[0]

        return currency_rate
    #End Change uf date - value

    def roundclp(self, value):
        return round_clp(value)

    def formatufclp(self, value):
        value_split = str(value).split('.')
        str_formated = str(format_clp(int(value_split[0]))) + ',' + value_split[1]
        return str_formated

    def compute_last_event(self):
        for item in self:
            if item.invoice_event_ids:
                item.sii_last_event_dte = item.invoice_event_ids[-1]
            else:
                item.sii_last_event_dte = None

    def _get_custom_report_name(self):
        return '%s %s' % (self.l10n_latam_document_type_id.name, self.l10n_latam_document_number)

    def action_invoice_sent(self):
        res = super(AccountMove, self).action_invoice_sent()
        if not self.ted:
            self.get_ted()
        return res

    @api.model
    def _compute_subtotal_amount(self):
        for item in self:
            subtotal_amount = 0
            for line in item.invoice_line_ids:
                subtotal_amount += line.price_unit * line.quantity
            item.subtotal_amount = subtotal_amount

    @api.model
    def _compute_net_amount(self):
        for item in self:
            net_amount = 0
            for line in item.invoice_line_ids:
                net_amount += line.price_unit * line.quantity * ((100 - line.discount) / 100)
            item.net_amount = net_amount

    @api.model
    def _compute_total_exempt(self):
        for item in self:
            total_exempt = 0
            for line in item.invoice_line_ids:
                if len(line.tax_ids) == 0:
                    total_exempt += line.price_unit * line.quantity * ((100 - line.discount) / 100)
            item.total_exempt = total_exempt

    @api.depends('name')
    def _compute_l10n_latam_document_number(self):
        for item in self:
            if not item.is_jump_number:
                super(AccountMove, item)._compute_l10n_latam_document_number()
            else:
                item.l10n_latam_document_number = item.document_number
                item.name = f'{item.l10n_latam_document_type_id.doc_code_prefix} {item.document_number}'

    def get_ted(self):
        cols = 12
        while True:
            try:
                if cols == 31:
                    break
                codes = encode(self.l10n_cl_sii_barcode, cols)
                image = render_image(codes, scale=5, ratio=2)
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue())
                return img_str
            except:
                cols += 1

    def custom_report_fix(self, list_report_list):
        report_linq = Enumerable(list_report_list)
        report_ids = report_linq.select(lambda x: x['id'])
        report = self.env['ir.actions.report'].search([('id', 'in', report_ids.to_list())])

        for rep in report:
            report_to_update = report_linq.first_or_default(lambda x: x['id'] == rep.id)
            if report_to_update:
                new_name = report_to_update['new_name'] if 'new_name' in report_to_update.keys() else rep.name
                new_template_name = report_to_update[
                    'template_new'] if 'template_new' in report_to_update.keys() else rep.report_name
                paperformat_id = report_to_update[
                    'paperformat_id'] if 'paperformat_id' in report_to_update.keys() else rep.paperformat_id
                print_report_name = report_to_update[
                    'print_report_name'] if 'print_report_name' in report_to_update.keys() else rep.print_report_name

                if rep.report_name != new_template_name or rep.report_file != new_template_name or rep.name != new_name or rep.paperformat_id != paperformat_id or rep.print_report_name != print_report_name:
                    rep.write({
                        'report_name': new_template_name,
                        'report_file': new_template_name,
                        'name': new_name,
                        'paperformat_id': paperformat_id,
                        'print_report_name': print_report_name
                    })
                else:
                    continue
            else:
                continue

    def action_post(self):
        if self.move_type == 'in_invoice':
            if not self.ted:
                self.get_client_ted()
        res = super(AccountMove, self).action_post()
        return res

    def button_verify_claim_dte_events(self):
        response = self._get_dte_claim(
            self.company_id.l10n_cl_dte_service_provider,
            self.company_id.vat,
            self.company_id._get_digital_signature(),
            self.l10n_latam_document_type_id.code,
            self.l10n_latam_document_number
        )
        if response:
            self.write({
                'sii_code_response': response['codResp']
            })
            if len(response['listaEventosDoc']) > 0:
                if any(event.event_code == '16' for event in self.invoice_event_ids):
                    self.invoice_event_ids.filtered(lambda x: x.event_code == '16').unlink()
                for event in response['listaEventosDoc']:
                    t_date = datetime.datetime.strptime(event['fechaEvento'], "%d-%m-%Y %H:%M:%S").strftime(
                        '%Y-%m-%d %H:%M:%S')
                    event_code = self.env['sii.event.dte'].search(
                        [('event_code', '=', event['codEvento']), ('invoice_id', '=', self.id)])
                    if event_code:
                        continue
                    self.env['sii.event.dte'].create({
                        'invoice_id': self.id,
                        'event_code': event['codEvento'],
                        'event_description': event['descEvento'],
                        'rut_accountable': f'{event["rutResponsable"]}-{event["dvResponsable"]}',
                        'event_date': t_date,
                        'invoice_name': self.name,
                    })
            else:
                self.write({
                    'l10n_cl_dte_acceptation_status': 'no_events'
                })
                event_code = self.env['sii.event.dte'].search(
                    [('event_code', '=', response['codResp']), ('invoice_id', '=', self.id)])
                if event_code:
                    return
                self.env['sii.event.dte'].create({
                    'invoice_id': self.id,
                    'event_code': f'{response["codResp"]}',
                    'event_description': response['descResp'],
                    'event_date': datetime.datetime.now(),
                    'invoice_name': self.name
                })
        days = datetime.date.today() - self.invoice_date
        try:
            if any(event.event_code in ('RCD', 'RFP', 'RFT') or event.event_code == 'NCA' for event in
                   self.invoice_event_ids):
                self.write({
                    'l10n_cl_dte_acceptation_status': 'claimed'
                })
                send_notification('DTE Reclamado', self.generate_message_claimed(), 2,
                                  self.env.ref('dimabe_dte.custom_noti_claimed_dte').user_ids, 'account.move', self.id)
                return
            elif any(event.event_code == 'CED' for event in self.invoice_event_ids):
                self.write({
                    'l10n_cl_dte_acceptation_status': 'factoring'
                })
            elif any(event.event_code in ('ACD', 'ERM') for event in
                     self.invoice_event_ids):
                self.write({
                    'l10n_cl_dte_acceptation_status': 'accepted'
                })
            elif days.days > self.env.user.company_id.days_acceptation and self.l10n_cl_dte_acceptation_status not in (
                    'claimed', 'accepted',
                    'factoring') or days.days > self.env.user.company_id.days_acceptation:
                self.write({
                    'l10n_cl_dte_acceptation_status': 'accepted'
                })
        except Exception as error:
            print(error)


    def generate_message_claimed(self):
        message = f'<p>Estimados. <br/> Le Informamos que el DTE {self.name} ha sido reclamado por la siguientes causas: <br/>'
        for item in self.invoice_event_ids:
            message += f'<p> {item.event_description} , el que el responsable cuenta con el siguiente RUT {item.rut_accountable}'
        return message

    def get_claim_dte_events(self):
        invoices = self.env['account.move'].search(
            [('l10n_cl_dte_status', 'in', ('accepted', 'objected')), ('move_type', '=', 'out_invoice'),
             ('l10n_latam_document_type_id.code', '!=', '39')])
        for inv in invoices:
            diff = datetime.date.today() - inv.date
            if diff.days <= 8:
                inv.button_verify_claim_dte_events()
            else:
                continue

    def write(self, values):
        for item in self:
            if 'l10n_cl_dte_status' in values.keys():
                if values['l10n_cl_dte_status'] in ['accepted', 'objected']:
                    get_remaining_caf(item.l10n_latam_document_type_id.id)
            if item.l10n_cl_sii_barcode:
                values['ted'] = item.get_ted()
            res = super(AccountMove, item).write(values)
            return res

    def _l10n_cl_send_dte_to_partner(self):
        res = super(AccountMove, self)._l10n_cl_send_dte_to_partner()
        for item in self:
            item.define_mail()
        return res

    def l10n_cl_verify_dte_status(self):
        self.partner_id.get_taxpayer_mail()
        res = super(AccountMove, self).l10n_cl_verify_dte_status()
        return res

    def _l10n_cl_edi_post_validation(self):
        self.partner_id.check_update_taxpayer_mail()
        res = super(AccountMove, self)._l10n_cl_edi_post_validation()
        return res

    def get_message(self, type):
        if type == 'received':
            return f"<p>Estimados.<br/><br/> Le informamos que el DTE {self.name} ha sido recibido por el cliente"
        elif type == 'ack_sent':
            return f"<p>Estimados.<br/><br/> Le informamos que el cliente acusa recibo del DTE {self.name}"
        elif type == 'claimed':
            return f"<p>Estimados.<br/><br/> Le informamos que el cliente informa reclamo del DTE {self.name}"
        elif type == 'accepted':
            return f"<p>Estimados.<br/><br/> Le informamos que el DTE {self.name} fue Aceptado por el cliente"

    def get_client_ted(self):
    
        doc_id = self.env['ir.attachment'].search(
            [('res_model', '=', 'fetchmail.server'), ('res_id', '=', self.id), ('name', 'like', 'DTE')],
            order='create_date desc')
        if doc_id:
            doc_xml = base64.b64decode(doc_id[0].datas).decode('utf-8')
            ted_str = doc_xml[doc_xml.find('<TED ') - 1:doc_xml.find('</TED>') + 6]
            ted_str_clean = etree.tostring(
                etree.fromstring(re.sub(r'<TmstFirma>.*</TmstFirma>', '', ted_str.replace('&', '&amp;')),
                                 parser=etree.XMLParser(remove_blank_text=True)))
            self.l10n_cl_sii_barcode = ted_str_clean

    @api.depends('message_sended_ids', 'email_sended_ids')
    def _compute_state_send_email_dte(self):
        for item in self:
            item.state_send_email_dte = None
            if item.email_sended_ids:
                if len(item.email_sended_ids) > 0:
                    item.state_send_email_dte = item.email_sended_ids[0].state

    def define_mail(self):
        for item in self:
            messages = self.env['mail.message'].sudo().search([('res_id', '=', item.id)])
            for message in messages:
                if message.message_type == 'email':
                    message.write({
                        'invoice_id': item.id
                    })
                mail_id = self.env['mail.mail'].search(
                    [('mail_message_id', '=', message.id), ('invoice_id', '!=', False)])
                mail_id.write({
                    'account_invoice_id': item.id
                })

    def get_format_rut(self, vat):
        rut = RutHelper.format_rut_dotted(vat)
        return rut

    def update_cl_reference(self):
        order_ids = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
        for order in order_ids:
            sale_reference_id = self.env['l10n_cl.account.invoice.reference'].search([('origin_doc_number','=',order.name), ('l10n_cl_reference_doc_type_selection', '=', '802'), ('date','=', order.date_order), ('move_id','=',self.id)])
            if not sale_reference_id:
                self.env['l10n_cl.account.invoice.reference'].create({
                    'origin_doc_number': order.name,
                    'l10n_cl_reference_doc_type_selection': '802',
                    'date': order.date_order,
                    'move_id': self.id
                })
            for reference in order.custom_file_ids:
                reference_id = self.env['l10n_cl.account.invoice.reference'].search([('origin_doc_number','=',reference.name), ('l10n_cl_reference_doc_type_selection', '=', reference.file_type), ('date','=', reference.file_date), ('move_id','=',self.id)])
                if not reference_id:
                    self.env['l10n_cl.account.invoice.reference'].create({
                        'origin_doc_number': reference.name,
                        'l10n_cl_reference_doc_type_selection': reference.file_type,
                        'date': reference.file_date,
                        'move_id': self.id
                    })

    @api.model
    def create(self, values):
        res = super(AccountMove, self).create(values)
        if 'invoice_origin' in values.keys():
            sale_order = False
            if values['invoice_origin']:
                sale_order = self.env['sale.order'].search([('name', '=', values['invoice_origin'])])
            if sale_order:
                self.env['l10n_cl.account.invoice.reference'].create({
                    'date': sale_order.date_order,
                    'origin_doc_number': sale_order.name,
                    'l10n_cl_reference_doc_type_selection': '802',
                    'move_id': res.id
                })
                for reference in sale_order.custom_file_ids:
                    self.env['l10n_cl.account.invoice.reference'].create({
                        'date': reference.file_date,
                        'origin_doc_number': reference.name,
                        'l10n_cl_reference_doc_type_selection': reference.file_type,
                        'move_id': res.id
                    })
        return res  


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    taxes_amount = fields.Float('Monto Impuesto', compute="_compute_taxes_amount")

    price_unit_with_discount = fields.Float('Precio Unit. con Descuento', compute="_compute_price_unit_with_discount")

    subtotal_with_taxes = fields.Float('Subtotal con Impuesto', compute="_compute_subtotal_with_taxes")

    price_total_signed = fields.Float('Precio Total con Signo', compute="_compute_price_total_signed")

    price_total_without_taxes_signed = fields.Float('Precio Total sin Impuesto con Signo', compute="_compute_price_total_signed") 


    @api.model
    def _compute_price_unit_with_discount(self):
        for item in self:
            item.price_unit_with_discount = item.price_unit - (item.price_unit * item.discount / 100)

    @api.model
    def _compute_taxes_amount(self):
        for item in self:
            taxes_amount = 0
            for tax in item.tax_ids:
                taxes_amount += item.price_unit_with_discount * tax.amount / 100

            item.taxes_amount = taxes_amount

    @api.model
    def _compute_subtotal_with_taxes(self):
        for item in self:
            item.subtotal_with_taxes = item.price_subtotal + (item.taxes_amount * item.quantity)

    def _compute_price_total_signed(self):
        for item in self:
            item.price_total_signed = item.price_total
            item.price_total_without_taxes_signed = item.price_subtotal
            if item.move_id.move_type in ['out_refund','in_refund']:
                item.price_total_signed = item.price_total * -1
                item.price_total_without_taxes_signed = item.price_subtotal * -1



class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    is_jump_number = fields.Boolean('Se omitiran folios')

    document_number = fields.Char('Número de Documento')

    document_type_id = fields.Many2one('l10n_latam.document.type', "Tipo de Documento",domain=[('code','in',['61','56'])])

    def _inverse_document_type(self):
        self._clean_pipe()
        self.l10n_latam_document_number = None

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({
            'is_jump_number' : self.is_jump_number,
            'document_number': self.document_number,
            'l10n_latam_document_type_id': self.l10n_latam_document_type_id.id if not self.document_type_id else self.document_type_id.id,
            'l10n_latam_document_number': self.l10n_latam_document_number,
        })
        return res

    @api.onchange('l10n_latam_document_number', 'l10n_latam_document_type_id')
    def _onchange_l10n_latam_document_number(self):
        if not self.document_type_id:
            if self.l10n_latam_document_type_id:
                l10n_latam_document_number = self.l10n_latam_document_type_id._format_document_number(
                    self.l10n_latam_document_number)
                if self.l10n_latam_document_number != l10n_latam_document_number:
                    self.l10n_latam_document_number = l10n_latam_document_number
