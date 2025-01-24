# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from operator import itemgetter
from itertools import groupby
from datetime import datetime

class ReportRecapOrderXlsxWizard(models.TransientModel):
    _name = 'recap.order.wizard'
    _description = 'Recap Order XLSX Wizard'

    company_id = fields.Many2many('res.company', string='Company', domain=[('parent_id','!=',False)])
    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End', required=True)

    def generate_report(self):
        formatted_start_date = self.date_start.strftime("%d-%m-%Y")
        formatted_end_date = self.date_end.strftime("%d-%m-%Y")
        formatted_date = f"{formatted_start_date} - {formatted_end_date}"

        data = {'formatted_date': formatted_date}
        return self.env.ref('swiss_custom.action_recap_order_xlsx').report_action([], data=data)

class ReportRecapOrderXlsxReport(models.AbstractModel):
    _name = 'report.swiss_custom.recap_order_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Recap Order XLSX'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            format_start_date = datetime(obj.date_start.year, obj.date_start.month, obj.date_start.day, 0, 0, 0, 0)
            format_end_date = datetime(obj.date_end.year, obj.date_end.month, obj.date_end.day, 23, 59, 59)

            company_obj = self.env['res.company'].sudo().browse(obj.company_id.ids)
            sale_obj = self.env['sale.order.line'].sudo().search([('company_id', 'in', company_obj.ids), ('order_id.date_order', '>=', format_start_date), ('order_id.date_order', '<', format_end_date)])

            report_name = "Recap Order"
            sheet = workbook.add_worksheet(report_name[:31])

            title_format = workbook.add_format({'align':'left', 'valign':'vcenter', 'font_size':11, 'border':0, 'bold':True})
            title = workbook.add_format({'border':1, 'align': 'center', 'valign': 'vcenter', 'font_size':8})

            sheet.set_column('C:C', 15)

            sheet.write(0, 0, f"Tanggal : {data.get('formatted_date')}", title_format)

            sheet.merge_range('A2:A4', 'NO', title)
            sheet.merge_range('B2:B4', 'PLU', title)
            sheet.merge_range('C2:C4', 'NAMA ROTI', title)

            start_column = 3
            start_row = 1

            for company in obj.company_id:
                sheet.merge_range(start_row , start_column, start_row, start_column + 2, company.name, title)
                sheet.merge_range(start_row + 1 , start_column, start_row + 2, start_column, 'TOKO.', title)
                sheet.merge_range(start_row + 1, start_column + 1,start_row + 1, start_column + 2, 'PSN.KHS.', title)
                sheet.write(start_row + 2, start_column + 1, 'P.', title)
                sheet.write(start_row + 2, start_column + 2, 'S.', title)
                start_column += 3

            sheet.merge_range(start_row, start_column, start_row, start_column + 2, 'Total', title)
            sheet.merge_range(start_row + 1 , start_column, start_row + 2, start_column, 'TOKO.', title)
            sheet.merge_range(start_row + 1, start_column + 1,start_row + 1, start_column + 2, 'PSN.KHS.', title)
            sheet.write(start_row + 2, start_column + 1, 'P.', title)
            sheet.write(start_row + 2, start_column + 2, 'S.', title)

            product_data = {}
            for sale in sale_obj:
                product_key = (sale.product_id.id, sale.company_id.id)
                if product_key not in product_data:
                    product_data[product_key] = {'cab': 0, 'pesanan_p': 0, 'pesanan_s': 0}
                
                for line in sale.order_id.order_line:
                    if line.company_id.id == sale.company_id.id:
                        if line.order_id.order_type == 'regular':
                            product_data[product_key]['cab'] += line.product_uom_qty
                        elif line.order_id.order_type == 'special':
                            product_data[product_key]['pesanan_p'] += line.product_uom_qty
                            product_data[product_key]['pesanan_s'] += line.product_uom_qty

            row = 4
            seen_ids = set() 

            for index, sale in enumerate(sale_obj, start=1):
                product_id = sale.product_id.id
                
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    
                    sheet.write(row, 0, index, title)
                    
                    sheet.write(row, 1, sale.product_id.default_code, title)
                    
                    sheet.write(row, 2, sale.product_id.name, title)

                    start_column = 3

                    total_count_cab = 0
                    total_count_pes_p = 0
                    total_count_pes_s = 0
                    
                    for company in obj.company_id: 
                        count_cab = 0
                        count_pes_p = 0
                        count_pes_s = 0
                        sales_cab_obj = self.env['sale.order.line'].sudo().search([('id', 'in', sale_obj.ids),('product_id', '=', sale.product_id.id),('company_id', 'in', company.ids), ('order_id.order_type', '=', 'regular')])
                        sales_pes_obj = self.env['sale.order.line'].sudo().search([('id', 'in', sale_obj.ids),('product_id', '=', sale.product_id.id),('company_id', 'in', company.ids), ('order_id.order_type', '=', 'special')])

                        count_cab += sum(sales_cab_obj.mapped('product_uom_qty'))
                        total_count_cab += count_cab
                        for sales in sales_pes_obj:
                            jam = sales.order_id.date_order.hour

                            jam = (jam + 7) % 24

                            if jam >= 6 and jam < 12:
                                count_pes_p += sales.product_uom_qty
                                total_count_pes_p += count_pes_p
                            else:
                                count_pes_s += sales.product_uom_qty
                                total_count_pes_s += count_pes_s

                        sheet.write(row, start_column, count_cab, title)
                        sheet.write(row, start_column + 1, count_pes_p, title)
                        sheet.write(row, start_column + 2, count_pes_s, title)
                        
                        start_column += 3            

                    sheet.write(row, start_column, total_count_cab, title)
                    sheet.write(row, start_column + 1, total_count_pes_p, title)
                    sheet.write(row, start_column + 2, total_count_pes_s, title)

                    row += 1