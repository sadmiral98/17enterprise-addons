from odoo import api, fields, models, _

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_bs = fields.Boolean('Is Bs', default=False)