from odoo import models, fields, api, _
from odoo.models import UserError
from odoo.tools.float_utils import float_round

class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        move_dest_exists = False
        product_return_moves = [(5,)]
        if self.picking_id and self.picking_id.state != 'done':
            raise UserError(_("You may only return Done pickings."))
        # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
        # default values for creation.
        line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
        product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
        for move in self.picking_id.move_line_ids_without_package:
            if move.state == 'cancel':
                continue
            if move.move_id.scrapped:
                continue
            if move.move_id.move_dest_ids:
                move_dest_exists = True
            product_return_moves_data = dict(product_return_moves_data_tmpl)
            self.env['stock.return.picking.line'].sudo().create(self._prepare_stock_return_picking_line_vals_from_move(move))
        if self.picking_id and not product_return_moves:
            raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)."))
        if self.picking_id:
            self.move_dest_exists = move_dest_exists
            self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
            self.original_location_id = self.picking_id.location_id.id
            location_id = self.picking_id.location_id.id
            if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
            self.location_id = location_id

    @api.model
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move_line):
        quantity = stock_move_line.move_id.product_qty
        for move in stock_move_line.move_id.move_dest_ids:
            if move.origin_returned_move_id and move.origin_returned_move_id != stock_move_line:
                continue
            if move.state in ('partially_available', 'assigned'):
                quantity -= sum(stock_move_line.move_id.move_line_ids.mapped('product_qty'))
            elif move.state in ('done'):
                quantity -= move.product_qty
        quantity = float_round(quantity, precision_rounding=stock_move_line.move_id.product_id.uom_id.rounding)
        return {
            'product_id': stock_move_line.product_id.id,
            'quantity': stock_move_line.qty_done,
            'move_id': stock_move_line.move_id.id,
            'wizard_id': self.id,
            'analytic_account_id': stock_move_line.analytic_account.id,
            'uom_id': stock_move_line.product_id.uom_id.id,
            'move_line_id': stock_move_line.id,
        }

    def _create_returns(self):
        res = super(StockReturnPicking, self)._create_returns()
        picking_id = self.env['stock.picking'].sudo().search([('id','=',res[0])])
        if picking_id:
            picking_id.move_line_ids_without_package.unlink()
            for r_move in self.product_return_moves:
                self.env['stock.move.line'].sudo().create({
                    'product_id': r_move.product_id.id,
                    'picking_id': picking_id.id,
                    'product_uom_id': r_move.product_id.uom_id.id,
                    'qty_done': r_move.quantity,
                    'location_id': picking_id.location_id.id,
                    'location_dest_id': picking_id.location_dest_id.id,
                    'analytic_account': r_move.analytic_account_id.id,
                })
            picking_id.button_validate()
        return res

class ReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica", readonly=True)

    move_line_id = fields.Many2one('stock.move.line',string='Movimientos Producto')
