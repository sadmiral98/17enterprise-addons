from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"    

    name_material = fields.Char(string="Name Material")
    number_lot = fields.Char(string="Number Lot")
    number_po = fields.Char(string="Number PO")
    number_btb = fields.Char(string="Number BTB")
    name_factory = fields.Char(string="Factory Name")
    expired_date = fields.Date(string="Expired Date")
    plan = fields.Char(string="Plan")
    number_containers_received = fields.Char(string="Number Of Containers Received")
    number_containers_opened = fields.Char(string="Number Of Containers Opened")
    number_containers_taken = fields.Char(string="Number Of Containers Taken")
    sample_container = fields.Char(string="Sample Container")
    sample_tools = fields.Char(string="Sample Tools")
    sampling_room = fields.Char(string="Sampling Room")
    sampling_by = fields.Char(string="Sampling By")
    sampling_date = fields.Date(string="Sampling Date")

    def action_print_sample_collection(self):
        return self.env.ref('tradmed_custom.action_sample_collection').report_action(self)
