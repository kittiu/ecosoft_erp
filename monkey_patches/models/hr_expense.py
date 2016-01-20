# -*- coding: utf-8 -*-
from openerp import models, api
from openerp.exceptions import UserError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    # https://github.com/odoo/odoo/issues/10543
    @api.multi
    def _move_line_get(self):
        account_move = []
        for expense in self:
            if expense.product_id:
                account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
                if not account:
                    raise UserError(_("No Expense account found for the product %s (or for it's category), please configure one.") % (expense.product_id.name))
            else:
                account = self.env['ir.property'].with_context(force_company=expense.company_id.id).get('property_account_expense_categ_id', 'product.category')
                if not account:
                    raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
            move_line = {
                    'type': 'src',
                    'name': expense.name.split('\n')[0][:64],
                    'price_unit': expense.unit_amount,
                    'quantity': expense.quantity,
                    'price': expense.total_amount,
                    'account_id': account.id,
                    'product_id': expense.product_id.id,
                    'uom_id': expense.product_uom_id.id,
                    'analytic_account_id': expense.analytic_account_id.id,
                }
            account_move.append(move_line)

            # Calculate tax lines and adjust base line
            taxes = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            account_move[-1]['price'] = taxes['total_excluded']
            # https://github.com/odoo/odoo/issues/10543
            account_move[-1]['tax_ids'] = expense.tax_ids.ids
            # --
            for tax in taxes['taxes']:
                account_move.append({
                    'type': 'tax',
                    'name': tax['name'],
                    'price_unit': tax['amount'],
                    'quantity': 1,
                    'price': tax['amount'],
                    'account_id': tax['account_id'] or move_line['account_id'],
                    'tax_line_id': tax['id'],
                })
        return account_move

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
