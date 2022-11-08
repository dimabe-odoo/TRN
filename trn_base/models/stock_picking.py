from odoo import models, fields, api
from ..utils.date_utils_format import get_date_spanish
import xlsxwriter

import pandas as pd


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean('Es Devolución', compute='compute_is_return')

    picking_return_id = fields.Many2one('stock.picking')

    @api.depends('location_id', 'location_dest_id')
    def compute_is_return(self):
        for item in self:
            if item.picking_type_code == 'incoming':
                item.is_return = item.location_id and item.location_id.usage == 'customer'
                return
            # if item.picking_type_code == 'outgoing':
            #     # item.is_return = item.location_dest_id and item.location_dest_id.usage == 'supplier'
            #     # return
            item.is_return = False

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for move in self.move_ids_without_package:
            account_move_id = self.env['account.move'].search([('stock_move_id', '=', move.id)])
            if account_move_id.state == 'draft':
                account_move_id.action_post()
        return res

