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

    delayed_picking = fields.Boolean('Operacion en diferido', copy=False,
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

    ## TODO Eliminar este codigo luego de la correcion

    def for_action_fix(self):
        product_ids = self.env['product.product'].sudo().search([('type', '=', 'product')])
        for product in product_ids:
            if product.standard_price > 0 and product.categ_id.property_valuation == 'real_time':
                layer_ids = self.env['stock.valuation.layer'].sudo().search(
                    [('product_id.id', '=', product.id), ('company_id.id', '=', self.env.company.id)])
                if len(layer_ids) > 0:
                    for layer in layer_ids:
                        try:
                            if layer.quantity < 0:
                                quantity_taken = abs(layer.quantity)
                                fifo_value = product._run_fifo(quantity_taken, layer.company_id)
                                layer.write({
                                    'unit_cost': fifo_value['unit_cost'],
                                    'value': fifo_value['value']
                                })
                            if layer.quantity > 0 and layer.stock_move_id.origin_returned_move_id:
                                origin_move_id = layer.stock_move_id.origin_returned_move_id
                                if len(origin_move_id.stock_valuation_layer_ids.filtered(lambda x: x.unit_cost > 0)):
                                    unit_cost = \
                                        origin_move_id.stock_valuation_layer_ids.filtered(lambda x: x.unit_cost > 0)[
                                            0].unit_cost
                                    layer.write({
                                        'unit_cost': unit_cost,
                                        'value': unit_cost * layer.quantity,
                                        'remaining_qty': layer.remaining_qty,
                                        'remaining_value': unit_cost * layer.remaining_qty
                                    })
                        except Exception as e:
                            print(e)

    def for_incoming_fix(self):
        product_ids = self.env['product.product'].sudo().search([('type', '=', 'product')])
        for product in product_ids:
            if product.standard_price == 0:
                layer_ids = self.env['stock.valuation.layer'].sudo().search(
                    [('product_id.id', '=', product.id), ('company_id', '=', self.env.company.id)])
                if len(layer_ids) > 0:
                    layer_with_remaining = layer_ids.filtered(lambda x: x.remaining_qty > 0 and x.unit_cost > 0)
                    if len(layer_with_remaining) > 0:
                        product.write({
                            'standard_price': layer_with_remaining[0].unit_cost
                        })
                    else:
                        quant_ids = self.env['stock.quant'].sudo().search(
                            [('product_id.id', '=', product.id), ('company_id', '=', self.env.company.id)])
                        sum_quant = sum(quant.quantity for quant in quant_ids)
                        if sum_quant == 0:
                            last_incoming_layer_id = layer_ids.filtered(lambda x: x.quantity > 0 and x.unit_cost > 0)
                            if last_incoming_layer_id:
                                product.write({
                                    'standard_price': last_incoming_layer_id[0].unit_cost
                                })

    def generate_layer_move(self):
        layer_ids = self.env['stock.valuation.layer'].sudo().search(
            [('product_id.categ_id.property_valuation', '=', 'real_time'), ('company_id.id', '=', self.env.company.id)])
        for layer in layer_ids:
            if layer.stock_move_id:
                if layer.unit_cost > 0:
                    journal_id, acc_src, acc_dest, acc_valuation = layer.stock_move_id._get_accounting_data_for_valuation()
                    am_vals = []
                    if not layer.account_move_id:
                        move_id = self.env['account.move'].sudo().create({
                            'date': layer.create_date.date(),
                            'journal_id': journal_id,
                            'move_type': 'entry',
                            'ref': layer.description,
                            'company_id': self.env.company.id,
                        })
                    if layer.account_move_id:
                        layer.account_move_id.button_draft()
                        move_id = layer.account_move_id
                    if layer.stock_move_id._is_in():
                        if layer.stock_move_id._is_returned(valued_type='in'):
                            am_vals.append(
                                layer.stock_move_id.with_company(layer.company_id)._prepare_account_move_vals(acc_dest,
                                                                                                              acc_valuation,
                                                                                                              journal_id,
                                                                                                              layer.quantity,
                                                                                                              layer.description,
                                                                                                              layer.id,
                                                                                                              layer.unit_cost))
                        else:
                            am_vals.append(
                                layer.stock_move_id.with_company(layer.company_id)._prepare_account_move_vals(acc_src,
                                                                                                              acc_valuation,
                                                                                                              journal_id,
                                                                                                              layer.quantity,
                                                                                                              layer.description,
                                                                                                              layer.id,
                                                                                                              layer.unit_cost))

                        # Create Journal Entry for products leaving the company
                    if layer.stock_move_id._is_out():
                        cost = layer.unit_cost
                        if layer.stock_move_id._is_returned(valued_type='out'):
                            am_vals.append(
                                layer.stock_move_id.with_company(layer.company_id)._prepare_account_move_vals(acc_valuation,
                                                                                                              acc_src,
                                                                                                              journal_id,
                                                                                                              layer.quantity,
                                                                                                              layer.description,
                                                                                                              layer.id,
                                                                                                              layer.unit_cost))
                        else:
                            am_vals.append(
                                layer.stock_move_id.with_company(layer.company_id)._prepare_account_move_vals(acc_valuation,
                                                                                                              acc_dest,
                                                                                                              journal_id,
                                                                                                              layer.quantity,
                                                                                                              layer.description,
                                                                                                              layer.id,
                                                                                                              cost))
                    line_ids = am_vals[0]['line_ids']
                    to_create_line = []
                    for line in line_ids:
                        line[2]['move_id'] = move_id.id
                        to_create_line.append(line[2])
                    self.env['account.move.line'].sudo().create(to_create_line)
                    layer.write({
                        'account_move_id': move_id.id
                    })
