# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = 'res.company'

    groups_id = fields.Many2one('swiss.company.groups', string='Groups')


class SwissCompanyGroups(models.Model):
    _name = "swiss.company.groups"
    _description = "Swiss Company Groups"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', default=10)