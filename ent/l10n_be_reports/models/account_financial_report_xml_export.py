# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import calendar
import json

class AccountFinancialReportXMLReportExport(models.TransientModel):
    _name = "account.financial.html.report.export"
    _description = "Financial Report XML Export"

    ask_restitution = fields.Boolean()
    ask_payment = fields.Boolean()
    client_nihil = fields.Boolean()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id, required=True)
    grid91 = fields.Monetary(string='Grid 91', currency_field='currency_id',
        help='La grille 91 ne concerne que les assujettis tenus au dépôt de déclarations mensuelles. Cette grille ne peut être complétée que pour la déclaration relative aux opérations du mois de décembre.')

    def print_xml(self):
        options = self.env.context.get('options')
        options['ask_restitution'] = self.ask_restitution
        options['ask_payment'] = self.ask_payment
        options['client_nihil'] = self.client_nihil
        options['grid91'] = self.grid91
        return {
                'type': 'ir_actions_account_report_download',
                'data': {'model': self.env.context.get('model'),
                         'options': json.dumps(options),
                         'output_format': 'xml',
                         'financial_id': self.env.context.get('id'),
                         }
                }

class AccountFinancialReportXMLExport(models.AbstractModel):
    _inherit = "account.financial.html.report"

    def _get_reports_buttons(self):
        buttons = super(AccountFinancialReportXMLExport, self)._get_reports_buttons()
        if self.id == self.env['ir.model.data'].xmlid_to_res_id('l10n_be_reports.account_financial_report_l10n_be_tva0'):
            buttons += [{'name': _('Export (XML)'), 'action': 'print_xml'}]
        return buttons

    def print_xml(self, options):
        # add options to context and return action to open transient model
        ctx = self.env.context.copy()
        ctx['options'] = options
        action = self.env.ref('l10n_be_reports.action_account_financial_report_export').read()[0]
        action.update({'context': ctx,})
        return action

    def get_xml(self, options):
        # Check
        if self.id != self.env['ir.model.data'].xmlid_to_res_id('l10n_be_reports.account_financial_report_l10n_be_tva0'):
            return super(AccountFinancialReportXMLExport, self).get_xml(options)
        company = self.env.user.company_id
        vat_no = company.partner_id.vat
        if not vat_no:
            raise UserError(_('No VAT number associated with your company.'))
        default_address = company.partner_id.address_get()
        address = self.env['res.partner'].browse(default_address.get("default")) or company.partner_id
        if not address.email:
            raise UserError(_('No email address associated with the company.'))
        if not address.phone:
            raise UserError(_('No phone associated with the company.'))

        # Compute xml
        list_of_tags = ['00', '01', '02', '03', '44', '45', '46', '47', '48', '49', '54', '55', '56', '57', '59', '61', '62', '63', '64', '71', '72', '81', '82', '83', '84', '85', '86', '87', '88', '91']
        vat_no = vat_no.replace(' ', '').upper()

        default_address = company.partner_id.address_get()
        address = self.env['res.partner'].browse(default_address.get("default", company.partner_id.id))

        issued_by = vat_no[:2]
        dt_from = options['date'].get('date_from')
        dt_to = options['date'].get('date_to')
        send_ref = str(company.partner_id.id) + str(dt_from[5:7]) + str(dt_to[:4])
        starting_month = dt_from[5:7]
        ending_month = dt_to[5:7]
        quarter = str(((int(starting_month) - 1) // 3) + 1)

        date_from = dt_from[0:7] + '-01'
        date_to = dt_to[0:7] + '-' + str(calendar.monthrange(int(dt_to[0:4]), int(ending_month))[1])
        ctx = self._set_context(options)
        ctx.update({'no_format': True, 'date_from': date_from, 'date_to': date_to})
        lines = self.with_context(ctx)._get_lines(options)

        data = {'client_nihil': options.get('client_nihil'), 'ask_restitution': options.get('ask_restitution', False), 'ask_payment': options.get('ask_payment', False)}

        file_data = {
                        'issued_by': issued_by,
                        'vat_no': vat_no,
                        'only_vat': vat_no[2:],
                        'cmpny_name': company.name,
                        'address': "%s %s" % (address.street or "", address.street2 or ""),
                        'post_code': address.zip or "",
                        'city': address.city or "",
                        'country_code': address.country_id and address.country_id.code or "",
                        'email': address.email or "",
                        'phone': address.phone.replace('.', '').replace('/', '').replace('(', '').replace(')', '').replace(' ', ''),
                        'send_ref': send_ref,
                        'quarter': quarter,
                        'month': starting_month,
                        'year': str(dt_to[:4]),
                        'client_nihil': (data['client_nihil'] and 'YES' or 'NO'),
                        'ask_restitution': (data['ask_restitution'] and 'YES' or 'NO'),
                        'ask_payment': (data['ask_payment'] and 'YES' or 'NO'),
                        'comments': self._get_report_manager(options).summary or '',
                     }

        data_of_file = """<?xml version="1.0"?>
<ns2:VATConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/VATConsignment" VATDeclarationsNbr="1">
    <ns2:VATDeclaration SequenceNumber="1" DeclarantReference="%(send_ref)s">
        <ns2:Declarant>
            <VATNumber xmlns="http://www.minfin.fgov.be/InputCommon">%(only_vat)s</VATNumber>
            <Name>%(cmpny_name)s</Name>
            <Street>%(address)s</Street>
            <PostCode>%(post_code)s</PostCode>
            <City>%(city)s</City>
            <CountryCode>%(country_code)s</CountryCode>
            <EmailAddress>%(email)s</EmailAddress>
            <Phone>%(phone)s</Phone>
        </ns2:Declarant>
        <ns2:Period>
    """ % (file_data)

        if starting_month != ending_month:
            # starting month and ending month of selected period are not the same
            # it means that the accounting isn't based on periods of 1 month but on quarters
            data_of_file += '\t\t<ns2:Quarter>%(quarter)s</ns2:Quarter>\n\t\t' % (file_data)
        else:
            data_of_file += '\t\t<ns2:Month>%(month)s</ns2:Month>\n\t\t' % (file_data)
        data_of_file += '\t<ns2:Year>%(year)s</ns2:Year>' % (file_data)
        data_of_file += '\n\t\t</ns2:Period>\n'
        data_of_file += '\t\t<ns2:Data>\t'
        cases_list = []
        currency_id = self.env.user.company_id.currency_id

        if options.get('grid91') and not currency_id.is_zero(options['grid91']):
            cases_list.append(('91', options['grid91']))

        for line in lines:
            if line['name'].startswith('91') and ending_month != 12:
                # the tax code 91 can only be send for the declaration of December
                continue
            if line['columns'][0].get('name', False) and not currency_id.is_zero(line['columns'][0].get('name')):
                for tag in list_of_tags:
                    if line['name'].startswith(tag + ' -'): # With ' -', we ensure that we don't take into account the children of the line (for example, we don't want to consider 46L and 46T, only the aggregate line 46)
                        tags_list = [x[0] for x in cases_list]
                        if tag in tags_list:
                            cases_list[tags_list.index(tag)] = (tag, cases_list[tags_list.index(tag)][1] + line['columns'][0].get('name'))
                        else:
                            cases_list.append((tag, line['columns'][0].get('name')))
                        del tag
        cases_list = sorted(cases_list, key=lambda a: a[0])
        for item in cases_list:
            grid_amount_data = {
                    'code': str(int(item[0])),
                    'amount': '%.2f' % abs(item[1]),
                    }
            data_of_file += '\n\t\t\t<ns2:Amount GridNumber="%(code)s">%(amount)s</ns2:Amount''>' % (grid_amount_data)

        data_of_file += '\n\t\t</ns2:Data>'
        data_of_file += '\n\t\t<ns2:ClientListingNihil>%(client_nihil)s</ns2:ClientListingNihil>' % (file_data)
        data_of_file += '\n\t\t<ns2:Ask Restitution="%(ask_restitution)s" Payment="%(ask_payment)s"/>' % (file_data)
        data_of_file += '\n\t\t<ns2:Comment>%(comments)s</ns2:Comment>' % (file_data)
        data_of_file += '\n\t</ns2:VATDeclaration> \n</ns2:VATConsignment>'

        return data_of_file
