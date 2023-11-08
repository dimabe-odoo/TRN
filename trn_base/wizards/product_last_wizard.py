import base64

import xlsxwriter

from odoo import models


class ProductLastWizard(models.TransientModel):
    _name = 'product.last.wizard'
    _description = 'Informe de ultimos entrada y salida'

    def generate_report(self):
        for item in self:
            file_name = 'temp'
            products = self.env['product.product'].sudo().search([])
            company_id = self.env.company

            workbook = xlsxwriter.Workbook(file_name)
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
            worksheet = workbook.add_worksheet('Ultimas entrada y Salida')
            worksheet.merge_range('A1:A2', 'PRODUCTO',self.get_format('title', workbook))
            worksheet.merge_range('B1:B2', 'CATEGORIA',self.get_format('title', workbook))
            worksheet.merge_range('C1:E1', 'ULTIMA COMPRA',self.get_format('title', workbook))
            worksheet.merge_range('F1:I1', 'ULTIMO CONSUMO',self.get_format('title', workbook))
            worksheet.write(1, 2, 'FECHA',self.get_format('title', workbook))
            worksheet.write(1, 3, 'CANTIDAD REALIZADA',self.get_format('title', workbook))
            worksheet.write(1, 4, 'COSTO UNITARIO',self.get_format('title', workbook))
            worksheet.write(1, 5, 'FECHA',self.get_format('title', workbook))
            worksheet.write(1, 6, 'CANTIDAD REALIZADA',self.get_format('title', workbook))
            worksheet.write(1, 7, 'COSTO UNITARIO',self.get_format('title', workbook))
            worksheet.write(1, 8, 'CUENTA ANALITICA',self.get_format('title', workbook))
            row = 2
            col = 0
            for product in products:
                last_purchase_order_line = self.env['purchase.order.line'].sudo().search(
                    [('product_id', '=', product.id),('company_id','=', company_id.id)], order='write_date desc', limit=1)
                worksheet.write(row, col, product.display_name,self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, product.categ_id.name,self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, last_purchase_order_line.date_order if last_purchase_order_line else '',date_format)
                col += 1
                worksheet.write(row, col, last_purchase_order_line.product_uom_qty if last_purchase_order_line else '',self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, last_purchase_order_line.price_unit if last_purchase_order_line else '',self.get_format('text', workbook))
                last_stock_move_line = self.env['stock.move.line'].sudo().search(
                    [('product_id', '=', product.id), ('analytic_account', '!=', False),
                     ('picking_code', '=', 'outgoing'),('company_id','=', company_id.id)], order='date desc', limit=1)
                col += 1
                worksheet.write(row, col, last_stock_move_line.date if last_stock_move_line else '',date_format)
                col += 1
                worksheet.write(row, col, last_stock_move_line.qty_done if last_stock_move_line else '',self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, last_stock_move_line.product_unit_cost if last_stock_move_line else '',self.get_format('text', workbook))
                col += 1
                worksheet.write(row, col, last_stock_move_line.analytic_account.name if last_stock_move_line else '',self.get_format('text', workbook))
                col += 1
                col = 0
                row += 1
            worksheet.autofit()
            workbook.close()
            with open(file_name, "rb") as file:
                file_base64 = base64.b64encode(file.read())

            file_name = 'Informe de ultimos entrada y salida '
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