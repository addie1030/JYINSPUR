# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta


class IntrastatReport(models.AbstractModel):
    _inherit = 'account.intrastat.report'

    def _get_reports_buttons(self):
        res = super(IntrastatReport, self)._get_reports_buttons()
        if self.env.user.company_id.country_id == self.env.ref('base.be'):
            res += [{'name': _('Export (XML)'), 'action': 'print_xml'}]
        return res

    @api.model
    def get_xml(self, options):
        ''' Create the xml export.

        :param options: The report options.
        :return: The xml export file content.
        '''
        date_from, date_to, journal_ids, incl_arrivals, incl_dispatches, extended = self._decode_options(options)
        date_1 = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        date_2 = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
        a_day = timedelta(days=1)
        if date_1.day != 1 or (date_2 - date_1) > timedelta(days=30) or date_1.month == (date_2 + a_day).month:
            raise UserError(_('Wrong date range selected. The intrastat declaration export has to be done monthly.'))
        date = date_1.strftime('%Y-%m')

        company = self.env.user.company_id
        if not company.company_registry:
            raise UserError(_('Missing company registry information on the company'))

        cache = {}

        # create in_vals corresponding to invoices with cash-in
        in_vals = []
        if incl_arrivals:
            query, params = self._prepare_query(
                date_from, date_to, journal_ids=journal_ids, invoice_types=('in_invoice', 'out_refund'))
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()
            in_vals = self._fill_missing_values(query_res, cache)

        # create out_vals corresponding to invoices with cash-out
        out_vals = []
        if incl_dispatches:
            query, params = self._prepare_query(
                date_from, date_to, journal_ids=journal_ids, invoice_types=('out_invoice', 'in_refund'))
            self._cr.execute(query, params)
            query_res = self._cr.dictfetchall()
            out_vals = self._fill_missing_values(query_res, cache)

        return self.env.ref('l10n_be_intrastat.intrastat_report_export_xml').render({
            'company': company,
            'in_vals': in_vals,
            'out_vals': out_vals,
            'extended': extended,
            'date': date,
            '_get_reception_code': self._get_reception_code,
            '_get_reception_form': self._get_reception_form,
            '_get_expedition_code': self._get_expedition_code,
            '_get_expedition_form': self._get_expedition_form,
        })

    def _get_reception_code(self, extended):
        return 'EX19E' if extended else 'EX19S'

    def _get_reception_form(self, extended):
        return 'EXF19E' if extended else 'EXF19S'

    def _get_expedition_code(self, extended):
        return 'EX29E' if extended else 'EX29S'

    def _get_expedition_form(self, extended):
        return 'EXF29E' if extended else 'EXF29S'
