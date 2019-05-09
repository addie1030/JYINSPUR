# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class IntrastatReport(models.AbstractModel):
    _name = 'account.sales.report'
    _description = 'EC Sales List'
    _inherit = 'account.report'

    filter_date = {'date_from': '', 'date_to': '', 'filter': 'this_month'}
    filter_journals = True
    filter_multi_company = None

    def _get_filter_journals(self):
        #only show sale/purchase journals
        return self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id), ('type', '=', 'sale')], order="company_id, name")

    def _get_columns_name(self, options):
        return [
            {'name': ''},
            {'name': _('VAT')},
            {'name': _('Country Code')},
            {'name': _('Value'), 'class': 'number'},
        ]

    @api.model
    def _prepare_query(self, options):
        query = """
            SELECT
                cpartner.id AS partner_id,
                cpartner.name AS partner_name,
                cpartner.vat AS partner_vat,
                country.code AS country_code,
                inv.currency_id AS currency_id,
                inv.date AS date,
                inv.amount_total_signed AS value
            FROM account_invoice inv
                LEFT JOIN res_partner partner ON inv.partner_id = partner.id
                LEFT JOIN res_company company ON inv.company_id = company.id
                LEFT JOIN res_partner company_partner ON company_partner.id = company.partner_id
                LEFT JOIN res_partner cpartner ON partner.commercial_partner_id = cpartner.id
                LEFT JOIN res_country country ON cpartner.country_id = country.id
            WHERE inv.state in ('open', 'in_payment', 'paid')
                AND country.intrastat = TRUE
                AND company_partner.country_id != country.id
                AND company.id = %s
                AND coalesce(inv.date, inv.date_invoice) >= %s
                AND coalesce(inv.date, inv.date_invoice) <= %s
                AND inv.type in ('out_invoice', 'out_refund')
                AND partner.vat IS NOT NULL
                AND inv.journal_id IN %s
        """
        # Date range
        params = [self.env.user.company_id.id, options['date']['date_from'], options['date']['date_to']]

        # Filter on selected journals
        journal_ids = self.env['account.journal'].search([('type', 'in', ('sale', 'purchase'))]).ids
        if options.get('journals'):
            journal_ids = [c['id'] for c in options['journals'] if c.get('selected')] or journal_ids
        params.append(tuple(journal_ids))

        return query, params

    @api.model
    def _create_sales_report_line(self, options, vals):
        return {
            'id': vals['partner_id'],
            'caret_options': 'res.partner',
            'model': 'res.partner',
            'name': vals['partner_name'],
            'columns': [{'name': c} for c in [
                vals['partner_vat'], vals['country_code'], self.format_value(vals['value'])]
            ],
            'level': 2,
        }

    @api.model
    def _get_lines(self, options, line_id=None):
        self.env['account.invoice.line'].check_access_rights('read')
        query, params = self._prepare_query(options)

        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()

        company_currency = self.env.user.company_id.currency_id
        currency_cache = dict((r.id, r) for r in self.env['res.currency'].search([('active', '=', True)]))
        partners_values = {}
        total_value = 0

        # Aggregate total amount for each partner.
        # Take care of the multi-currencies.
        for vals in query_res:
            if vals['currency_id'] in currency_cache:
                currency = currency_cache[vals['currency_id']]
            else:
                currency = currency_cache[vals['currency_id']] = self.env['res.currency'].browse(vals['currency_id'])

            if currency != company_currency:
                vals['value'] = currency._convert(vals['value'], company_currency, self.env.user.company_id, vals['date'])

            if vals['partner_name'] not in partners_values:
                partners_values[vals['partner_name']] = vals
            else:
                partners_values[vals['partner_name']]['value'] += vals['value']
            total_value += vals['value']

        lines = [self._create_sales_report_line(options, partners_values[partner_name]) for partner_name in sorted(partners_values)]

        # Create total line
        lines.append({
            'id': 0,
            'name': _('Total'),
            'class': 'total',
            'level': 2,
            'columns': [{'name': v} for v in [self.format_value(total_value)]],
            'colspan': 3,
        })
        return lines

    @api.model
    def _get_report_name(self):
        return _('EC Sales List')
