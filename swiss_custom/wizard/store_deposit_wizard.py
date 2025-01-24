# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from operator import itemgetter
from itertools import groupby

class StoreDepositWizard(models.TransientModel):
    _name = 'store.deposit.wizard'
    _description = 'Store Deposit Wizard'

    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End', required=True)


    def generate_report(self):
        data = {'date_start': self.date_start, 'date_end': self.date_end}
        return self.env.ref('swiss_custom.store_deposit_report').report_action([], data=data)
    
class StoreDepositReport(models.AbstractModel):
    _name = 'report.swiss_custom.report_storedeposit'
    _description = 'Store Deposit Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update({
            'date_start': data.get('date_start'),
            'date_end': data.get('date_end')
        })
        data.update(self.get_sale_details(data['date_start'], data['date_end']))
        return data

    @api.model
    def get_sale_details(self, date_start=False, date_end=False):
        payment_obj = self.env['pos.payment'].search([('payment_date', '>=', date_start), ('payment_date', '<=', date_end), ('company_id', '=', self.env.company.id)])
        account_obj = self.env['account.payment'].search([('date', '>=', date_start), ('date', '<=', date_end),('payment_type', '=', 'inbound')])
        datas = []
        result = []
        for payment in payment_obj:            
            datas.append({
                'name':  payment.payment_method_id.name,
                'deposit_cashier': payment.amount,
                'paid': 0,
                'order': 0,
                'dump': 'dump',
            })

        for account in account_obj:
            move_obj = self.env['account.move'].search([('name', '=', account.ref)],limit=1)
            sale_obj = self.env['sale.order'].search([('name', '=', move_obj.invoice_origin)], limit=1)
            if sale_obj.order_type:
                if sale_obj.order_type == 'regular':
                    datas.append({
                        'name':  account.journal_id.name,
                        'deposit_cashier': 0,
                        'paid': account.amount,
                        'order': 0,
                        'dump': 'dump',
                    })
                else:
                    datas.append({
                        'name':  account.journal_id.name,
                        'deposit_cashier': 0,
                        'paid': 0,
                        'order': account.amount,
                        'dump': 'dump',
                    })
        grouper = itemgetter("name", "dump")
        for key, grp in groupby(sorted(datas, key = grouper), grouper):
            temp_dict = dict(zip(["name", "dump"], key))
            deposit_cashier = 0
            paid = 0
            order = 0
            for item in grp:
                paid += item["paid"]
                order += item["order"]
                deposit_cashier += item["deposit_cashier"]
            temp_dict["paid"] = paid
            temp_dict["order"] = order
            temp_dict["deposit_cashier"] = deposit_cashier
            result.append(temp_dict)
        
        return {
            'name': 'hahaha1',
            'date_start': date_start,
            'date_end': date_end,
            'payment': result,
            'company': self.env['res.company'].browse(self.env.company.id)
        }