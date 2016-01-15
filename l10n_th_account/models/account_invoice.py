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
    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Overwrite """
        line_to_reconcile = self.env['account.move.line']
        for inv in self:
            line_to_reconcile += inv.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable'))
        # Intercept here, and pass to account_move_line._create_write_off()
        line_to_reconcile.write({'payment_id': payment_line.payment_id.id})
        # --
        return (line_to_reconcile + payment_line).reconcile(writeoff_acc_id, writeoff_journal_id)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
