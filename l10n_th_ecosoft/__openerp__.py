# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2011 Smartmode LTD (<http://www.smartmode.co.uk>).

{
    'name': 'Thailand - Chart of account (ECOSOFT)',
    'version': '1.0',
    'category': 'Localization/Account Charts',
    'description': """
    """,
    'author': 'Kitti U. (Ecosoft)',
    'website': 'http://ecosoft.co.th',
    'depends': ['base', 'account'],
    'data': [
        'views/partner_view.xml',
        'data/account_chart_template.xml',
        'data/account.account.template.csv',
        'data/account.chart.template.csv',
        'data/account.account.tag.csv',
        'data/account.tax.template.csv',
        'data/account_chart_template.yml',
    ],
    'demo' : [],
    'installable': True,
}
