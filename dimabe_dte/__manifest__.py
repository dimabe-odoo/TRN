# -*- coding: utf-8 -*-
{
    'name': "dimabe_dte",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_cl_edi', 'l10n_cl_edi_boletas', 'dimabe_clients', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'reports/invoice.xml',
        'data/custom_collection_group_data.xml',
        'views/account_move_reversal.xml',
        'views/account_move.xml',
        'views/custom_change_status_dte.xml',
        'views/custom_remaining_caf_group.xml',
        'views/l10n_cl_daily_sales_book_views.xml',
        'views/l10n_latam_document_type_view.xml',
        'views/main_data_change_report.xml',
        'views/res_company.xml',
        'views/res_partner.xml'


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
