# -*- encoding: utf-8 -*-

{
    'name': 'Accounting Management Extension',
    'version': '1.0',
    'category': 'Accounting & Finance',
    'sequence': 15,
    'summary': 'Additional/Modification for Ecosoft',
    'description': """
Modification
============

* Revise Invoice Form
    """,
    'website': 'http://ecosoft.co.th',
    'depends': ['account'],
    'data': [
        'views/account_report.xml',
        'views/report_invoice.xml',
        'views/report_payment.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
