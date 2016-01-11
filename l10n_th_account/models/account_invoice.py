# -*- coding: utf-8 -*-
#
#    Author: Kitti Upariphutthiphong
#    Copyright 2014-2015 Ecosoft Co., Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Compute

    # Constrain

    # Onchange

    # CRUD methods

    # Action methods

    # Business methods

#     @api.multi
#     def get_taxes_values(self):
#         tax_grouped = super(AccountInvoice, self).get_taxes_values()
#         AccountTax = self.env['account.tax']
#         for tax_id in tax_grouped:
#             tax = AccountTax.browse(tax_id)
#             if tax.undue_tax:
#                 undue_account_id = tax.undue_account_id.id
#                 undue_refund_account_id = tax.undue_refund_account_id.id
#                 account_id = self.type in ('out_invoice', 'in_invoice') and \
#                     undue_account_id or undue_refund_account_id
#                 tax_grouped[tax_id]['account_id'] = account_id
#         return tax_grouped

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
