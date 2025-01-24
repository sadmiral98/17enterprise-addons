from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_term_and_condition(self):
        company_id = self.env.company
        return company_id.sale_term_and_condition

    term_and_condition = fields.Html(
        string="Term and Condition", default=_default_term_and_condition
    )
