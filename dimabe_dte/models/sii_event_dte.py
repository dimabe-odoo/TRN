from odoo import api, fields, models


class SiiEventDte(models.Model):
    _name = 'sii.event.dte'
    _rec_name = 'event_description'
    _order = 'event_date'

    event_code = fields.Char(
        string='Codigo Evento',
        required=False)

    event_description = fields.Char(
        string='Descripcion Evento',
        required=False)

    rut_accountable = fields.Char(
        string='Rut Responsable',
        required=False)

    event_date = fields.Datetime(
        string='Fecha del Evento',
        required=False)

    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Factura',
        required=False)

    invoice_name = fields.Char(
        string='Factura (Nombre)',
        required=False)