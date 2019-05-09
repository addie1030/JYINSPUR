# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.tools import pycompat


class ReportL10nNLIntrastat(models.AbstractModel):
    _name = 'l10n.nl.report.intrastat'
    _description = 'Intrastat Report (ICP)'
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_year'}

    def _get_columns_name(self, options):
        return [
            {'name': _('Partner')},
            {'name': _('VAT')},
            {'name': _('Country')},
            {'name': _('Amount Product'), 'class': 'number'},
            {'name': _('Amount Service'), 'class': 'number'},
        ]

    def _get_report_name(self):
        return _('Intrastat (ICP)')

    @api.model
    def _get_lines(self, options, line_id=None):
        lines = []
        company_id = self.env.user.company_id

        country_ids = (self.env.ref('base.europe').country_ids - company_id.country_id).ids

        query = """
            SELECT l.partner_id, p.name, p.vat, c.code,
                   SUM(CASE WHEN tt.account_account_tag_id = %(product_tag)s THEN l.credit - l.debit ELSE 0 END) as amount_product,
                   SUM(CASE WHEN tt.account_account_tag_id = %(service_tag)s THEN l.credit - l.debit ELSE 0 END) as amount_service
            FROM account_move_line l
            LEFT JOIN res_partner p ON l.partner_id = p.id AND p.customer = true
            LEFT JOIN res_country c ON p.country_id = c.id
            LEFT JOIN account_move_line_account_tax_rel amlt ON l.id = amlt.account_move_line_id
            LEFT JOIN account_tax_account_tag tt on amlt.account_tax_id = tt.account_tax_id
            WHERE tt.account_account_tag_id IN (%(product_tag)s, %(service_tag)s)
            AND c.id IN %(country_ids)s
            AND l.date >= %(date_from)s
            AND l.date <= %(date_to)s
            AND l.company_id IN %(company_ids)s
            GROUP BY l.partner_id, p.name, p.vat, c.code
            ORDER BY p.name
        """

        params = {
            'product_tag': self.env.ref('l10n_nl.tag_nl_40').id,
            'service_tag': self.env.ref('l10n_nl.tag_nl_41').id,
            'country_ids': tuple(country_ids),
            'date_from': self._context['date_from'],
            'date_to': self._context['date_to'],
            'company_ids': tuple(self._context.get('company_ids')),
        }
        self.env.cr.execute(query, params)

        # Add lines
        total = 0
        for result in self.env.cr.dictfetchall():
            total += result['amount_product'] + result['amount_service']
            lines.append({
                'id': result['partner_id'],
                'caret_options': 'res.partner',
                'model': 'res.partner',
                'name': result['name'],
                'level': 2,
                'columns': [
                    {'name': v} for v in [
                        result['vat'], result['code'],
                        self.format_value(result['amount_product']), self.format_value(result['amount_service'])
                    ]
                ],
                'unfoldable': False,
                'unfolded': False,
            })

        if lines:
            lines.append({
                'id': 'total_line',
                'class': 'total',
                'name': _('Total'),
                'level': 2,
                'columns': [
                    {'name': v}
                    for v in ['', '', '(product + service)', self.format_value(total)]
                ],
                'unfoldable': False,
                'unfolded': False,
            })

        return lines
