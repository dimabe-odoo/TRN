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

    ## TODO Eliminar este codigo luego de la correcion

    def for_action_fix(self):
        product_ids = self.env['product.product'].sudo().search([('type', '=', 'product'),('categ_id.property_valuation','=', 'real_time')])
        for product in product_ids:
            if product.standard_price > 0:
                layer_ids = self.env['stock.valuation.layer'].sudo().search(
                    [('product_id.id', '=', product.id), ('company_id', '=', self.env.company.id)])
                if len(layer_ids) > 0:
                    layer_without_value_ids = layer_ids.filtered(
                        lambda x: x.quantity < 0 and not x.account_move_id and x.value == 0)
                    layer_in_ids = layer_ids.filtered(lambda x: x.quantity > 0)
                    remaining_qty = 0
                    counter = 0
                    for layer in layer_without_value_ids:
                        try:
                            total_layer = 0
                            if remaining_qty == 0:
                                remaining_qty = layer_in_ids[counter].quantity
                            remaining_qty += layer.quantity
                            if remaining_qty <= 0:
                                counter += 1 if len(layer_in_ids) > 1 else 0
                                diff = remaining_qty
                                remaining_qty = layer_in_ids[counter].quantity
                                remaining_qty += diff
                            if remaining_qty > 0:
                                unit_cost = layer_in_ids[counter].unit_cost
                                total_layer = self.env.company.currency_id.round(unit_cost * layer.quantity)
                                layer.write({
                                    'unit_cost': unit_cost,
                                    'value': total_layer
                                })
                        except Exception as e:
                            print(e)
                        if not layer.account_move_id and total_layer != 0:
                            move_id = self.env['account.move'].sudo().create({
                                'date': layer.create_date.date(),
                                'journal_id': product.categ_id.property_stock_journal.id,
                                'move_type': 'entry',
                                'ref': layer.description,
                                'company_id': self.env.company.id,
                            })
                            line_ids = []
                            credit_line = {
                                'credit': abs(total_layer),
                                'debit': 0,
                                'account_id': product.categ_id.property_stock_valuation_account_id.id,
                                'move_id': move_id.id,
                                'product_id': product.id,
                                'quantity': abs(layer.quantity),
                                'name': layer.description,
                            }
                            line_ids.append(credit_line)
                            for line in layer.stock_move_id.move_line_ids:
                                total = self.env.company.currency_id.round(unit_cost * line.qty_done)
                                debit_line = {
                                    'debit': total,
                                    'credit': 0,
                                    'quantity': line.qty_done,
                                    'account_id': product.categ_id.property_stock_account_output_categ_id.id,
                                    'move_id': move_id.id,
                                    'product_id': product.id,
                                    'name': layer.description,
                                }
                                line_ids.append(debit_line)
                            total_debit = sum(deb['debit'] for deb in line_ids)
                            diff = abs(total_layer) - total_debit
                            if diff != 0:
                                account_id = self.env.company.account_diff_id.id if self.env.company.account_diff_id else product.categ_id.property_stock_account_output_categ_id.id
                                diff_line = {
                                    'account_id': account_id,
                                    'name': 'Diferencia {}'.format(layer.description),
                                    'debit': abs(diff) if diff > 0 else 0,
                                    'credit': abs(diff) if diff < 0 else 0,
                                    'move_id': move_id.id,
                                    'product_id': product.id,
                                }
                                line_ids.append(diff_line)
                            self.env['account.move.line'].sudo().create(line_ids)
                            move_id.action_post()
                            layer.write({
                                'account_move_id': move_id.id
                            })

    def fix_return_layer(self):
        product_ids = self.env['product.product'].sudo().search([('type', '=', 'product'),('categ_id.property_valuation','=', 'real_time')])
        for product in product_ids:
            layer_ids = self.env['stock.valuation.layer'].sudo().search(
                [('product_id.id', '=', product.id), ('company_id', '=', self.env.company.id)])
            layer_return_ids = layer_ids.filtered(lambda x: x.quantity > 0 and '/DEV/' in x.description)
            for return_layer in layer_return_ids:
                if return_layer.stock_move_id.origin_returned_move_id:
                    origin_move_id = return_layer.stock_move_id.origin_returned_move_id
                    if len(origin_move_id.stock_valuation_layer_ids.filtered(lambda x: x.unit_cost > 0)):
                        unit_cost = \
                            origin_move_id.stock_valuation_layer_ids.filtered(lambda x: x.unit_cost > 0)[
                                0].unit_cost
                        return_layer.write({
                            'unit_cost': unit_cost,
                            'value': unit_cost * return_layer.quantity,
                            'remaining_qty': return_layer.remaining_qty,
                            'remaining_value': unit_cost * return_layer.remaining_qty
                        })
                        if not return_layer.account_move_id and unit_cost == 0:
                            total_layer = unit_cost * return_layer.quantity
                            if not return_layer.account_move_id and total_layer != 0:
                                move_id = self.env['account.move'].sudo().create({
                                    'date': return_layer.create_date.date(),
                                    'journal_id': product.categ_id.property_stock_journal.id,
                                    'move_type': 'entry',
                                    'ref': return_layer.description,
                                    'company_id': self.env.company.id,
                                })
                                line_ids = []
                                credit_line = {
                                    'credit': abs(total_layer),
                                    'debit': 0,
                                    'account_id': product.categ_id.property_stock_valuation_account_id.id,
                                    'move_id': move_id.id,
                                    'product_id': product.id,
                                    'quantity': abs(return_layer.quantity),
                                    'name': return_layer.description,
                                }
                                line_ids.append(credit_line)
                                for line in return_layer.stock_move_id.move_line_ids:
                                    total = self.env.company.currency_id.round(unit_cost * line.qty_done)
                                    debit_line = {
                                        'debit': total,
                                        'credit': 0,
                                        'quantity': line.qty_done,
                                        'account_id': product.categ_id.property_stock_account_output_categ_id.id,
                                        'move_id': move_id.id,
                                        'product_id': product.id,
                                        'name': return_layer.description,
                                    }
                                    line_ids.append(debit_line)
                                total_debit = sum(deb['debit'] for deb in line_ids)
                                diff = abs(total_layer) - total_debit
                                if diff != 0:
                                    account_id = self.env.company.account_diff_id.id if self.env.company.account_diff_id else product.categ_id.property_stock_account_output_categ_id.id
                                    diff_line = {
                                        'account_id': account_id,
                                        'name': 'Diferencia {}'.format(return_layer.description),
                                        'debit': abs(diff) if diff > 0 else 0,
                                        'credit': abs(diff) if diff < 0 else 0,
                                        'move_id': move_id.id,
                                        'product_id': product.id,
                                    }
                                    line_ids.append(diff_line)
                                self.env['account.move.line'].sudo().create(line_ids)
                                move_id.action_post()
                                return_layer.write({
                                    'account_move_id': move_id.id
                                })

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
                        if product.qty_available == 0:
                            last_incoming_layer_id = layer_ids.filtered(lambda x: x.quantity > 0 and x.unit_cost > 0)
                            if last_incoming_layer_id:
                                product.write({
                                    'standard_price': last_incoming_layer_id.unit_cost
                                })
