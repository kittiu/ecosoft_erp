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

    undue_tax = fields.Boolean(
        string='Undue Tax',
        default=False,
        help="This is a undueed tax. "
        "The tax point will be deferred to the time of payment",
    )
    counterpart_tax_id = fields.Many2one(
        'account.tax',
        string='Counterpart Tax',
        ondelete='restrict',
        help="Counterpart Tax for payment process"
    )

    # Compute

    # Constrain

    # Onchange

    # CRUD methods

    # Action methods

    # Business methods
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
