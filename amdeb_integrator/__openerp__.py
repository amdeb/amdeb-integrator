# __openerp__.py

{
    'name': 'Amdeb Integrator',
    'summary': 'Base module to integrate Odoo with other marketplaces.',
    'version': '0.02',
    'category': 'Amdeb Integration',
    'website': 'https://github.com/amdeb/amdeb-integrator',
    'author': 'Amdeb Developers',
    'description': """
Amdeb Integrator
=========================

This is an Odoo module that intercepts e-commerce related model changes
and write changes to integration tables.
""",
    'depends': [
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_job.xml'
    ],
    'installable': True,
    'application': False,
}
