from odoo import models, fields, api
from ..utils.date_utils_format import get_date_spanish
import xlsxwriter
from datetime import datetime
import pandas as pd


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean('Es Devolución', compute='compute_is_return')

    picking_return_id = fields.Many2one('stock.picking')

    date_done = fields.Datetime(readonly=False)

    delayed_picking = fields.Boolean('Operacion en diferido',
                                     help="Habilitar ingreso manual para fecha efectiva de la operación")

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
        # for move in self.move_ids_without_package:
        #     account_move_id = self.env['account.move'].search([('stock_move_id', '=', move.id)])
        #     if account_move_id.state == 'draft':
        #         account_move_id.action_post()
        return res

    def write(self, vals):
        return super(StockPicking, self).write(vals)

    def _action_done(self):
        if self:
            for item in self:
                if item.delayed_picking:
                    if item.date_done > datetime.now():
                        raise models.UserError('No puede realizar una operacion a una fecha posterior a la actual.')
                    date_done = item.date_done
        res = super(StockPicking, self)._action_done()
        if self:
            for item in self:
                if item.delayed_picking:
                    item.write({
                        'date_done': date_done
                    })
        return res

    def generate_layer_move(self):
        picking_ids = self.env['stock.picking'].sudo().search([('picking_type_id.id', '=', 34), ('state', '=', 'done')])
        for picking in picking_ids:
            move_ids = picking.move_ids_without_package
            for move in move_ids:
                standard_price = 0
                layer_ids = self.env['stock.valuation.layer'].sudo().search(
                    [('product_id.id', '=', product_id), ('company_id.id', '=', company_id), ('remaining_qty', '>', 0)],
                    order='create_date asc')
                for layer in layer_ids:
                    if layer.create_date < search_date:
                        standard_price = layer.unit_cost
                        break
                total_move = self.env.company.currency_id.round(standard_price * move.quantity_done) * -1
                to_create_layer = {
                    'product_id': move.product_id.id,
                    'stock_move_id': move.id,
                    'quantity': move.quantity_done * -1,
                    'unit_cost': standard_price,
                    'value': total_move if standard_price > 0 else 0,
                    'description': f'{picking.name} - {move.product_id.name}',
                    'company_id': self.env.company.id,
                }
                print(to_create_layer)
                layer = self.env['stock.valuation.layer'].sudo().create(to_create_layer)
                move_id = self.env['account.move'].sudo().create({
                    'journal_id': move.product_id.categ_id.property_stock_journal.id,
                    'date': picking.date_done.date(),
                    'ref': f'{picking.name} - {move.product_id.name}',
                    'move_type': 'entry',
                    'company_id': self.env.company.id
                })
                line_ids = []
                credit_line = {
                    'account_id': move.product_id.categ_id.property_stock_valuation_account_id.id,
                    'name': f'{picking.name} - {move.product_id.name}',
                    'credit': abs(total_move),
                    'debit': 0,
                    'move_id': move_id.id,
                    'product_id': move.product_id.id,
                }
                line_ids.append(credit_line)
                for line in move.move_line_ids:
                    total = self.env.company.currency_id.round(standard_price * line.qty_done)
                    debit_line = {
                        'account_id': move.product_id.categ_id.property_stock_account_output_categ_id.id,
                        'name': f'{picking.name} - {move.product_id.name}',
                        'analytic_account_id': line.analytic_account.id,
                        'debit': total,
                        'credit': 0,
                        'move_id': move_id.id,
                        'product_id': move.product_id.id,
                    }
                    line_ids.append(debit_line)
                total_debit = sum(deb['debit'] for deb in line_ids)
                diff = abs(total_move) - total_debit
                if diff != 0:
                    account_id = self.env.account_diff_id.id if self.env.account_diff_id else layer.product_id.categ_id.property_stock_account_output_categ_id.id
                    diff_line = {
                        'account_id': account_id,
                        'name': 'Diferencia',
                        'debit': abs(diff) if diff > 0 else 0,
                        'credit': abs(diff) if diff < 0 else 0,
                        'move_id': move_id.id,
                        'product_id': layer.product_id.id,
                    }
                    line_ids.append(diff_line)
                self.env['account.move.line'].sudo().create(line_ids)
                move_id.action_post()
                layer.write({
                    'account_move_id': move_id.id
                })

    def get_price(self, product_id, company_id, search_date):
        layer_ids = self.env['stock.valuation.layer'].sudo().search(
            [('product_id.id', '=', product_id), ('company_id.id', '=', company_id), ('remaining_qty', '>', 0)],
            order='create_date asc')
        for layer in layer_ids:
            if layer.create_date < search_date:
                return layer.unit_cost
