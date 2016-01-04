# -*- encoding: utf-8 -*-

{
    'name': 'Sales Management Extension',
    'version': '1.0',
    'category': 'Sales Management',
    'sequence': 15,
    'summary': 'Additional/Modification for Ecosoft',
    'description': """
Modification
============

* Revise Sales Form
    """,
    'website': 'http://ecosoft.co.th',
    'depends': ['sale'],
    'data': [
        'views/report_saleorder.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
