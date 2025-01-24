# -*- coding: utf-8 -*-

from odoo import models, api
from itertools import groupby
from operator import itemgetter


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super()._payment_fields(order, ui_paymentline)
        res['card_no'] = ui_paymentline.get('card_no')
        return res
