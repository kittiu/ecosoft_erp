# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _create_payment_entry(self, amount):
        """ Adding Undue Tax and Tax line form invoice
            TODO: Not applicable for multi-currency
        """
        move = super(AccountPayment, self)._create_payment_entry(amount)
        # Loop through invoices find the undue vat and copy
        for invoice in self.invoice_ids:
            if not invoice.move_id:
                continue
            for move_line in invoice.move_id.line_ids:
                tax = move_line.tax_line_id
                account_id = invoice.type in ('out_invoice', 'in_invoice') \
                    and tax.counterpart_tax_id.account_id.id \
                    or tax.counterpart_tax_id.refund_account_id.id
                if tax.undue_tax:
                    # Undue VAT line, credit -> debit
                    undue_tax_dict = move_line.copy_data({
                        'move_id': move.id,
                        'credit': move_line.debit,
                        'debit': move_line.credit,
                    })[0]
                    move_line.with_context(check_move_validity=False).create(undue_tax_dict)
                    # Due VAT line, change name and account_id
                    tax_dict = move_line.copy_data({
                        'move_id': move.id,
                        'name': tax.counterpart_tax_id.name,
                        'account_id': account_id,
                    })[0]
                    move_line.create(tax_dict)
        return move
