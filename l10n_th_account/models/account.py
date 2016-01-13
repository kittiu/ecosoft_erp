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


class AccountTax(models.Model):
    _inherit = 'account.tax'

    wht_tax = fields.Boolean(
        string='Withholding Tax',
        default=False,
        help="This is a withholding tax. "
        "Tax amount will be deducted during payment.",
    )
    wht_threshold = fields.Float(
        string='Threshold Amount',
        help="Withholding Tax will be applied only if base amount more "
        "or equal to threshold amount.",
    )
    undue_tax = fields.Boolean(
        string='Undue Tax',
        default=False,
        help="This is a undue tax. "
        "The tax point will be deferred to the time of payment.",
    )
    counterpart_tax_id = fields.Many2one(
        'account.tax',
        string='Counterpart Tax',
        ondelete='restrict',
        help="Counterpart Tax for payment process."
    )

    # Compute

    # Constrain

    # Onchange
    @api.onchange('wht_tax')
    def _onchange_wht_tax(self):
        if self.wht_tax:
            self.undue_tax = False

    @api.onchange('undue_tax')
    def _onchange_undue_tax(self):
        if self.undue_tax:
            self.wht_tax = False

    # CRUD methods

    # Action methods

    # Business methods
    @api.multi
    def compute_all(self, price_unit, currency=None,
                    quantity=1.0, product=None, partner=None):
        taxes = self.filtered(lambda r: not r.wht_tax)  # Remove all WHT
        res = super(AccountTax, taxes).compute_all(
            price_unit, currency=currency, quantity=quantity,
            product=product, partner=partner)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
