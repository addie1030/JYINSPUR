# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo import release

from datetime import datetime


class IntrastatReport(models.AbstractModel):
    _inherit = 'account.intrastat.report'

    def _get_reports_buttons(self):
        res = super(IntrastatReport, self)._get_reports_buttons()
        if self.env.user.company_id.country_id == self.env.ref('base.nl'):
            res += [{'name': _('Export (CBS)'), 'action': 'print_csv'}]
        return res

    def print_csv(self, options):
        action = self.print_xml(options)
        action['data']['output_format'] = 'csv'
        return action

    @api.model
    def get_csv(self, options):
        ''' Export the Centraal Bureau voor de Statistiek (CBS) file.

        Documentation found in:
        https://www.cbs.nl/en-gb/deelnemers%20enquetes/overzicht/bedrijven/onderzoek/lopend/international-trade-in-goods/idep-code-lists

        :param options: The report options.
        :return:        The content of the file as str.
        '''
        # Fetch data.
        self.env['account.invoice.line'].check_access_rights('read')

        company = self.env.user.company_id
        date_from, date_to, journal_ids, incl_arrivals, incl_dispatches, extended = self._decode_options(options)

        invoice_types = []
        if incl_arrivals:
            invoice_types += ['in_invoice', 'out_refund']
        if incl_dispatches:
            invoice_types += ['out_invoice', 'in_refund']

        query, params = self._prepare_query(date_from, date_to, journal_ids, invoice_types=invoice_types)

        self._cr.execute(query, params)
        query_res = self._cr.dictfetchall()
        line_map = dict((l.id, l) for l in self.env['account.invoice.line'].browse(res['id'] for res in query_res))

        # Create csv file content.
        vat = company.vat
        now = datetime.now()
        registration_number = company.l10n_nl_cbs_reg_number or ''
        software_version = release.version

        # The software_version looks like saas~11.1+e but we have maximum 5 characters allowed
        software_version = software_version.replace('saas~', '').replace('+e', '').replace('alpha', '')

        # HEADER LINE
        file_content = ''.join([
            '9801',                                                             # Record type           length=4
            vat and vat[2:].replace(' ', '').ljust(12) or ''.ljust(12),         # VAT number            length=12
            date_from[:4] + date_from[5:7],                                     # Review perior         length=6
            (company.name or '').ljust(40),                                     # Company name          length=40
            registration_number.ljust(6),                                       # Registration number   length=6
            software_version.ljust(5),                                          # Version number        length=5
            now.strftime('%Y%m%d'),                                             # Creation date         length=8
            now.strftime('%H%M%S'),                                             # Creation time         length=6
            company.phone and \
            company.phone.replace(' ', '')[:15].ljust(15) or ''.ljust(15),      # Telephone number      length=15
            ''.ljust(13),                                                       # Reserve               length=13
        ]) + '\n'

        # CONTENT LINES
        i = 1
        for res in query_res:
            line = line_map[res['id']]
            inv = line.invoice_id
            country_dest_code = inv.partner_id.country_id and inv.partner_id.country_id.code or ''
            country_origin_code = inv.intrastat_country_id and inv.intrastat_country_id.code or ''
            num = len(inv.number) < 8 and inv.number or inv.number[:8]
            mass = line.product_id and line.quantity * line.product_id.weight or 0
            transaction_period = str(inv.date_invoice.year) + str(inv.date_invoice.month).rjust(2, '0')
            file_content += ''.join([
                transaction_period,                                             # Transaction period    length=6
                res['commodity_code'] or '7',                                   # Commodity flow        length=1
                vat and vat[2:].replace(' ', '').ljust(12) or ''.ljust(12),     # VAT number            length=12
                str(i).zfill(5),                                                # Line number           length=5
                country_origin_code.ljust(3),                                   # Country of origin     length=3
                country_dest_code.ljust(3),                                     # Destination country   length=3
                res['invoice_transport'] or '3',                                # Mode of transport     length=1
                '0',                                                            # Container             length=1
                '00',                                                           # Traffic region/port   length=2
                '00',                                                           # Statistical procedure length=2
                res['transaction_code'] or '1',                                 # Transaction           length=1
                (res['commodity_code'] or '')[:8].ljust(8),                     # Commodity code        length=8
                '00',                                                           # Taric                 length=2
                mass >= 0 and '+' or '-',                                       # Mass sign             length=1
                str(int(mass)).zfill(10),                                       # Mass                  length=10
                '+',                                                            # Supplementary sign    length=1
                '0000000000',                                                   # Supplementary unit    length=10
                inv.amount_total_signed >= 0 and '+' or '-',                    # Invoice sign          length=1
                str(int(line.price_subtotal)).zfill(10),                        # Invoice value         length=10
                '+',                                                            # Statistical sign      length=1
                '0000000000',                                                   # Statistical value     length=10
                ('%s%s' % (num, str(i).zfill(2))).ljust(10),                    # Administration number length=10
                ''.ljust(3),                                                    # Reserve               length=3
                ' ',                                                            # Correction items      length=1
                '000',                                                          # Preference            length=3
                ''.ljust(7),                                                    # Reserve               length=7
            ]) + '\n'
            i += 1

        # FOOTER LINE
        file_content += ''.join([
            '9899',                                                             # Record type           length=4
            ''.ljust(111)                                                       # Reserve               length=111
        ])

        return file_content
