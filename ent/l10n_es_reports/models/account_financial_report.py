# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo.exceptions import UserError

from datetime import datetime


class AccountFinancialReportLine(models.Model):
    _inherit = 'account.financial.html.report.line'

    l10n_es_mod347_threshold = fields.Float("Mod.347 Partner Threshold", help="""
The threshold value, in EURO, to be applied on invoice journal items  grouped by partner in the Modelo 347 report.
Only the partners having a debit sum value strictly superior to the threshold over the fiscal year
will be taken into account in this report.
This feature is only supported/useful in spanish MOD347 report.""")

    def _parse_threshold_parameter(self, company, date):
        """ Parses the content of the l10n_es_mod347_threshold field, returning its
        value in company currency.
        """
        if self.l10n_es_mod347_threshold:
            amount = self.l10n_es_mod347_threshold
            threshold_currency = self.env['res.currency'].search([('name', '=', 'EUR')])

            if not threshold_currency:
                raise UserError(_("Currency %s, used for a threshold in this report, is either nonexistent or inactive. Please create or activate it." % threshold_currency.name))

            company_currency = self.env['res.company']._company_default_get().currency_id
            return threshold_currency._convert(amount, company_currency, company, date)

    def _get_with_statement(self, financial_report):
        if financial_report.l10n_es_reports_modelo_number == '347':
            if self.l10n_es_mod347_threshold:
                if self.groupby != 'partner_id':
                    raise UserError(_("Trying to use a groupby threshold for a line without grouping by partner_id isn't supported."))

                company = self.env['res.company'].browse(self.env.context['company_ids'][0])
                from_fiscalyear_dates = company.compute_fiscalyear_dates(datetime.strptime(self.env.context['date_from'], DEFAULT_SERVER_DATE_FORMAT))
                to_fiscalyear_dates = company.compute_fiscalyear_dates(datetime.strptime(self.env.context['date_to'], DEFAULT_SERVER_DATE_FORMAT))

                # ignore the threshold if from and to dates belong to different fiscal years
                if from_fiscalyear_dates == to_fiscalyear_dates:
                    sql_with = """WITH account_move_line
                                  AS (SELECT *
                                      FROM account_move_line where partner_id
                                      IN (SELECT partner_id
                                          FROM account_move_line
                                          WHERE date >= %s AND date <= %s
                                          AND invoice_id IS NOT NULL
                                          GROUP BY partner_id
                                          HAVING sum(debit) > %s
                                          )
                                      )
                               """
                    threshold_value = self._parse_threshold_parameter(company, from_fiscalyear_dates['date_to'])
                    params_sql = [from_fiscalyear_dates['date_from'].strftime(DEFAULT_SERVER_DATE_FORMAT), from_fiscalyear_dates['date_to'].strftime(DEFAULT_SERVER_DATE_FORMAT), str(threshold_value)]
                    return sql_with, params_sql

            # forbid cash basis for mod 347 in any case (for consistency)
            return '', []

        return super(AccountFinancialReportLine, self)._get_with_statement(financial_report)
