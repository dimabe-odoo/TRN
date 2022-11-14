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
        product_ids = self.env['product.product'].sudo().search([('type', '=', 'product')])
        for product in product_ids:
            if product.standard_price > 0 and product.categ_id.property_valuation == 'real_time':
                layer_ids = self.env['stock.valuation.layer'].sudo().search(
                    [('product_id.id', '=', product.id), ('company_id.id', '=', self.env.company.id)])
                if len(layer_ids) > 0:
                    remaining_qty = 0
                    counter = 0
                    for layer in layer_ids:
                        try:
                            if layer.quantity < 0:
                                layer_in_ids = layer_ids.filtered(lambda x: x.quantity > 0)
                                if remaining_qty == 0:
                                    remaining_qty = layer_in_ids[counter].quantity
                                if (remaining_qty + layer.quantity) <= 0:
                                    first_qty = remaining_qty
                                    first_cost = layer_in_ids[counter].unit_cost
                                remaining_qty += layer.quantity
                                if remaining_qty <= 0:
                                    diff = remaining_qty
                                    if diff < 0:
                                        counter += 1 if len(layer_in_ids) > 1 else 0
                                        remaining_qty = layer_in_ids[counter].quantity
                                        remaining_qty += diff
                                        first_value = first_cost * first_qty
                                        second_value = layer_in_ids[counter].unit_cost * abs(diff)
                                        total_layer = first_value + second_value
                                        unit_cost = total_layer / layer.quantity
                                        layer.write({
                                            'value': total_layer * -1,
                                            'unit_cost': unit_cost
                                        })
                                        continue
                                if remaining_qty >= 0:
                                    unit_cost = layer_in_ids[counter].unit_cost
                                    total_layer = self.env.company.currency_id.round(unit_cost * layer.quantity)
                                    layer.write({
                                        'unit_cost': unit_cost,
                                        'value': total_layer
                                    })
                                    if remaining_qty == 0 and layer_in_ids[counter].id != layer_in_ids[-1].id:
                                        counter += 1 if len(layer_in_ids) > 1 else 0
                                    continue
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
        product_ids = self.env['product.product'].sudo().search([('id', '=', 12568)])
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
                                    'standard_price': last_incoming_layer_id.unit_cost
                                })
