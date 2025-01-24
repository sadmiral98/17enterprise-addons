# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError


class PosPayment(models.Model):
    """ Used to register payments made in a pos.order.

    See `payment_ids` field of pos.order model.
    The main characteristics of pos.payment can be read from
    `payment_method_id`.
    """

    _inherit = "pos.payment"

    card_no = fields.Char('Card Number')
