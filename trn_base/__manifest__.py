# -*- coding: utf-8 -*-
{
    'name': "trn_base",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'stock', 'hr', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/groups.xml',
        'reports/purchase_order.xml',
        'views/stock_move_line.xml',
        'views/stock_picking.xml',
        'views/ir_ui_menu.xml',
        'views/purchase_order.xml',
        'views/product_template.xml',
        'views/res_company.xml',
        'reports/picking_report.xml',
        'views/stock_quant.xml',
        'wizards/stock_return_picking.xml',
        'views/stock_valuation_layer.xml',
        'data/ir_action_window.xml',
        'views/stock_warehouse.xml',
        'wizards/product_last_wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "assets": {
        "web.assets_common": [
            "trn_base/static/css/trn_base.scss",
        ],
    },
}
