# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from operator import itemgetter
from itertools import groupby

class PosSession(models.Model):
    _inherit = 'pos.session'


    def get_payment_details(self):
        payments = []
        result = []
        for session in self:
            payment_obj = self.env['pos.payment'].search([('session_id', '=', session.id)])
            for pay in payment_obj:
                if pay.amount > 0:
                    payments.append({
                        'name': pay.payment_method_id.name,
                        'amount': pay.amount,
                        'cashier': pay.pos_order_id.user_id.name,
                        'paid': pay.pos_order_id.amount_paid,
                        'dump': 'dump',
                    })

        grouper = itemgetter("name", "dump")
        for key, grp in groupby(sorted(payments, key = grouper), grouper):
            temp_dict = dict(zip(["name", "dump"], key))
            amount = 0
            cashier = []
            paid = 0
            for item in grp:
                amount += item["amount"]
                paid += item["paid"]
                cashier.append(item["cashier"])
            unique_values = set(cashier)
            unique_values_str = map(str, unique_values)
            value = ', '.join(unique_values_str)
            
            temp_dict["amount"] = amount
            temp_dict["cashier"] = value
            temp_dict["paid"] = paid
            result.append(temp_dict)
        return result