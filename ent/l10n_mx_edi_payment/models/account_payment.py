from datetime import datetime

from lxml.etree import tostring
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT

CFDI_XSLT_CADENA = 'l10n_mx_edi/data/3.3/cadenaoriginal.xslt'


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_edi_expedition_date = fields.Date(
        string='Expedition Date', copy=False,
        help='Save the expedition date of the CFDI that according to the SAT '
        'documentation must be the date when the CFDI is issued.')
    l10n_mx_edi_time_payment = fields.Char(
        string='Time payment', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current Mexico central time")

    @api.multi
    def _l10n_mx_edi_create_cfdi_payment(self):
        res = super(AccountPayment, self)._l10n_mx_edi_create_cfdi_payment()
        date_mx = self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime() # noqa
        if not self.l10n_mx_edi_expedition_date:
            self.l10n_mx_edi_expedition_date = date_mx.date()
        if not self.l10n_mx_edi_time_payment:
            self.l10n_mx_edi_time_payment = date_mx.strftime(
                DEFAULT_SERVER_TIME_FORMAT)
        time_invoice = datetime.strptime(self.l10n_mx_edi_time_payment, DEFAULT_SERVER_TIME_FORMAT).time()
        cfdi_date = datetime.combine(
            fields.Datetime.from_string(self.l10n_mx_edi_expedition_date),
            time_invoice).strftime('%Y-%m-%dT%H:%M:%S')
        if res.get('error'):
            return res
        cfdi = res.pop('cfdi')
        xml = self.l10n_mx_edi_get_xml_etree(cfdi)
        certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        xml.set('Fecha',  cfdi_date)
        cadena = self.env['account.invoice'].l10n_mx_edi_generate_cadena(
            CFDI_XSLT_CADENA, xml)
        xml.attrib['Sello'] = certificate_id.sudo().get_encrypted_cadena(cadena) # noqa
        return {'cfdi': tostring(xml, pretty_print=True, xml_declaration=True,
                                 encoding='UTF-8')}

    def action_draft(self):
        self.filtered(lambda r: r.l10n_mx_edi_is_required()).write({
            'l10n_mx_edi_expedition_date': False,
            'l10n_mx_edi_time_payment': False,
        })
        return super(AccountPayment, self).action_draft()
