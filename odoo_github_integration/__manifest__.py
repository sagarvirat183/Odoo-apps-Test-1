{
    'name': 'GitHub Integration',
    'summary': 'Integrate Odoo with GitHub to manage repositories and apps',
    'version': '1.0',
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/odoo_github_integration.xml',
        'wizard/odoo_github_integration.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}