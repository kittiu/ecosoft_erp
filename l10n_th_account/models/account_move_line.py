# -*- coding: utf-8 -*-

from openerp import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    doc_ref = fields.Char(
        string='Document Ref',
        readonly=True,
    )

    def _create_writeoff(self, vals):
        # Fixed to make sure writeoff entries also have payment_id
        print self
        vals.update({'payment_id': self.payment_id.id})
        return super(AccountMoveLine, self)._create_writeoff(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
