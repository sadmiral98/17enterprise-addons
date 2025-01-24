# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from operator import itemgetter
from itertools import groupby
from datetime import datetime


class ReportBranchProductionXlsxWizard(models.TransientModel):
    _name = 'branch.production.wizard'
    _description = 'Branch Production XLSX Wizard'

    groups_id = fields.Many2many('swiss.company.groups', string='Groups')
    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End', required=True)

    def generate_report(self):
        formatted_start_date = self.date_start.strftime("%d-%m-%Y")
        formatted_end_date = self.date_end.strftime("%d-%m-%Y")
        formatted_date = f"{formatted_start_date} - {formatted_end_date}"

        data = {'formatted_date': formatted_date}
        return self.env.ref('swiss_custom.action_branch_production_xlsx').report_action([], data=data)

class ReportBSXlsxReport(models.AbstractModel):
    _name = 'report.swiss_custom.branch_production_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Branch Production XLSX'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            format_start_date = datetime(obj.date_start.year, obj.date_start.month, obj.date_start.day, 0, 0, 0, 0)
            format_end_date = datetime(obj.date_end.year, obj.date_end.month, obj.date_end.day, 23, 59, 59)
            company_obj = self.env['res.company'].sudo().search([('groups_id', 'in', obj.groups_id.ids)])
            sale_obj = self.env['sale.order.line'].sudo().search([('company_id', 'in', company_obj.ids), ('order_id.date_order', '>=', format_start_date), ('order_id.date_order', '<', format_end_date)])

            report_name = "Branch Production"
            sheet = workbook.add_worksheet(report_name[:31])

            table_center = workbook.add_format({'align': 'center','border':1, 'font_size':9})
            title_format = workbook.add_format({'align':'left', 'valign':'vcenter', 'font_size':11, 'border':0, 'bold':True})
            title = workbook.add_format({'border':1, 'align': 'center', 'valign': 'vcenter', 'font_size':8})

            sheet.write(0, 0, f"Tanggal : {data.get('formatted_date')}", title_format)

            sheet.merge_range('A2:A3', 'NO', title)
            sheet.merge_range('B2:B3', 'PLU', title)
            sheet.merge_range('C2:C3', 'JENIS ROTI', title)

            # Urutkan grup berdasarkan sequence
            sorted_groups = sorted(obj.groups_id, key=lambda x: x.sequence)

            start_column = 3
            start_row = 1

            for groups in sorted_groups:
                sheet.merge_range(start_row, start_column, start_row, start_column + 1, groups.name, title)
                sheet.write(start_row + 1, start_column, 'CAB.', title)
                sheet.write(start_row + 1, start_column + 1, 'PSN.KHS.', title)
                start_column += 2

            sheet.merge_range(start_row, start_column, start_row + 1, start_column, 'STOCK.', title)


            product_data = {}
            for sale in sale_obj:
                product_key = (sale.product_id.id, sale.company_id.id)
                if product_key not in product_data:
                    product_data[product_key] = {'cab': 0, 'pesanan': 0}
                
                for line in sale.order_id.order_line:
                    if line.company_id.id == sale.company_id.id:
                        if line.order_id.order_type == 'regular':
                            product_data[product_key]['cab'] += line.product_uom_qty
                        elif line.order_id.order_type == 'special':
                            product_data[product_key]['pesanan'] += line.product_uom_qty

            row = 3
            seen_ids = set() 

            for index, sale in enumerate(sale_obj, start=1):
                product_id = sale.product_id.id
                
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    
                    sheet.write(row, 0, index, title)
                    
                    sheet.write(row, 1, sale.product_id.default_code, title)
                    
                    sheet.write(row, 2, sale.product_id.name, title)

                    start_column = 3
                    
                    for groups in sorted_groups:  # Gunakan sorted_groups yang sudah diurutkan
                        count_cab = 0
                        count_pes = 0
                        sales_cab_obj = self.env['sale.order.line'].sudo().search([('id', 'in', sale_obj.ids),('product_id', '=', sale.product_id.id),('company_id.groups_id', 'in', groups.ids), ('order_id.order_type', '=', 'regular')])
                        sales_pes_obj = self.env['sale.order.line'].sudo().search([('id', 'in', sale_obj.ids),('product_id', '=', sale.product_id.id),('company_id.groups_id', 'in', groups.ids), ('order_id.order_type', '=', 'special')])
                        count_cab += sum(sales_cab_obj.mapped('product_uom_qty'))
                        count_pes += sum(sales_pes_obj.mapped('product_uom_qty'))

                        sheet.write(row, start_column, count_cab, title)
                        sheet.write(row, start_column + 1, count_pes, title)
                        
                        start_column += 2

                    location_ids = self.env['stock.location'].search([('usage', '=', 'internal')])
                    total_stock = 0
                    
                    for location_id in location_ids:
                        quants = self.env['stock.quant'].search([
                            ('product_id', '=', sale.product_id.id),
                            ('location_id', '=', location_id.id),
                        ])
                        total_stock += sum(quants.mapped('quantity'))
                        
                    sheet.write(row, start_column, total_stock, title)
                    
                    row += 1




