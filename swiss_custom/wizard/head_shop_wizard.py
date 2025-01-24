# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from operator import itemgetter
from itertools import groupby
from datetime import datetime


class HeadShopWizard(models.TransientModel):
    _name = 'head.shop.wizard'
    _description = 'Head Shop Wizard'

    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End', required=True)

    def generate_report(self):
        data = {'date_start': self.date_start, 'date_end': self.date_end}
        return self.env.ref('swiss_custom.head_shop_report').report_action([], data=data)

class HeadShopReport(models.AbstractModel):
    _name = 'report.swiss_custom.report_headshop'
    _description = 'Head Shop Report'

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
        # Penjualan Retail
        order_obj = self.env['pos.order'].search([('session_id.stop_at', '>=', date_start), ('session_id.stop_at', '<=', date_end)])
        cashier = sum(order_obj.mapped('amount_total'))

        payment_obj = self.env['pos.payment'].search([('payment_date', '>=', date_start), ('payment_date', '<=', date_end)])
        cashier_deposit = sum(payment_obj.mapped('amount'))

        deposit = cashier - cashier_deposit

        # Penjualan
        sale_regular_obj = self.env['sale.order'].search([('date_order', '>=', date_start), ('date_order', '<=', date_end), ('order_type', '=', 'regular')])
        sale_regular = sum(sale_regular_obj.mapped('amount_total'))

        payments = self.env['account.payment'].search([('date', '>=', date_start), ('date', '<=', date_end), ('payment_type', '=', 'inbound')])
        regular_sales = self.env['sale.order'].search([('order_type', '=', 'regular'),('name', 'in', self.env['account.move'].search([('name', 'in', payments.mapped('ref'))]).mapped('invoice_origin'))])
        payment_regular = sum(
            account.amount
            for account in payments
            if any(
                account.ref == move.name and move.invoice_origin == sale.name
                for move in self.env['account.move'].search([('name', '=', account.ref)], limit=1)
                for sale in regular_sales
            )
        )

        receivable = sale_regular - payment_regular

        sale_total = cashier + sale_regular

        # Pesanan Khusus
        sale_special_obj = self.env['sale.order'].search([('date_order', '>=', date_start), ('date_order', '<=', date_end), ('order_type', '=', 'special')])
        sale_special = sum(sale_special_obj.mapped('amount_total'))

        total_delivered = sum(line.price_unit * line.qty_delivered for order in sale_special_obj for line in order.order_line)

        special_sales = self.env['sale.order'].search([('order_type', '=', 'special'),('name', 'in', self.env['account.move'].search([('name', 'in', payments.mapped('ref'))]).mapped('invoice_origin'))])
        payment_special = sum(
            account.amount
            for account in payments
            if any(
                account.ref == move.name and move.invoice_origin == sale.name
                for move in self.env['account.move'].search([('name', '=', account.ref)], limit=1)
                for sale in special_sales
            )
        )

        receivable_two = sale_special - payment_special

        receivable_all = receivable + receivable_two

        # Rincian Pembayaran
        settlement_payments = self.env['account.payment'].search([('date', '>=', date_start),('date', '<=', date_end),('payment_type', '=', 'inbound')])
        sale_orders = self.env['sale.order'].search([('date_order', '>=', date_start),('date_order', '<=', date_end)])

        settlement_payment = sum(account.amount for account in settlement_payments if any(
            account.ref == move_obj.name and sale_order.name == move_obj.invoice_origin
            for move_obj in self.env['account.move'].search([('name', 'in', settlement_payments.mapped('ref'))])
            for sale_order in sale_orders
        ))

        date_start = datetime.strptime(date_start, '%Y-%m-%d')
        date_end = datetime.strptime(date_end, '%Y-%m-%d')

        down_payment = sum(
            account.amount
            for account in settlement_payments
            if any(
                move.product_id.name == 'Down payment'
                for move in self.env['account.move'].search([('name', '=', account.ref)], limit=1).invoice_line_ids
            )
        )

        filtered_payments = [
            account.amount
            for account in settlement_payments
            if any(
                sale.date_order < date_start or sale.date_order > date_end
                for move in self.env['account.move'].search([('name', '=', account.ref)], limit=1)
                for sale in self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            )
        ]

        repayment = sum(filtered_payments)

        # Mutasi Stock
        stock_move_line = self.env['stock.move.line']
        stock_objs = stock_move_line.search([('date', '<=', date_start), ('state', '=', 'done')])
        stock_in = sum(stock.quantity * stock.product_id.standard_price for stock in stock_objs if stock.picking_id.picking_type_code == 'incoming')
        stock_out = sum(stock.quantity * stock.product_id.standard_price for stock in stock_objs if stock.picking_id.picking_type_code == 'outgoing')
            
        stock_begin = stock_in - stock_out

        receipt = sum(rec.quantity * rec.product_id.standard_price for rec in self.env['stock.move'].search([('picking_code', '=', 'incoming'), ('date', '>=', date_start), ('date', '<=', date_end), ('state', '=', 'done')]))


        return_obj = self.env['stock.move'].search([('picking_code', '=', 'outgoing'),('date', '>=', date_start),('date', '<=', date_end), ('state', '=', 'done')])
        retur = sum(
            returns.quantity * returns.product_id.standard_price
            for returns in return_obj
            if "Return of WH/IN" in returns.picking_id.origin
        )

        return_good_obj = self.env['stock.move'].search([('picking_code', '=', 'incoming'),('date', '>=', date_start),('date', '<=', date_end), ('state', '=', 'done')])
        retur_good = sum(
            returnz.quantity * returnz.product_id.standard_price
            for returnz in return_good_obj
            if "Return of WH/OUT" in returnz.picking_id.origin
        )

        total_mutasi_order = cashier

        final_stock = ((stock_begin + receipt) - (retur + retur_good)) - total_mutasi_order

        opname = sum(stock.quantity * stock.product_id.standard_price for stock in self.env['stock.quant'].search([('location_id.usage', 'not in', ['view', 'supplier', 'customer', 'inventory', 'production', 'transit'])]))

        difference_stock = opname - final_stock

        # Table Payment
        table_payment = []
        result = []

        for payment in payment_obj:
            table_payment.append({
                'name': payment.payment_method_id.name,
                'deposit': payment.amount, 
                'payment': 0,
                'order': 0,
                'settlement_payment': 0,
                'down_payment': 0,
                'repayment': 0,
                'dump': 'dump',
            })
            
        for account in payments:
            sale_obj = self.env['sale.order'].search([
                ('name', '=', self.env['account.move'].search([('name', '=', account.ref)], limit=1).invoice_origin),
                ('order_type', '=', 'regular')
            ], limit=1)
            
            if sale_obj:
                table_payment.append({
                    'name': account.journal_id.name,
                    'deposit': 0,
                    'payment': account.amount,
                    'order': 0,
                    'settlement_payment': 0,
                    'down_payment': 0,
                    'repayment': 0,
                    'dump': 'dump',
                })
        
        for sale in sale_special_obj:
            invoice_objs = self.env['account.move'].search([('invoice_origin', '=', sale.name)])
            payment_objs = self.env['account.payment'].search([('ref', 'in', invoice_objs.mapped('name'))])
            for payment in payment_objs:
                table_payment.append({
                    'name': payment.journal_id.name,
                    'deposit': 0,
                    'payment': 0,
                    'order': payment.amount,
                    'settlement_payment': 0,
                    'down_payment': 0,
                    'repayment': 0,
                    'dump': 'dump',
                })

        for account in settlement_payments:
            move_obj = self.env['account.move'].search([('name', '=', account.ref)], limit=1)
            sale_order_name = move_obj.invoice_origin
            sale_obj = self.env['sale.order'].search([
                ('name', '=', sale_order_name),
                ('date_order', '>=', date_start),
                ('date_order', '<=', date_end)
            ], limit=1)

            if sale_obj:
                table_payment.append({
                    'name': account.journal_id.name,
                    'deposit': 0,
                    'payment': 0,
                    'order': 0,
                    'settlement_payment': account.amount,
                    'down_payment': 0,
                    'repayment': 0,
                    'dump': 'dump',
                })

        for account in settlement_payments:
            move_obj = self.env['account.move'].search([('name', '=', account.ref)], limit=1)
            has_down_payment = any(move.product_id.name == 'Down payment' for move in move_obj.invoice_line_ids)
            
            if has_down_payment:
                table_payment.append({
                    'name': account.journal_id.name,
                    'deposit': 0,
                    'payment': 0,
                    'order': 0,
                    'settlement_payment': 0,
                    'down_payment': account.amount,
                    'repayment': 0,
                    'dump': 'dump',
                })


        for account in settlement_payments:
            move_obj = self.env['account.move'].search([('name', '=', account.ref)], limit=1)
            sale_obj = self.env['sale.order'].search([('name', '=', move_obj.invoice_origin)], limit=1)
            if sale_obj:
                if sale_obj.date_order < date_start or sale_obj.date_order > date_end:
                    table_payment.append({
                        'name': account.journal_id.name,
                        'deposit': 0,
                        'payment': 0,
                        'order': 0,
                        'settlement_payment': 0,
                        'down_payment': 0,
                        'repayment': account.amount,
                        'dump': 'dump',
                    })
        
        grouper = itemgetter("name", "dump")
        for key, grp in groupby(sorted(table_payment, key = grouper), grouper):
            temp_dict = dict(zip(["name", "dump"], key))
            deposit_table = 0
            payment_table = 0
            order_table = 0
            settlement_payment_table = 0
            repayment_table = 0
            down_payment_table = 0
            for item in grp:
                deposit_table += item["deposit"]
                payment_table += item["payment"]
                order_table += item["order"]
                settlement_payment_table += item["settlement_payment"]
                down_payment_table += item["down_payment"]
                repayment_table += item["repayment"]
            temp_dict["deposit"] = deposit_table
            temp_dict["payment"] = payment_table
            temp_dict["order"] = order_table
            temp_dict["settlement_payment"] = settlement_payment_table
            temp_dict["repayment"] = repayment_table
            temp_dict["down_payment"] = down_payment_table
            result.append(temp_dict)

        return {
            'name': 'hahaha1',
            'cashier': cashier,
            'cashier_deposit': cashier_deposit,
            'deposit': deposit,
            'sale_regular': sale_regular,
            'payment_regular': payment_regular,
            'receivable': receivable,
            'sale_total': sale_total,
            'sale_special': sale_special,
            'total_delivered': total_delivered,
            'payment_special':payment_special,
            'receivable_two': receivable_two,
            'receivable_all': receivable_all,
            'settlement_payment': settlement_payment,
            'repayment': repayment,
            'down_payment': down_payment,
            'stock_begin':stock_begin,
            'receipt': receipt,
            'retur': retur,
            'retur_good': retur_good,
            'total_mutasi_order': total_mutasi_order,
            'final_stock':final_stock,
            'opname': opname,
            'difference_stock':difference_stock,
            'date_start': date_start.strftime("%d") + ' ' + date_start.strftime("%B") + ' ' + date_start.strftime("%Y"),
            'date_end': date_end.strftime("%d") + ' ' + date_end.strftime("%B") + ' ' + date_end.strftime("%Y"),
            'payment': result
        }