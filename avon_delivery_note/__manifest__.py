# -*- coding: utf-8 -*-
{
    'name': "Delivery Note Report -18.0.0.1",

    'summary': "Delivery Note Report",

    'description': """Delivery Note Report""",

    'author': "Prixgen",
    'website': "https://www.prixgen.com",
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',

    'category': 'Stock',
    'module_type':'official',
    'version': '18.0.0.0',

    'depends': ['base','account','stock','stock_account','purchase','l10n_in','sale','product',],

    'data': [
        'reports/header_footer.xml',
        'reports/delivery_note_report.xml',
        'views/views.xml'
    ],
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': True,
   
}


