from odoo import fields, models, api
from ..utils.lot_generator import generate_lot, get_last_lot


def get_message(qty_requested, qty_done):
    message = 'La cantidad realizada no puede ser mayor a la demanda \n'
    message += f'Cantidad Solicitada {qty_requested} \n'
    message += f'Cantidad Realizada {qty_done} '
    return message


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    analytic_account = fields.Many2one('account.analytic.account', string="Cuenta Analítica")
    product_requested_qty = fields.Float('Demanda')
    product_requested_uom_id = fields.Many2one('uom.uom', 'Unidad de Medida')
    product_unit_cost = fields.Float('Costo Unitario')
    product_total_cost = fields.Float('Costo Total')
    supplier_lot = fields.Char('Lote Proveedor')
    is_tracking_lot = fields.Boolean('Tiene Seguimiento por Lote?', compute="compute_is_tracking_lot")
    product_stock_qty = fields.Float('Stock Disponible', compute='compute_product_stock_qty')
    stock_product_lot_ids = fields.Many2many('stock.production.lot', compute='compute_stock_product_lot_ids')
    is_return_line = fields.Boolean('Es Movimiento de devolución', related='picking_id.is_return')
    employee_id = fields.Many2one('hr.employee', string="Retirado por")
    category_id = fields.Many2one('product.category', string='Categoria')
    notes = fields.Html('Observacion')

    @api.onchange('product_id')
    def onchange_product_requested(self):
        for item in self:
            item.product_requested_uom_id = item.product_id.uom_id

    @api.depends('product_id', 'location_id', 'lot_id')
    def compute_stock_product_lot_ids(self):
        for item in self:
            if item.product_id:
                if item.product_id.tracking == 'lot':
                    location_id = item.location_dest_id if item.picking_type_id.code == 'incoming' else item.location_id
                    quant_ids = item.product_id.stock_quant_ids.filtered(
                        lambda x: x.location_id.id == location_id.id and x.quantity > 0)
                    item.stock_product_lot_ids = quant_ids.mapped('lot_id')
                    return
            item.stock_product_lot_ids = None
            return

    @api.depends('product_id', 'location_id', 'lot_id')
    def compute_product_stock_qty(self):
        for item in self:
            location_id = item.location_dest_id if item.picking_type_id.code == 'incoming' else item.location_id
            if item.product_id:
                if len(item.product_id.stock_quant_ids) == 0:
                    item.product_stock_qty = 0
                    return
                quant_ids = item.product_id.stock_quant_ids.filtered(lambda x: x.location_id.id == location_id.id)
                item.product_stock_qty = sum(quant.quantity for quant in quant_ids)
                if item.product_id.tracking == 'lot' and item.lot_id:
                    quant_lot_ids = quant_ids.filtered(lambda x: x.lot_id.id == item.lot_id.id)
                    item.product_stock_qty = sum(quant.quantity for quant in quant_lot_ids)
                    return
                return
            item.product_stock_qty = 0

    def _action_done(self):
        for item in self:
            standard_price = item.product_id.standard_price
            if item.picking_id.delayed_picking:
                date_done = item.picking_id.date_done
            if item.picking_id:
                if item.picking_id.note or item.picking_id.note != '':
                    item.write({
                        'notes': item.picking_id.note
                    })
                if item.product_requested_qty > 0:
                    if item.product_requested_qty < item.qty_done:
                        raise models.ValidationError(get_message(item.product_requested_qty, item.qty_done))
                if not item.analytic_account and item.picking_code == 'outgoing':
                    if item.location_dest_id.usage != 'supplier':
                        raise models.UserError(
                            f'El movimiento del producto {item.product_id.display_name} no tiene definida la cuenta '
                            f'analítica,'
                            f' por lo cual no se puede finalizar la orden de entrega')
                if item.move_id.purchase_line_id:
                    standard_price = item.move_id.purchase_line_id.price_unit
            item.write({
                'product_unit_cost': standard_price,
                'product_total_cost': standard_price * item.qty_done
            })
        res = super(StockMoveLine, self)._action_done()
        for item in self:
            if item.picking_id.delayed_picking:
                item.write({
                    'date': date_done
                })
        return res
    
    @api.model
    def create(self, vals_list):
        if 'product_id' in vals_list.keys():
            product = self.env['product.product'].sudo().search([('id', '=', vals_list['product_id'])])
            if product:
                if product.categ_id:
                    vals_list['category_id'] = product.categ_id.id
        if 'picking_id' in vals_list.keys():
            picking_id = self.env['stock.picking'].sudo().search([('id', '=', vals_list['picking_id'])])
            product_id = self.env['product.product'].sudo().search([('id', '=', vals_list['product_id'])])
            if picking_id.picking_type_id.code == 'incoming' and product_id.tracking == 'lot':
                last_lot_id = get_last_lot()
                if last_lot_id:
                    lot_id = self.env['stock.production.lot'].sudo().create({
                        'name': last_lot_id,
                        'product_id': vals_list['product_id'],
                        'is_auto_lot': True,
                        'company_id': self.env.company.id,
                    })
                    vals_list['lot_id'] = lot_id.id
                    vals_list['lot_name'] = lot_id.name
        res = super(StockMoveLine, self).create(vals_list)
        if res.picking_id.picking_type_id.code == 'incoming':
            if res.move_id:
                res.product_requested_qty = res.move_id.product_uom_qty
        return res
