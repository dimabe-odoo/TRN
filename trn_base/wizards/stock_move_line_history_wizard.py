import base64

import xlsxwriter
import datetime

from odoo import fields, models


class StockMoveLineHistoryWizard(models.TransientModel):
    _name = 'stock.move.line.history.wizard'

    location_ids = fields.Many2many('stock.location', string='Ubicaciones', domain=[('usage', '=', 'internal')])

    date = fields.Date('Hasta')

    def generate_report(self):
        if (len(self.location_ids)) == 0 or not self.location_ids:
            raise models.UserError("Se seleccionar al menos una bodega para continuar")
        for location in self.location_ids:
            date = self.date if self.date else datetime.date.today()
            stock_move_line = self.env['stock.move.line'].sudo().search(
                [('state', '=', 'done'), ('date', '<=', date)])
            stock_move_line = stock_move_line.filtered(
                lambda x: x.location_id == location or x.location_dest_id == location).sorted(key='date', reverse=True)
            file_name = 'temp'
            workbook = xlsxwriter.Workbook(file_name)
            worksheet = workbook.add_worksheet(f'Valorización hasta {date.strftime("%m-%d-%Y")}')
            titles = ['Fecha de operación','Operación', 'Producto', 'Categoria de producto',  'Bodega origen',
                      'Bodega destino', 'Unidad de medida',
                      'Cuenta analitica','Cantidad', 'Costo unitario', 'Costo total', 'Usuario']
            col = 0
            row = 0
            for title in titles:
                worksheet.write(row, col, title, self.get_format('title', workbook))
                col += 1
            worksheet.autofilter('A1:L1')
            col = 0
            row += 1
            for move_line in stock_move_line:
                qty = 0
                unit_cost = 0
                total_cost = 0
                if move_line.location_id == location:
                    qty = move_line.qty_done * -1
                    unit_cost = move_line.product_unit_cost * -1
                    total_cost = move_line.product_total_cost * -1
                elif move_line.location_dest_id == location:
                    qty = move_line.qty_done
                    unit_cost = move_line.product_unit_cost
                    total_cost = move_line.product_total_cost
                worksheet.write(row, col, move_line.date, self.get_format('date', workbook))
                col += 1
                worksheet.write(row, col, move_line.picking_id.name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.product_id.display_name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.product_id.categ_id.display_name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.location_id.display_name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.location_dest_id.display_name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.product_uom_id.display_name, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.analytic_account.display_name if move_line.analytic_account else '',
                                self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, qty, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, unit_cost, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, total_cost, self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, move_line.write_uid.display_name, self.get_format('text', workbook))
                col += 1
                row += 1
                col = 0
            worksheet.autofit()
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())

            file_name = f'Valorización {date.strftime("%m-%d-%Y")}'
            attachment_id = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'datas': file_base64
            })
            action = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
                'target': 'current',
            }
            return action

    def get_format(self, type, workbook):
        format_excel = workbook.add_format()
        if type == "header":
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_font_size(28)
        if type == 'date':
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_num_format('dd/mm/yyyy hh:mm:ss')
        if type == "header_text":
            format_excel.set_border(1)
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
        if type == "money":
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_border(1)
            format_excel.set_border_color("black")
            format_excel.set_num_format('$#,##0')
        if type == "header_label":
            format_excel.set_align('center')
            format_excel.set_border(1)
            format_excel.set_align('vcenter')
        if type == 'title':
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
        if type == 'text':
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_border(1)
        if type == 'total':
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_font_name("Times New Roman")
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
        if type == 'total_money':
            format_excel.set_border(1)
            format_excel.set_bold()
            format_excel.set_align('center')
            format_excel.set_align('vcenter')
            format_excel.set_font_name("Times New Roman")
            format_excel.set_bg_color("#0083be")
            format_excel.set_font_color("#FFFFFF")
            format_excel.set_num_format('$#,##0')
        return format_excel
