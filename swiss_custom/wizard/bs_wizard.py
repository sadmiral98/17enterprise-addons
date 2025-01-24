# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from operator import itemgetter
from itertools import groupby
from datetime import datetime


class ReportBSXlsxWizard(models.TransientModel):
    _name = 'bs.wizard'
    _description = 'Report BS XLSX Wizard'

    company_id = fields.Many2one('res.company', string='Company', domain=[('parent_id','!=',False)])
    date_start = fields.Date(string='Date Start', required=True)
    date = fields.Date(string='Date End', required=True)

    def generate_report(self):
        formatted_start_date = self.date_start.strftime("%d-%m-%Y")
        formatted_end_date = self.date.strftime("%d-%m-%Y")
        formatted_date = f"{formatted_start_date} - {formatted_end_date}"

        data = {'formatted_date': formatted_date}
        return self.env.ref('swiss_custom.action_report_bs_xlsx').report_action([], data=data)

class ReportBSXlsxReport(models.AbstractModel):
    _name = 'report.swiss_custom.report_bs_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Report BS XLSX'

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = "BS"
            sheet = workbook.add_worksheet(report_name[:31])

            title_format = workbook.add_format({'align':'left', 'valign':'vcenter', 'font_size':11, 'border':0, 'bold':True})
            header_format = workbook.add_format({'align':'left', 'valign':'vcenter', 'font_size':11, 'border':1})
            header_center_format = workbook.add_format({'align':'center', 'valign':'vcenter', 'font_size':11, 'border':1})
            data_format = workbook.add_format({'align':'left', 'valign':'vcenter', 'font_size':11, 'border':1})
            data_number_format = workbook.add_format({'align':'right', 'valign':'vcenter', 'font_size':11, 'border':1})
            currency_format = workbook.add_format({'num_format': '[$IDR] #,##0.00','font_size':11, 'border':1})
            footer_text_format = workbook.add_format({'align':'center', 'valign':'vcenter', 'font_size':11})
            footer_number_format = workbook.add_format({'align':'right', 'valign':'vcenter', 'font_size':11})
            footer_currency_format = workbook.add_format({'num_format': '[$IDR] #,##0.00','font_size':11,})

            company_name, record_data = self.get_data_bs(obj)

            #COLUMN FIX
            sheet.set_column('B:B', 15)
            sheet.set_column('C:C', 20)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:E', 25)
            sheet.set_column('F:F', 25)

            # sheet.write(x, y, text content, text format)
            #TITLE
            sheet.write(0, 0, f"Roti BS - {company_name}", title_format)
            sheet.write(1, 0, f"Tanggal : {data.get('formatted_date')}", title_format)

            #HEADER
            sheet.write(3, 0, "No", header_format)
            sheet.write(3, 1, "PLU", header_format)
            sheet.write(3, 2, "JENIS ROTI", header_format)
            sheet.write(3, 3, "QTY", header_center_format)
            sheet.write(3, 4, "HARGA", header_center_format)
            sheet.write(3, 5, "JUMLAH", header_center_format)

            x = 4
            no = 1
            total_qty = 0
            total_harga = 0
            total_jumlah = 0
            #RECORDS
            for (product_id, jenis_roti, plu, harga), data in record_data.items():
                sheet.write(x, 0, no, data_format)
                sheet.write(x, 1, plu, data_format)
                sheet.write(x, 2, jenis_roti, data_format)
                sheet.write(x, 3, data['quantity'], data_number_format)
                sheet.write(x, 4, harga, currency_format)
                sheet.write(x, 5, data['jumlah'], currency_format)

                total_qty += data['quantity']
                total_harga += harga
                total_jumlah += data['jumlah']
                x += 1
                no += 1
            
            x = x + 1
            sheet.merge_range(x, 0,x,2,"TOTAL", footer_text_format)
            sheet.write(x, 3, total_qty, footer_number_format)
            sheet.write(x, 4, total_harga, footer_currency_format)
            sheet.write(x, 5, total_jumlah, footer_currency_format)

    
    def get_data_bs(self, wizard_data):
        company_obj = self.env['res.company'].sudo().browse(wizard_data.company_id.id)
        company_name = company_obj.name
        start_date = datetime(wizard_data.date_start.year, wizard_data.date_start.month, wizard_data.date_start.day, 0, 0, 0, 0)
        end_date = datetime(wizard_data.date.year, wizard_data.date.month, wizard_data.date.day, 23, 59, 59)

        bom_is_bs = self.env['mrp.bom'].sudo().search([('is_bs','=',True)])
        bom_ids = bom_is_bs.mapped('id')
        records = self.env['mrp.production'].sudo().search([
            ('bom_id','in',bom_ids),
            ('date_start','>=',start_date),
            ('date_start','<',end_date),
            ('company_id','=',company_obj.id)
            ])

        record_data = {}
        for record in records:
            jenis_roti = record.product_id.name
            plu = record.product_id.barcode
            harga = record.product_id.lst_price
            key = (record.product_id.id, jenis_roti, plu, harga)

            if key not in record_data:
                record_data[key] = {
                    'quantity': 0,
                    'jumlah': 0,
                }
            record_data[key]['quantity'] += record.product_qty
            record_data[key]['jumlah'] = float(record_data[key]['quantity']) * float(harga)

        return company_name, record_data