# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import markupsafe

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, html2plaintext, plaintext2html


class AccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'
  


    def _get_followup_report_lines(self, options):
        """
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.sorted().filtered(lambda aml: not aml.currency_id.is_zero(aml.amount_residual_currency)):
            if l.company_id in self.env.company._accessible_branches() and not l.blocked:
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                invoice_date = {
                    'name': format_date(self.env, aml.move_id.invoice_date or aml.date, lang_code=lang_code),
                    'class': 'date',
                    'style': 'white-space:nowrap;text-align:left;',
                    'template': 'account_followup.line_template',
                }
                date_due = format_date(self.env, aml.date_maturity or aml.move_id.invoice_date or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                date_due = {
                    'name': date_due, 'class': 'date',
                    'style': 'white-space:nowrap;text-align:left;',
                    'template': 'account_followup.line_template',
                }
                if is_overdue:
                    date_due['style'] += 'color: red;'
                if is_payment:
                    date_due = ''
                move_line_name = {
                    'name': self._followup_report_format_aml_name(aml.name, aml.move_id.ref),
                    'style': 'text-align:left; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                amount = {
                    'name': formatLang(self.env, amount, currency_obj=currency),
                    'style': 'text-align:right; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                line_num += 1
                invoice_origin = aml.move_id.invoice_origin or ''
                if len(invoice_origin) > 43:
                    invoice_origin = invoice_origin[:40] + '...'
                invoice_origin = {
                    'name': invoice_origin,
                    'style': 'text-align:center; white-space:normal;',
                    'template': 'account_followup.line_template',
                }
                columns = [
                    invoice_date,
                    date_due,
                    invoice_origin,
                    move_line_name,
                    amount,
                ]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [isinstance(v, dict) and v or {'name': v, 'template': 'account_followup.line_template'} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1

            cols = \
                [{
                    'name': v,
                    'template': 'account_followup.line_template',
                } for v in [''] * 3] + \
                [{
                    'name': v,
                    'style': 'text-align:right; white-space:normal; font-weight: bold;',
                    'template': 'account_followup.line_template',
                } for v in [total >= 0 and _('Total Due') or '', total_due]]

            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'style': 'border-top-style: double',
                'unfoldable': False,
                'level': 3,
                'columns': cols,
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1

                cols = \
                    [{
                        'name': v,
                        'template': 'account_followup.line_template',
                    } for v in [''] * 3] + \
                    [{
                        'name': v,
                        'style': 'text-align:right; white-space:normal; font-weight: bold;',
                        'template': 'account_followup.line_template',
                    } for v in [_('Total Overdue'), total_issued]]

                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 3,
                    'columns': cols,
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{'template': 'account_followup.line_template'} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()

        # Catch negative numbers when present
        for line in lines:
            for col in line['columns']:
                if self.env.company.currency_id.compare_amounts(col.get('no_format', 0.0), 0.0) == -1:
                    col['class'] = 'number color-red'

        return lines

