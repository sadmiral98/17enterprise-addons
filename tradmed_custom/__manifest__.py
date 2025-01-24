# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Tradmed Custom',
    'version': '1.1',
    'depends': ['stock', 'quality_control'],
    'category': 'Inventory/Inventory',
    'data': [
        'report/paperformat.xml',
        'report/sample_collection_report.xml',
        
        'views/stock_picking_views.xml',
    ],
    'assets': {},
    'license': 'LGPL-3',
}
