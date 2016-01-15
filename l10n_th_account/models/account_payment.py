# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_difference = fields.Monetary(
        store=True,
    )
    amount_wht = fields.Monetary(
        string='Withhold Amount',
        store=True,
        copy=False,
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

    @api.model
    def _compute_amount_wht(self):
        if len(self.invoice_ids) == 0:
            return
        assert len(self.invoice_ids) == 1, "WHT work with 1 invoice only"
        residual = self._compute_total_invoices_amount()
        if not residual:
            self.amount_wht = 0.0
            return
        invoice = self.invoice_ids[0]
        wht_coeff, untax_coeff = self._invoice_wht_coeff(invoice,
                                                         self.wht_percent)
        # Real Pay
        amount_pay = wht_coeff * self.amount
        residual_untaxed = untax_coeff * residual
        pay_ratio = amount_pay / residual
        amount_wht = pay_ratio * residual_untaxed * (self.wht_percent / 100)
        return amount_wht

    @api.model
    def _invoice_wht_coeff(self, invoice, wht_percent):
        full_amount_total = invoice.amount_total
        full_amount_untaxed = invoice.amount_untaxed
        full_amount_wht = full_amount_untaxed * (wht_percent / 100)
        full_amount_pay = full_amount_total - full_amount_wht
        wht_coeff = full_amount_total / full_amount_pay
        untax_coeff = full_amount_untaxed / full_amount_total
        return wht_coeff, untax_coeff


    # Constrain

    # Onchange
    @api.onchange('amount')
    def _onchange_amount(self):
        self.amount_wht = self._compute_amount_wht()

    @api.onchange('amount_wht')
    def _onchange_amount_wht(self):
        reconcile_amount_wht = self._compute_reconcile_amount_wht()
        # Do not allow > possible amount
        if self.amount_wht > reconcile_amount_wht:
            self.amount_wht = reconcile_amount_wht
        if self.amount_wht == reconcile_amount_wht and self.payment_difference:
            self.payment_difference_handling = 'reconcile'
        else:
            self.payment_difference_handling = 'open'
            self.amount_wht = self._compute_amount_wht()

    @api.onchange('payment_difference_handling')
    def _onchange_payment_difference_handling(self):
        reconcile_amount_wht = self._compute_reconcile_amount_wht()
        if self.payment_difference_handling == 'reconcile':
            self.amount_wht = reconcile_amount_wht
        else:
            self.amount_wht = self._compute_amount_wht()

    # CRUD methods
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

    # Action methods

    # Business methods
    @api.model
    def _create_undue_vat_move_line(self, move):
        for invoice in self.invoice_ids:
            if not invoice.move_id:
                continue
            # Find payment ratio
            invoice_total = invoice.amount_total
            amount_pay = abs(self.amount) + abs(self.amount_wht)
            if self.payment_difference_handling == 'reconcile':
                amount_pay += abs(self.payment_difference)
            ratio = amount_pay / invoice_total
            for move_line in invoice.move_id.line_ids:
                tax = move_line.tax_line_id
                account_id = invoice.type in ('out_invoice', 'in_invoice') \
                    and tax.counterpart_tax_id.account_id.id \
                    or tax.counterpart_tax_id.refund_account_id.id
                if tax.undue_tax:
                    # Undue VAT line, credit -> debit
                    undue_tax_dict = move_line.copy_data({
                        'move_id': move.id,
                        'payment_id': self.id,
                        'quantity': False,
                        'credit': move_line.debit * ratio,
                        'debit': move_line.credit * ratio,
                    })[0]
                    move_line.with_context(check_move_validity=False).create(
                        undue_tax_dict)
                    # Due VAT line, change name and account_id
                    tax_dict = move_line.copy_data({
                        'move_id': move.id,
                        'payment_id': self.id,
                        'quantity': False,
                        'name': tax.counterpart_tax_id.name,
                        'account_id': account_id,
                        'credit': move_line.credit * ratio,
                        'debit': move_line.debit * ratio,
                    })[0]
                    move_line.create(tax_dict)

    @api.model
    def _create_payment_entry(self, amount):
        """ Adding Undue Tax and Tax line form invoice
            TODO: Not applicable for multi-currency
        """
        # WITHHOLDING TAX
        if self.amount_wht:
            if self.payment_type == 'inbound':
                self._create_payment_entry_wht(-self.amount_wht)
            else:
                self._create_payment_entry_wht(self.amount_wht)

        move = super(AccountPayment, self)._create_payment_entry(amount)
        # UNDUE VAT
        self._create_undue_vat_move_line(move)
        return move

    @api.model
    def _create_payment_entry_wht(self, amount_wht):
        """ Specifically add wht_amount move line
        """
        aml_obj = self.env['account.move.line'].with_context(
            check_move_validity=False)
        debit_wht, credit_wht, amount_currency_wht = aml_obj.with_context(
            date=self.payment_date).compute_amount_fields(
                amount_wht, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        wht_aml_dict = self._get_shared_move_line_vals(
            debit_wht, credit_wht, amount_currency_wht, move.id, False)
        wht_aml_dict.update(
            self._get_counterpart_move_line_vals(self.invoice_ids))
        currency_id = self.currency_id != self.company_id.currency_id and \
            self.currency_id.id or False
        wht_aml_dict.update({'currency_id': currency_id,
                             'name': _('Withholding Tax')})
        wht_aml = aml_obj.create(wht_aml_dict)

        # Reconcile with the invoices
        self.invoice_ids.register_payment(wht_aml)

        # Write counterpart lines
        liquidity_aml_dict = self._get_shared_move_line_vals(
            credit_wht, debit_wht, -amount_currency_wht,
            move.id, False)
        liquidity_aml_dict.update(
            self._get_liquidity_move_line_vals(-amount_wht))
        liquidity_aml_dict.update({'account_id': self.wht_account_id.id,
                                   'name': _('Withholding Tax')})
        aml_obj.create(liquidity_aml_dict)

        move.post()
        return move

    @api.model
    def _compute_reconcile_amount_wht(self):
        invoice = self.invoice_ids[0]
        _, untax_coeff = self._invoice_wht_coeff(invoice, self.wht_percent)
        residual = self._compute_total_invoices_amount()
        residual_untaxed = untax_coeff * residual
        reconcile_amount_wht = residual_untaxed * (self.wht_percent / 100)
        return reconcile_amount_wht
