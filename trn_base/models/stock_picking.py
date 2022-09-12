from odoo import models, fields, api
from ..utils.date_utils_format import get_date_spanish
import xlsxwriter

import pandas as pd


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean('Es Devolución', compute='compute_is_return')

    @api.depends('location_id', 'location_dest_id')
    def compute_is_return(self):
        for item in self:
            if item.picking_type_code == 'incoming':
                item.is_return = item.location_id and item.location_id.usage == 'customer'
                return
            if item.picking_type_code == 'outgoing':
                item.is_return = item.location_dest_id and item.location_dest_id.usage == 'supplier'
                return
            item.is_return = False