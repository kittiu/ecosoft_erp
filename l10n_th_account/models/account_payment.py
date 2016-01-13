# -*- coding: utf-8 -*-

from openerp import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    amount_wht = fields.Monetary(
        string='Withhold Amount',
        compute='_compute_amount_wht',
        store=True,
        copy=False
    )
    wht_account_id = fields.Many2one(
        'account.account',
        string="Withhold Account",
        domain=[('deprecated', '=', False)],
        copy=False,
    )
    wht_percent = fields.Float(
        string="Withhold Percent",
        copy=False,
    )

    # Compute
    @api.one
    @api.depends('invoice_ids', 'amount', 'payment_date',
                 'currency_id', 'amount_wht')
    def _compute_payment_difference(self):
        if len(self.invoice_ids) == 0:
            return
        self.payment_difference = self._compute_total_invoices_amount() - \
            self.amount - self.amount_wht

    @api.one
    @api.depends('amount')
    def _compute_amount_wht(self):
        if len(self.invoice_ids) == 0:
            return
        assert len(self.invoice_ids) == 1, "WHT work with 1 invoice only"
        residual = self._compute_total_invoices_amount()
        if not residual:
            self.amount_wht = 0.0
            return
        invoice = self.invoice_ids[0]
        wht_coeff, untaxed_coeff = self._invoice_wht_coeff(invoice,self.wht_percent)
        # Real Pay
        amount_pay = wht_coeff * self.amount
        residual_untaxed = untaxed_coeff * residual
        pay_ratio = amount_pay / residual
        amount_wht = pay_ratio * residual_untaxed * (self.wht_percent / 100)
        self.amount_wht = amount_wht
        return

    @api.model
    def _invoice_wht_coeff(self, invoice, wht_percent):
        full_amount_total = invoice.amount_total
        full_amount_untaxed = invoice.amount_untaxed
        full_amount_wht = full_amount_untaxed * (wht_percent / 100)
        full_amount_pay = full_amount_total - full_amount_wht
        wht_coeff = full_amount_total / full_amount_pay
        untaxed_coeff = full_amount_untaxed / full_amount_total
        return wht_coeff, untaxed_coeff

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands(
            'invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults:
            # WHT Account
            invoice = invoice_defaults[0]
            invoice_lines = invoice['invoice_line_ids']
            if not invoice_lines:
                return rec
            line = self.env['account.invoice.line'].browse(invoice_lines[0])
            tax = line.invoice_line_tax_ids.filtered("wht_tax")
            rec['wht_percent'] = tax.amount
            invoice = line.invoice_id
            account_id = invoice.type in ('out_invoice', 'in_invoice') and \
                tax.account_id.id or tax.refund_account_id.id
            rec['wht_account_id'] = account_id
            # Adjusted amount
            wht_coeff, _ = self._invoice_wht_coeff(invoice, rec['wht_percent'])
            rec['amount'] = rec['amount'] / wht_coeff
        return rec

    # Constrain

    # Onchange

    # CRUD methods

    # Action methods

    # Business methods
    def _create_payment_entry(self, amount):
        """ Adding Undue Tax and Tax line form invoice
            TODO: Not applicable for multi-currency
        """
        move = self.env['account.move']

        if self.amount_wht:
            move = self._create_payment_entry_wht(amount, -self.amount_wht)
        else:
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
                    move_line.with_context(check_move_validity=False).create(
                        undue_tax_dict)
                    # Due VAT line, change name and account_id
                    tax_dict = move_line.copy_data({
                        'move_id': move.id,
                        'name': tax.counterpart_tax_id.name,
                        'account_id': account_id,
                    })[0]
                    move_line.create(tax_dict)
        return move

    def _create_payment_entry_wht(self, amount, amount_wht):
        """ Specifically add wht_amount move line
        """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        debit, credit, amount_currency = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(
                amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(
            debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(
            self._get_counterpart_move_line_vals(self.invoice_ids))
        currency_id = self.currency_id != self.company_id.currency_id and \
            self.currency_id.id or False
        counterpart_aml_dict.update({
            'currency_id': currency_id
        })
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # WHT
        debit_wht, credit_wht, amount_currency_wht = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(
                amount_wht, self.currency_id, self.company_id.currency_id)
        wht_aml_dict = self._get_shared_move_line_vals(
            debit_wht, credit_wht, amount_currency_wht, move.id, False)
        wht_aml_dict.update(
            self._get_counterpart_move_line_vals(self.invoice_ids))
        wht_aml_dict.update({'currency_id': currency_id})
        wht_aml = aml_obj.create(wht_aml_dict)
        # Adding to total amount
        counterpart_aml += wht_aml
        amount_currency += amount_currency_wht
        amount += amount_wht
        credit += credit_wht
        debit += debit_wht
        # --

        # Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile':
            self.invoice_ids.register_payment(
                counterpart_aml, self.writeoff_account_id, self.journal_id)
        else:
            self.invoice_ids.register_payment(counterpart_aml)

        # Write counterpart lines
        liquidity_aml_dict = self._get_shared_move_line_vals(
            credit, debit, -amount_currency,
            move.id, False)
        liquidity_aml_dict.update(
            self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)

        move.post()

        # As we can't set account_id of withholding line before post()
        # It does block the reconcile of > 1 accont_id, so we do here after
        self._cr.execute("""
            UPDATE account_move_line SET account_id=%s WHERE id=%s
            """, (self.wht_account_id.id, wht_aml.id)
        )
        return move
