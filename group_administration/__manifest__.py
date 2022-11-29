# -*- coding: utf-8 -*-
{
	'name': "Administracion de Grupos",
	
	'summary': """
        Administracion de Grupos nativo""",
	
	'description': """
        Administracion de Grupos nativos a travez de grupos independientes
    """,
	
	'author': "Dimabe",
	'website': "http://www.yourcompany.com",
	
	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
	# for the full list
	'category': 'Uncategorized',
	'version': '0.1',
	
	# any module necessary for this one to work correctly
	'depends': ['base'],
	
	# always loaded
	'data': [
		'security/ir.model.access.csv',
		'views/group_administration.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		'demo/demo.xml',
	],
}
