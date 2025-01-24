import base64

from odoo import _, fields, models


class Company(models.Model):
    _inherit = "res.company"

    sale_term_and_condition = fields.Html(string="Terms and Conditions")

    schedule_create_commission_bill = fields.Boolean(
        string="Auto Create Commission Bill"
    )
    branch_commission = fields.Float(string="Branch Commission (%)")
    commission_product_id = fields.Many2one(
        comodel_name="product.product", string="Commission Product"
    )
    interval_number = fields.Integer(string="Commission Interval Number")
    interval_type = fields.Selection(
        selection=[
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
        ],
        default="days",
        string="Commission Interval Unit",
    )
    next_call = fields.Datetime(
        string="Commission Next Execution Date",
    )
    auto_attach_sale_report = fields.Boolean("Auto Attach Sale Report")

    def action_all_company_branches_kilau(self):
        self.ensure_one()

        action = self.env["ir.actions.act_window"]._for_xml_id(
            "kilau_custom.action_res_company_form_kilau"
        )

        action["name"] = _("Branches")
        action["domain"] = [("parent_id", "=", self.id)]
        action["context"] = {
            "active_test": False,
            "default_parent_id": self.id,
            "form_view_ref": "kilau_custom.res_company_view_form_kilau",
        }
        return action

    def _run_auto_commission_bill(self):
        company_ids = self.search([])

        so_obj = self.env["sale.order"]
        am_obj = self.env["account.move"]
        aml_obj = self.env["account.move.line"]

        context_bill = {
            "default_move_type": "in_invoice",
            "display_account_trust": True,
        }
        context_invoice = {"default_move_type": "out_invoice"}

        for rec in company_ids:
            if rec.parent_id:
                if rec.schedule_create_commission_bill:
                    so_ids = False
                    # sale order
                    so_ids = so_obj.search([("company_id", "=", rec.id)])
                    price_unit = (
                        sum(so_ids.mapped("amount_total")) * rec.branch_commission / 100
                    )
                    name = "Sale Order Report"
                    if so_ids:
                        report = self.env["ir.actions.report"]._render_qweb_pdf(
                            "sale.report_saleorder_raw", so_ids.ids
                        )
                        filename = name + ".pdf"
                    if rec.next_call <= fields.Datetime.now():
                        # Create Bill
                        today = fields.Datetime.today().strftime("%d %b %Y")
                        comm_bill = am_obj.with_context(context_bill).create(
                            {
                                "partner_id": rec.parent_id.partner_id.id,
                                "company_id": rec.id,
                                "invoice_date": fields.Datetime.now(),
                                "ref": f"Commission share - {today}",
                            }
                        )
                        aml_obj.create(
                            {
                                "product_id": rec.commission_product_id.id,
                                "move_id": comm_bill.id,
                                "price_unit": price_unit,
                            }
                        )
                        if so_ids and rec.auto_attach_sale_report:
                            # attachment
                            pdf_attach = self.env["ir.attachment"].create(
                                {
                                    "name": filename,
                                    "type": "binary",
                                    "datas": base64.b64encode(report[0]),
                                    "res_model": "account.move",
                                    "res_id": comm_bill.ids[0],
                                    "mimetype": "application/pdf",
                                }
                            )
                            attachment = [(4, pdf_attach.id)]
                            comm_bill.attachment_ids = attachment
                        # Create Invoice
                        comm_inv = am_obj.with_context(context_invoice).create(
                            {
                                "partner_id": rec.partner_id.id,
                                "company_id": rec.parent_id.id,
                                "invoice_date": fields.Datetime.now(),
                                "ref": f"Commission share - {today}",
                            }
                        )
                        aml_obj.create(
                            {
                                "product_id": rec.commission_product_id.id,
                                "move_id": comm_inv.id,
                                "price_unit": price_unit,
                            }
                        )
                        if so_ids and rec.auto_attach_sale_report:
                            # attachment
                            pdf_attach = self.env["ir.attachment"].create(
                                {
                                    "name": filename,
                                    "type": "binary",
                                    "datas": base64.b64encode(report[0]),
                                    "res_model": "account.move",
                                    "res_id": comm_bill.ids[0],
                                    "mimetype": "application/pdf",
                                }
                            )
                            attachment = [(4, pdf_attach.id)]
                            comm_inv.attachment_ids = attachment
