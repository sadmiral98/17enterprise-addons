{
    "name": "Kilau Custom",
    "version": "1.0",
    "category": "Customization",
    "description": """
        Custom module for Kilau Laundry.
        This module provides additional features and customization for Kilau Laundry management.
    """,
    "author": "Hafizh Ibnu Syam",
    "website": "",
    "depends": ["base", "account", "sale"],
    "data": [
        "data/ir_cron.xml",
        "views/menu_views.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",

        "report/report_e_receipt.xml",

        # 'static/fonts/Harmonia_Sans_W01_Bold.ttf',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "OPL-1",
}
