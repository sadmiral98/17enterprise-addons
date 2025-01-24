# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import timedelta
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, format_amount, format_date, html_keep_url, is_html_empty
from odoo.tools.sql import create_index

from odoo.addons.payment import utils as payment_utils

INVOICE_STATUS = [
    ('upselling', 'Upselling Opportunity'),
    ('invoiced', 'Fully Invoiced'),
    ('to invoice', 'To Invoice'),
    ('no', 'Nothing to Invoice')
]

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('sent', "Quotation Sent"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_type = fields.Selection(
        selection=[
            ('regular', 'Shop'),
            ('special', 'Special Order')
        ],
        string='Order Type'
    )
    amount_discount = fields.Float(
        string='Discount',
        compute='_amount_discount'
    )
    amount_before_discount = fields.Float(
        string='Before Discount',
        compute='_amount_discount'
    )
    bill_no = fields.Char(
        string='Bill No'
    )
    delivery_type = fields.Selection(
        selection=[
            ('self', 'Self-Collect'),
            ('delivery', 'Deliver'),
        ],
        string='Delivery Type'
    )
    description = fields.Text(
        string='Description'
    )

    def _amount_discount(self):
        for rec in self:
            amount_discount = 0
            amount_total = 0
            for line in rec.order_line:
                amount_total += (line.price_unit * line.product_uom_qty)
                amount_discount += (amount_total * line.discount / 100)
            rec.amount_discount = amount_discount
            rec.amount_before_discount = amount_total
