# -*- coding: utf-8 -*-

import base64
from itertools import groupby
import re
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from io import BytesIO
import requests
from pytz import timezone

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client

from odoo import _, api, fields, models, tools
from odoo.tools.xml_utils import _check_with_xsd
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools import float_round
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr

CFDI_TEMPLATE_33 = 'l10n_mx_edi.cfdiv33'
CFDI_XSLT_CADENA = 'l10n_mx_edi/data/%s/cadenaoriginal.xslt'
CFDI_XSLT_CADENA_TFD = 'l10n_mx_edi/data/xslt/3.3/cadenaoriginal_TFD_1_1.xslt'
# Mapped from original SAT state to l10n_mx_edi_sat_status selection value
# https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl
CFDI_SAT_QR_STATE = {
    'No Encontrado': 'not_found',
    'Cancelado': 'cancelled',
    'Vigente': 'valid',
}

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_list_html(array):
    '''Convert an array of string to a html list.
    :param array: A list of strings
    :return: an empty string if not array, an html list otherwise.
    '''
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    l10n_mx_edi_pac_status = fields.Selection(
        selection=[
            ('retry', 'Retry'),
            ('to_sign', 'To sign'),
            ('signed', 'Signed'),
            ('to_cancel', 'To cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='PAC status',
        help='Refers to the status of the invoice inside the PAC.',
        readonly=True,
        copy=False)
    l10n_mx_edi_sat_status = fields.Selection(
        selection=[
            ('none', 'State not defined'),
            ('undefined', 'Not Synced Yet'),
            ('not_found', 'Not Found'),
            ('cancelled', 'Cancelled'),
            ('valid', 'Valid'),
        ],
        string='SAT status',
        help='Refers to the status of the invoice inside the SAT system.',
        readonly=True,
        copy=False,
        required=True,
        track_visibility='onchange',
        default='undefined')
    l10n_mx_edi_cfdi_name = fields.Char(string='CFDI name', copy=False, readonly=True,
        help='The attachment name of the CFDI.')
    l10n_mx_edi_partner_bank_id = fields.Many2one('res.partner.bank',
        string='Partner bank',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('partner_id', '=', partner_id)]",
        help='The bank account the client will pay from. Leave empty if '
        'unkown and the XML will show "Unidentified".')
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
        string='Payment Way',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Indicates the way the invoice was/will be paid, where the '
        'options could be: Cash, Nominal Check, Credit Card, etc. Leave empty '
        'if unkown and the XML will show "Unidentified".',
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros',
                                          raise_if_not_found=False))
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True,
        help='Folio in electronic invoice, is returned by SAT when send to stamp.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi = fields.Binary(string='Cfdi content', copy=False, readonly=True,
        help='The cfdi xml content encoded in base64.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(string='Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(string='Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_amount = fields.Monetary(string='Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one('l10n_mx_edi.certificate',
        string='Certificate', copy=False, readonly=True,
        help='The certificate used during the generation of the cfdi.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_time_invoice = fields.Char(
        string='Time invoice', readonly=True, copy=False,
        states={'draft': [('readonly', False)]},
        help="Keep empty to use the current México central time")
    l10n_mx_edi_usage = fields.Selection([
        ('G01', 'Acquisition of merchandise'),
        ('G02', 'Returns, discounts or bonuses'),
        ('G03', 'General expenses'),
        ('I01', 'Constructions'),
        ('I02', 'Office furniture and equipment investment'),
        ('I03', 'Transportation equipment'),
        ('I04', 'Computer equipment and accessories'),
        ('I05', 'Dices, dies, molds, matrices and tooling'),
        ('I06', 'Telephone communications'),
        ('I07', 'Satellite communications'),
        ('I08', 'Other machinery and equipment'),
        ('D01', 'Medical, dental and hospital expenses.'),
        ('D02', 'Medical expenses for disability'),
        ('D03', 'Funeral expenses'),
        ('D04', 'Donations'),
        ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
        ('D06', 'Voluntary contributions to SAR'),
        ('D07', 'Medical insurance premiums'),
        ('D08', 'Mandatory School Transportation Expenses'),
        ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
        ('D10', 'Payments for educational services (Colegiatura)'),
        ('P01', 'To define'),
    ], 'Usage', default='P01',
        help='Used in CFDI 3.3 to express the key to the usage that will '
        'gives the receiver to this invoice. This value is defined by the '
        'customer. \nNote: It is not cause for cancellation if the key set is '
        'not the usage that will give the receiver of the document.')
    l10n_mx_edi_origin = fields.Char(
        string='CFDI Origin', copy=False,
        help='In some cases like payments, credit notes, debit notes, '
        'invoices re-signed or invoices that are redone due to payment in '
        'advance will need this field filled, the format is: \nOrigin Type|'
        'UUID1, UUID2, ...., UUIDn.\nWhere the origin type could be:\n'
        u'- 01: Nota de crédito\n'
        u'- 02: Nota de débito de los documentos relacionados\n'
        u'- 03: Devolución de mercancía sobre facturas o traslados previos\n'
        u'- 04: Sustitución de los CFDI previos\n'
        '- 05: Traslados de mercancias facturados previamente\n'
        '- 06: Factura generada por los traslados previos\n'
        u'- 07: CFDI por aplicación de anticipo')

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        '''Retrieve all the cfdi attachments generated for this invoice.

        :return: An ir.attachment recordset
        '''
        self.ensure_one()
        if not self.l10n_mx_edi_cfdi_name:
            return []
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', self.l10n_mx_edi_cfdi_name)]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def l10n_mx_edi_retrieve_last_attachment(self):
        attachment_ids = self.l10n_mx_edi_retrieve_attachments()
        return attachment_ids and attachment_ids[0] or None

    @api.model
    def l10n_mx_edi_get_xml_etree(self, cfdi=None):
        '''Get an objectified tree representing the cfdi.
        If the cfdi is not specified, retrieve it from the attachment.

        :param cfdi: The cfdi as string
        :return: An objectified tree
        '''
        #TODO helper which is not of too much help and should be removed
        self.ensure_one()
        if cfdi is None and self.l10n_mx_edi_cfdi:
            cfdi = base64.decodestring(self.l10n_mx_edi_cfdi)
        return fromstring(cfdi) if cfdi else None

    @api.model
    def l10n_mx_edi_get_payment_method_cfdi(self):
        self.ensure_one()
        cfdi = self.l10n_mx_edi_get_xml_etree()
        return cfdi.get('MetodoPago') if cfdi is not None else None

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        '''Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    @api.model
    def _get_l10n_mx_edi_cadena(self):
        self.ensure_one()
        #get the xslt path
        xslt_path = CFDI_XSLT_CADENA_TFD
        #get the cfdi as eTree
        cfdi = base64.decodestring(self.l10n_mx_edi_cfdi)
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        cfdi = self.l10n_mx_edi_get_tfd_etree(cfdi)
        #return the cadena
        return self.l10n_mx_edi_generate_cadena(xslt_path, cfdi)

    @api.model
    def l10n_mx_edi_generate_cadena(self, xslt_path, cfdi_as_tree):
        '''Generate the cadena of the cfdi based on an xslt file.
        The cadena is the sequence of data formed with the information contained within the cfdi.
        This can be encoded with the certificate to create the digital seal.
        Since the cadena is generated with the invoice data, any change in it will be noticed resulting in a different
        cadena and so, ensure the invoice has not been modified.

        :param xslt_path: The path to the xslt file.
        :param cfdi_as_tree: The cfdi converted as a tree
        :return: A string computed with the invoice data called the cadena
        '''
        xslt_root = etree.parse(tools.file_open(xslt_path))
        return str(etree.XSLT(xslt_root)(cfdi_as_tree))

    @api.model
    def l10n_mx_edi_is_customer_address_required(self):
        '''Look in the customer address to know if enough address information can be found to justify the creation
         of an address block in the xml.

        :return: True if at least one required field is found.
        '''
        self.ensure_one()
        partner_id = self.partner_id.commercial_partner_id
        if self.partner_id.type == 'invoice':
            partner_id = self.partner_id
        address_fields = ['street_name',
                          'street_number',
                          'street_number2',
                          'l10n_mx_edi_colony',
                          'l10n_mx_edi_locality',
                          'city',
                          'state_id',
                          'country_id',
                          'zip']
        for field in address_fields:
            if getattr(partner_id, field):
                return True
        return False

    @api.multi
    def l10n_mx_edi_amount_to_text(self):
        """Method to transform a float amount to text words
        E.g. 100 - ONE HUNDRED
        :returns: Amount transformed to words mexican format for invoices
        :rtype: str
        """
        self.ensure_one()
        currency = self.currency_id.name.upper()
        # M.N. = Moneda Nacional (National Currency)
        # M.E. = Moneda Extranjera (Foreign Currency)
        currency_type = 'M.N' if currency == 'MXN' else 'M.E.'
        # Split integer and decimal part
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = round(amount_d, 2)
        amount_d = int(round(amount_d * 100, 2))
        words = self.currency_id.with_context(lang=self.partner_id.lang or 'es_ES').amount_to_text(amount_i).upper()
        invoice_words = '%(words)s %(amount_d)02d/100 %(curr_t)s' % dict(
            words=words, amount_d=amount_d, curr_t=currency_type)
        return invoice_words

    @api.multi
    def l10n_mx_edi_is_required(self):
        self.ensure_one()
        return (self.type in ('out_invoice', 'out_refund') and
                self.company_id.country_id == self.env.ref('base.mx'))

    @api.multi
    def l10n_mx_edi_log_error(self, message):
        self.ensure_one()
        self.message_post(body=_('Error during the process: %s') % message, subtype='account.mt_invoice_validated')

    # -------------------------------------------------------------------------
    # SAT/PAC service methods
    # -------------------------------------------------------------------------

    @api.model
    def _l10n_mx_edi_solfact_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        url = 'https://testing.solucionfactible.com/ws/services/Timbrado?wsdl'\
            if test else 'https://solucionfactible.com/ws/services/Timbrado?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'testing@solucionfactible.com' if test else username,
            'password': 'timbrado.SF.16672' if test else password,
        }

    @api.multi
    def _l10n_mx_edi_solfact_sign(self, pac_info):
        '''SIGN for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            cfdi = inv.l10n_mx_edi_cfdi.decode('UTF-8')
            try:
                client = Client(url, timeout=20)
                response = client.service.timbrar(username, password, cfdi, False)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            res = response.resultados
            msg = getattr(res[0] if res else response, 'mensaje', None)
            code = getattr(res[0] if res else response, 'status', None)
            xml_signed = getattr(res[0] if res else response, 'cfdiTimbrado', None)
            inv._l10n_mx_edi_post_sign_process(
                xml_signed.encode('utf-8') if xml_signed else None, code, msg)

    @api.multi
    def _l10n_mx_edi_solfact_cancel(self, pac_info):
        '''CANCEL for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            uuids = [inv.l10n_mx_edi_cfdi_uuid]
            certificate_id = inv.l10n_mx_edi_cfdi_certificate_id.sudo()
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            key_password = certificate_id.password
            try:
                client = Client(url, timeout=20)
                response = client.service.cancelar(username, password, uuids, cer_pem.replace(
                    '\n', ''), key_pem, key_password)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            res = response.resultados
            code = getattr(res[0], 'statusUUID', None) if res else getattr(response, 'status', None)
            cancelled = code in ('201', '202')  # cancelled or previously cancelled
            # no show code and response message if cancel was success
            msg = '' if cancelled else getattr(res[0] if res else response, 'mensaje', None)
            code = '' if cancelled else code
            inv._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    @api.multi
    def _l10n_mx_edi_finkok_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        if service_type == 'sign':
            url = 'http://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/stamp.wsdl'
        else:
            url = 'http://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/cancel.wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'cfdi@vauxoo.com' if test else username,
            'password': 'vAux00__' if test else password,
        }

    @api.multi
    def _l10n_mx_edi_finkok_sign(self, pac_info):
        '''SIGN for Finkok.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            cfdi = [inv.l10n_mx_edi_cfdi.decode('UTF-8')]
            try:
                client = Client(url, timeout=20)
                response = client.service.stamp(cfdi, username, password)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            code = 0
            msg = None
            if response.Incidencias:
                code = getattr(response.Incidencias[0][0], 'CodigoError', None)
                msg = getattr(response.Incidencias[0][0], 'MensajeIncidencia', None)
            xml_signed = getattr(response, 'xml', None)
            if xml_signed:
                xml_signed = base64.b64encode(xml_signed.encode('utf-8'))
            inv._l10n_mx_edi_post_sign_process(xml_signed, code, msg)

    @api.multi
    def _l10n_mx_edi_finkok_cancel(self, pac_info):
        '''CANCEL for Finkok.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            uuid = inv.l10n_mx_edi_cfdi_uuid
            certificate_id = inv.l10n_mx_edi_cfdi_certificate_id.sudo()
            company_id = self.company_id
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            cancelled = False
            code = False
            try:
                client = Client(url, timeout=20)
                invoices_list = client.factory.create("UUIDS")
                invoices_list.uuids.string = [uuid]
                response = client.service.cancel(invoices_list, username, password, company_id.vat, cer_pem.replace(
                    '\n', ''), key_pem)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            if not getattr(response, 'Folios', None):
                code = getattr(response, 'CodEstatus', None)
                msg = _("Cancelling got an error") if code else _('A delay of 2 hours has to be respected before to cancel')
            else:
                code = getattr(response.Folios[0][0], 'EstatusUUID', None)
                cancelled = code in ('201', '202')  # cancelled or previously cancelled
                # no show code and response message if cancel was success
                code = '' if cancelled else code
                msg = '' if cancelled else _("Cancelling got an error")
            inv._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    @api.model
    def l10n_mx_edi_get_pac_version(self):
        '''Returns the cfdi version to generate the CFDI.
        In December, 1, 2017 the CFDI 3.2 is deprecated, after of July 1, 2018
        the CFDI 3.3 could be used.
        '''
        version = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_mx_edi_cfdi_version', '3.3')
        return version

    @api.multi
    def _l10n_mx_edi_call_service(self, service_type):
        '''Call the right method according to the pac_name, it's info returned by the '_l10n_mx_edi_%s_info' % pac_name'
        method and the service_type passed as parameter.
        :param service_type: sign or cancel
        '''
        # Regroup the invoices by company (= by pac)
        comp_x_records = groupby(self, lambda r: r.company_id)
        for company_id, records in comp_x_records:
            pac_name = company_id.l10n_mx_edi_pac
            if not pac_name:
                continue
            # Get the informations about the pac
            pac_info_func = '_l10n_mx_edi_%s_info' % pac_name
            service_func = '_l10n_mx_edi_%s_%s' % (pac_name, service_type)
            pac_info = getattr(self, pac_info_func)(company_id, service_type)
            # Call the service with invoices one by one or all together according to the 'multi' value.
            multi = pac_info.pop('multi', False)
            if multi:
                # rebuild the recordset
                records = self.env['account.invoice'].search(
                    [('id', 'in', self.ids), ('company_id', '=', company_id.id)])
                getattr(records, service_func)(pac_info)
            else:
                for record in records:
                    getattr(record, service_func)(pac_info)

    @api.multi
    def _l10n_mx_edi_post_sign_process(self, xml_signed, code=None, msg=None):
        '''Post process the results of the sign service.

        :param xml_signed: the xml signed datas codified in base64
        :param code: an eventual error code
        :param msg: an eventual error msg
        '''
        self.ensure_one()
        if xml_signed:
            # Post append addenda
            body_msg = _('The sign service has been called with success')
            # Update the pac status
            self.l10n_mx_edi_pac_status = 'signed'
            self.l10n_mx_edi_cfdi = xml_signed
            # Update the content of the attachment
            attachment_id = self.l10n_mx_edi_retrieve_last_attachment()
            attachment_id.write({
                'datas': xml_signed,
                'mimetype': 'application/xml'
            })
            xml_signed = self.l10n_mx_edi_append_addenda(xml_signed)
            post_msg = [_('The content of the attachment has been updated')]
        else:
            body_msg = _('The sign service requested failed')
            post_msg = []
        if code:
            post_msg.extend([_('Code: ') + str(code)])
        if msg:
            post_msg.extend([_('Message: ') + msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            subtype='account.mt_invoice_validated')

    @api.multi
    def _l10n_mx_edi_sign(self):
        '''Call the sign service with records that can be signed.
        '''
        records = self.search([
            ('l10n_mx_edi_pac_status', 'not in', ['signed', 'to_cancel', 'cancelled', 'retry']),
            ('id', 'in', self.ids)])
        records._l10n_mx_edi_call_service('sign')

    @api.multi
    def _l10n_mx_edi_post_cancel_process(self, cancelled, code=None, msg=None):
        '''Post process the results of the cancel service.

        :param cancelled: is the cancel has been done with success
        :param code: an eventual error code
        :param msg: an eventual error msg
        '''

        self.ensure_one()
        if cancelled:
            body_msg = _('The cancel service has been called with success')
            self.l10n_mx_edi_pac_status = 'cancelled'
        else:
            body_msg = _('The cancel service requested failed')
        post_msg = []
        if code:
            post_msg.extend([_('Code: ') + str(code)])
        if msg:
            post_msg.extend([_('Message: ') + msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            subtype='account.mt_invoice_validated')

    @api.multi
    def _l10n_mx_edi_cancel(self):
        '''Call the cancel service with records that can be signed.
        '''
        records = self.search([
            ('l10n_mx_edi_pac_status', 'in', ['to_sign', 'signed', 'to_cancel', 'retry']),
            ('id', 'in', self.ids)])
        for record in records:
            if record.l10n_mx_edi_pac_status in ['to_sign', 'retry']:
                record.l10n_mx_edi_pac_status = 'cancelled'
                record.message_post(body=_('The cancel service has been called with success'),
                    subtype='account.mt_invoice_validated')
            else:
                record.l10n_mx_edi_pac_status = 'to_cancel'
        records = self.search([
            ('l10n_mx_edi_pac_status', '=', 'to_cancel'),
            ('id', 'in', self.ids)])
        records._l10n_mx_edi_call_service('cancel')

    # -------------------------------------------------------------------------
    # Account invoice methods
    # -------------------------------------------------------------------------

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        '''Set the payment bank account on the invoice as the first of the selected partner.
        '''
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.commercial_partner_id.bank_ids:
            self.l10n_mx_edi_partner_bank_id = self.commercial_partner_id.bank_ids[0].id
        return res

    @api.multi
    def action_invoice_draft(self):
        """Reset l10n_mx_edi_time_invoice when invoice state set to draft"""

        signed = self.filtered(lambda r: r.l10n_mx_edi_is_required() and
                               not r.company_id.l10n_mx_edi_pac_test_env and
                               r.l10n_mx_edi_cfdi_uuid)
        signed.l10n_mx_edi_update_sat_status()
        not_allow = signed.filtered(lambda r: r.l10n_mx_edi_sat_status != 'cancelled' or r.l10n_mx_edi_pac_status == 'to_cancel')
        not_allow.message_post(
            subject=_('An error occurred while setting to draft.'),
            message_type='comment',
            body=_('This invoice does not have a properly cancelled XML and '
                   'it was signed at least once, please cancel properly with '
                   'the SAT.'))
        allow = self - not_allow
        allow.write({'l10n_mx_edi_time_invoice': False})
        for record in allow.filtered('l10n_mx_edi_cfdi_uuid'):
            record.l10n_mx_edi_origin = record._set_cfdi_origin('04', [record.l10n_mx_edi_cfdi_uuid])
        return super(AccountInvoice, self - not_allow).action_invoice_draft()

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        """When is created the invoice refund is assigned the reference to
        the invoice that was generate it"""
        values = super(AccountInvoice, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        if invoice.l10n_mx_edi_cfdi_uuid:
            values['l10n_mx_edi_origin'] = '%s|%s' % ('01', invoice.l10n_mx_edi_cfdi_uuid)
        return values

    @api.multi
    @api.depends('l10n_mx_edi_cfdi_name')
    def _compute_cfdi_values(self):
        '''Fill the invoice fields from the cfdi values.
        '''
        for inv in self:
            attachment_id = inv.l10n_mx_edi_retrieve_last_attachment()
            if not attachment_id:
                continue
            # At this moment, the attachment contains the file size in its 'datas' field because
            # to save some memory, the attachment will store its data on the physical disk.
            # To avoid this problem, we read the 'datas' directly on the disk.
            datas = attachment_id._file_read(attachment_id.store_fname)
            inv.l10n_mx_edi_cfdi = datas
            cfdi = base64.decodestring(datas).replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            tree = inv.l10n_mx_edi_get_xml_etree(cfdi)
            # if already signed, extract uuid
            tfd_node = inv.l10n_mx_edi_get_tfd_etree(tree)
            if tfd_node is not None:
                inv.l10n_mx_edi_cfdi_uuid = tfd_node.get('UUID')
            inv.l10n_mx_edi_cfdi_amount = tree.get('Total', tree.get('total'))
            inv.l10n_mx_edi_cfdi_supplier_rfc = tree.Emisor.get(
                'Rfc', tree.Emisor.get('rfc'))
            inv.l10n_mx_edi_cfdi_customer_rfc = tree.Receptor.get(
                'Rfc', tree.Receptor.get('rfc'))
            certificate = tree.get('noCertificado', tree.get('NoCertificado'))
            inv.l10n_mx_edi_cfdi_certificate_id = self.env['l10n_mx_edi.certificate'].sudo().search(
                [('serial_number', '=', certificate)], limit=1)

    @api.multi
    def _l10n_mx_edi_create_taxes_cfdi_values(self):
        '''Create the taxes values to fill the CFDI template.
        '''
        self.ensure_one()
        values = {
            'total_withhold': 0,
            'total_transferred': 0,
            'withholding': [],
            'transferred': [],
        }
        taxes = {}
        for line in self.invoice_line_ids.filtered('price_subtotal'):
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            taxes_line = line.invoice_line_tax_ids
            taxes_line = taxes_line.filtered(
                lambda tax: tax.amount_type != 'group') + taxes_line.filtered(
                    lambda tax: tax.amount_type == 'group').mapped(
                        'children_tax_ids')
            tax_line = {tax['id']: tax for tax in taxes_line.compute_all(
                price, line.currency_id, line.quantity, line.product_id, line.partner_id)['taxes']}
            for tax in taxes_line.filtered(lambda r: r.l10n_mx_cfdi_tax_type != 'Exento'):
                tax_dict = tax_line.get(tax.id, {})
                amount = round(abs(tax_dict.get(
                    'amount', tax.amount / 100 * float("%.2f" % line.price_subtotal))), 2)
                rate = round(abs(tax.amount), 2)
                if tax.id not in taxes:
                    taxes.update({tax.id: {
                        'name': (tax.tag_ids[0].name
                                 if tax.tag_ids else tax.name).upper(),
                        'amount': amount,
                        'rate': rate if tax.amount_type == 'fixed' else rate / 100.0,
                        'type': tax.l10n_mx_cfdi_tax_type,
                        'tax_amount': tax_dict.get('amount', tax.amount),
                    }})
                else:
                    taxes[tax.id].update({
                        'amount': taxes[tax.id]['amount'] + amount
                    })
                if tax.amount >= 0:
                    values['total_transferred'] += amount
                else:
                    values['total_withhold'] += amount
        values['transferred'] = [tax for tax in taxes.values() if tax['tax_amount'] >= 0]
        values['withholding'] = [tax for tax in taxes.values() if tax['tax_amount'] < 0]
        return values

    @staticmethod
    def _l10n_mx_get_serie_and_folio(number):
        values = {'serie': None, 'folio': None}
        number = (number or '').strip()
        number_matchs = [rn for rn in re.finditer('\d+', number)]
        if number_matchs:
            last_number_match = number_matchs[-1]
            values['serie'] = number[:last_number_match.start()] or None
            values['folio'] = last_number_match.group().lstrip('0') or None
        return values

    @staticmethod
    def _get_string_cfdi(text, size=100):
        """Replace from text received the characters that are not found in the
        regex. This regex is taken from SAT documentation
        https://goo.gl/C9sKH6
        text: Text to remove extra characters
        size: Cut the string in size len
        Ex. 'Product ABC (small size)' - 'Product ABC small size'"""
        if not text:
            return None
        text = text.replace('|', ' ')
        return text.strip()[:size]

    @api.multi
    def _l10n_mx_edi_get_payment_policy(self):
        self.ensure_one()
        version = self.l10n_mx_edi_get_pac_version()
        term_ids = self.payment_term_id.line_ids
        if version == '3.2':
            if len(term_ids.ids) > 1:
                return 'Pago en parcialidades'
            else:
                return 'Pago en una sola exhibición'
        elif version == '3.3' and self.date_due and self.date_invoice:
            # In CFDI 3.3 - SAT 2018 rule 2.7.1.44, the payment policy is PUE
            # if the invoice will be paid before 17th of the following month,
            # PPD otherwise
            date_pue = (fields.Date.from_string(self.date_invoice) +
                        relativedelta(day=17, months=1))
            date_due = fields.Date.from_string(self.date_due)
            if (date_due > date_pue or len(term_ids) > 1):
                return 'PPD'
            return 'PUE'
        return ''

    @api.multi
    def _l10n_mx_edi_create_cfdi_values(self):
        '''Create the values to fill the CFDI template.
        '''
        self.ensure_one()
        precision_digits = self.currency_id.l10n_mx_edi_decimal_places
        if precision_digits is False:
            raise UserError(_(
                "The SAT does not provide information for the currency %s.\n"
                "You must get manually a key from the PAC to confirm the "
                "currency rate is accurate enough."), self.currency_id)
        partner_id = self.partner_id
        if self.partner_id.type != 'invoice':
            partner_id = self.partner_id.commercial_partner_id
        values = {
            'record': self,
            'currency_name': self.currency_id.name,
            'supplier': self.company_id.partner_id.commercial_partner_id,
            'issued': self.journal_id.l10n_mx_address_issued_id,
            'customer': partner_id,
            'fiscal_position': self.company_id.partner_id.property_account_position_id,
            'payment_method': self.l10n_mx_edi_payment_method_id.code,
            'use_cfdi': self.l10n_mx_edi_usage,
            'conditions': self._get_string_cfdi(
                self.payment_term_id.name, 1000) if self.payment_term_id else False,
        }

        values.update(self._l10n_mx_get_serie_and_folio(self.number))
        ctx = dict(company_id=self.company_id.id, date=self.date_invoice)
        mxn = self.env.ref('base.MXN').with_context(ctx)
        invoice_currency = self.currency_id.with_context(ctx)
        values['rate'] = ('%.6f' % (
            invoice_currency._convert(1, mxn, self.company_id, self.date_invoice or fields.Date.today(), round=False))) if self.currency_id.name != 'MXN' else False

        values['document_type'] = 'ingreso' if self.type == 'out_invoice' else 'egreso'
        values['payment_policy'] = self._l10n_mx_edi_get_payment_policy()
        domicile = self.journal_id.l10n_mx_address_issued_id or self.company_id
        values['domicile'] = '%s %s, %s' % (
                domicile.city,
                domicile.state_id.name,
                domicile.country_id.name,
        )

        values['decimal_precision'] = precision_digits
        subtotal_wo_discount = lambda l: float_round(
            l.price_subtotal / (1 - l.discount/100) if l.discount != 100 else
            l.price_unit * l.quantity, int(precision_digits))
        values['subtotal_wo_discount'] = subtotal_wo_discount
        get_discount = lambda l, d: ('%.*f' % (
            int(d), subtotal_wo_discount(l) - l.price_subtotal)) if l.discount else False
        values['total_discount'] = get_discount
        total_discount = sum([float(get_discount(p, precision_digits)) for p in self.invoice_line_ids])
        values['amount_untaxed'] = '%.*f' % (
            precision_digits, sum([subtotal_wo_discount(p) for p in self.invoice_line_ids]))
        values['amount_discount'] = '%.*f' % (precision_digits, total_discount) if total_discount else None

        values['taxes'] = self._l10n_mx_edi_create_taxes_cfdi_values()
        values['amount_total'] = '%0.*f' % (precision_digits,
            float(values['amount_untaxed']) - float(values['amount_discount'] or 0) + (
                values['taxes']['total_transferred'] or 0) - (values['taxes']['total_withhold'] or 0))

        values['tax_name'] = lambda t: {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(
            t, False)

        if self.l10n_mx_edi_partner_bank_id:
            digits = [s for s in self.l10n_mx_edi_partner_bank_id.acc_number if s.isdigit()]
            acc_4number = ''.join(digits)[-4:]
            values['account_4num'] = acc_4number if len(acc_4number) == 4 else None
        else:
            values['account_4num'] = None

        return values

    @api.multi
    def get_cfdi_related(self):
        """To node CfdiRelacionados get documents related with each invoice
        from l10n_mx_edi_origin, hope the next structure:
            relation type|UUIDs separated by ,"""
        self.ensure_one()
        if not self.l10n_mx_edi_origin:
            return {}
        origin = self.l10n_mx_edi_origin.split('|')
        uuids = origin[1].split(',') if len(origin) > 1 else []
        return {
            'type': origin[0],
            'related': [u.strip() for u in uuids],
            }

    def l10n_mx_edi_append_addenda(self, xml_signed):
        self.ensure_one()
        addenda = (
            self.partner_id.l10n_mx_edi_addenda or
            self.partner_id.commercial_partner_id.l10n_mx_edi_addenda)
        if not addenda:
            return xml_signed
        values = {
            'record': self,
        }
        tree = fromstring(base64.decodestring(xml_signed))
        addenda_node = fromstring(addenda.render(values=values))
        if addenda_node.tag != '{http://www.sat.gob.mx/cfd/3}Addenda':
            node = etree.Element(etree.QName(
                'http://www.sat.gob.mx/cfd/3', 'Addenda'))
            node.append(addenda_node)
            addenda_node = node
        tree.append(addenda_node)
        self.message_post(
            body=_('Addenda has been added in the CFDI with success'),
            subtype='account.mt_invoice_validated')
        xml_signed = base64.encodestring(etree.tostring(
            tree, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
        attachment_id = self.l10n_mx_edi_retrieve_last_attachment()
        attachment_id.write({
            'datas': xml_signed,
            'mimetype': 'application/xml'
        })
        return xml_signed

    @api.multi
    def _l10n_mx_edi_create_cfdi(self):
        '''Creates and returns a dictionnary containing 'cfdi' if the cfdi is well created, 'error' otherwise.
        '''
        self.ensure_one()
        qweb = self.env['ir.qweb']
        error_log = []
        company_id = self.company_id
        pac_name = company_id.l10n_mx_edi_pac
        values = self._l10n_mx_edi_create_cfdi_values()

        # -----------------------
        # Check the configuration
        # -----------------------
        # -Check certificate
        certificate_ids = company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        if not certificate_id:
            error_log.append(_('No valid certificate found'))

        # -Check PAC
        if pac_name:
            pac_test_env = company_id.l10n_mx_edi_pac_test_env
            pac_username = company_id.l10n_mx_edi_pac_username
            pac_password = company_id.l10n_mx_edi_pac_password
            if not pac_test_env and not (pac_username and pac_password):
                error_log.append(_('No PAC credentials specified.'))
        else:
            error_log.append(_('No PAC specified.'))

        if error_log:
            return {'error': _('Please check your configuration: ') + create_list_html(error_log)}

        # -Compute date and time of the invoice
        time_invoice = datetime.strptime(self.l10n_mx_edi_time_invoice,
                                         DEFAULT_SERVER_TIME_FORMAT).time()
        # -----------------------
        # Create the EDI document
        # -----------------------
        version = self.l10n_mx_edi_get_pac_version()

        # -Compute certificate data
        values['date'] = datetime.combine(
            fields.Datetime.from_string(self.date_invoice), time_invoice).strftime('%Y-%m-%dT%H:%M:%S')
        values['certificate_number'] = certificate_id.serial_number
        values['certificate'] = certificate_id.sudo().get_data()[0]

        # -Compute cfdi
        cfdi = qweb.render(CFDI_TEMPLATE_33, values=values)
        node_sello = 'Sello'
        attachment = self.env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
        xsd_datas = base64.b64decode(attachment.datas) if attachment else b''

        # -Compute cadena
        tree = self.l10n_mx_edi_get_xml_etree(cfdi)
        cadena = self.l10n_mx_edi_generate_cadena(CFDI_XSLT_CADENA % version, tree)
        tree.attrib[node_sello] = certificate_id.sudo().get_encrypted_cadena(cadena)

        # Check with xsd
        if xsd_datas:
            try:
                with BytesIO(xsd_datas) as xsd:
                    _check_with_xsd(tree, xsd)
            except (IOError, ValueError):
                _logger.info(
                    _('The xsd file to validate the XML structure was not found'))
            except Exception as e:
                return {'error': (_('The cfdi generated is not valid') +
                                    create_list_html(str(e).split('\\n')))}

        return {'cfdi': etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding='UTF-8')}

    @api.multi
    def _l10n_mx_edi_retry(self):
        '''Try to generate the cfdi attachment and then, sign it.
        '''
        version = self.l10n_mx_edi_get_pac_version()
        for inv in self:
            cfdi_values = inv._l10n_mx_edi_create_cfdi()
            error = cfdi_values.pop('error', None)
            cfdi = cfdi_values.pop('cfdi', None)
            if error:
                # cfdi failed to be generated
                inv.l10n_mx_edi_pac_status = 'retry'
                inv.message_post(body=error, subtype='account.mt_invoice_validated')
                continue
            # cfdi has been successfully generated
            inv.l10n_mx_edi_pac_status = 'to_sign'
            filename = ('%s-%s-MX-Invoice-%s.xml' % (
                inv.journal_id.code, inv.number, version.replace('.', '-'))).replace('/', '')
            ctx = self.env.context.copy()
            ctx.pop('default_type', False)
            inv.l10n_mx_edi_cfdi_name = filename
            attachment_id = self.env['ir.attachment'].with_context(ctx).create({
                'name': filename,
                'res_id': inv.id,
                'res_model': inv._name,
                'datas': base64.encodestring(cfdi),
                'datas_fname': filename,
                'description': 'Mexican invoice',
                })
            inv.message_post(
                body=_('CFDI document generated (may be not signed)'),
                attachment_ids=[attachment_id.id],
                subtype='account.mt_invoice_validated')
            inv._l10n_mx_edi_sign()

    @api.multi
    def invoice_validate(self):
        '''Generates the cfdi attachments for mexican companies when validated.'''
        result = super(AccountInvoice, self).invoice_validate()
        version = self.l10n_mx_edi_get_pac_version()
        for record in self.filtered(lambda r: r.l10n_mx_edi_is_required()):
            if record.type == 'out_refund' and (
                record.refund_invoice_id and not record.refund_invoice_id.l10n_mx_edi_cfdi_uuid):
                record.message_post(
                    body='<p style="color:red">' + _(
                        'The invoice related has no valid fiscal folio. For this '
                        'reason, this refund didn\'t generate a fiscal document.') + '</p>',
                    subtype='account.mt_invoice_validated')
                continue
            record.l10n_mx_edi_cfdi_name = ('%s-%s-MX-Invoice-%s.xml' % (
                record.journal_id.code, record.number, version.replace('.', '-'))).replace('/', '')
            record._l10n_mx_edi_retry()
        return result

    @api.multi
    def action_date_assign(self):
        """Assign invoice time and date"""
        for record in self.filtered(lambda r: r.l10n_mx_edi_is_required()):
            date_mx = self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime()
            if not record.date_invoice:
                record.date_invoice = date_mx.date()
            if not record.l10n_mx_edi_time_invoice:
                record.l10n_mx_edi_time_invoice = date_mx.strftime(
                    DEFAULT_SERVER_TIME_FORMAT)
                record._l10n_mx_edi_update_hour_timezone()
        return super(AccountInvoice, self).action_date_assign()

    @api.multi
    def action_invoice_cancel(self):
        '''Cancel the cfdi attachments for mexican companies when cancelled.
        '''
        result = super(AccountInvoice, self).action_invoice_cancel()
        for record in self.filtered(lambda r: r.l10n_mx_edi_is_required()):
            record._l10n_mx_edi_cancel()
        return result

    @api.multi
    def l10n_mx_edi_update_pac_status(self):
        '''Synchronize both systems: Odoo & PAC if the invoices need to be signed or cancelled.
        '''
        for record in self:
            if record.l10n_mx_edi_pac_status in ('to_sign', 'retry'):
                record._l10n_mx_edi_retry()
            elif record.l10n_mx_edi_pac_status == 'to_cancel':
                record._l10n_mx_edi_cancel()

    @api.multi
    def l10n_mx_edi_update_sat_status(self):
        '''Synchronize both systems: Odoo & SAT to make sure the invoice is valid.
        '''
        url = 'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl'
        headers = {'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta', 'Content-Type': 'text/xml; charset=utf-8'}
        template = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Consulta>
         <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
      </ns0:Consulta>
   </ns1:Body>
</SOAP-ENV:Envelope>"""
        namespace = {'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'}
        for inv in self.filtered('l10n_mx_edi_cfdi'):
            supplier_rfc = inv.l10n_mx_edi_cfdi_supplier_rfc
            customer_rfc = inv.l10n_mx_edi_cfdi_customer_rfc
            total = float_repr(inv.l10n_mx_edi_cfdi_amount,
                               precision_digits=inv.currency_id.decimal_places)
            uuid = inv.l10n_mx_edi_cfdi_uuid
            params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
                tools.html_escape(tools.html_escape(supplier_rfc or '')),
                tools.html_escape(tools.html_escape(customer_rfc or '')),
                total or 0.0, uuid or '')
            soap_env = template.format(data=params)
            try:
                soap_xml = requests.post(url, data=soap_env, headers=headers)
                response = fromstring(soap_xml.text)
                status = response.xpath(
                    '//a:Estado', namespaces=namespace)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            inv.l10n_mx_edi_sat_status = CFDI_SAT_QR_STATE.get(
                status[0] if status else '', 'none')

    @api.multi
    def _set_cfdi_origin(self, rtype='', uuids=[]):
        """Try to write the origin in of the CFDI, it is important in order
        to have a centralized way to manage this elements due to the fact
        that this logic can be used in several places functionally speaking
        all around Odoo.
        :param rtype:
            - 01: Nota de crédito
            - 02: Nota de débito de los documentos relacionados
            - 03: Devolución de mercancía sobre facturas o traslados previos
            - 04: Sustitución de los CFDI previos
            - 05: Traslados de mercancias facturados previamente
            - 06: Factura generada por los traslados previos
            - 07: CFDI por aplicación de anticipo
        :param uuids:
        :return:
        """
        self.ensure_one()
        types = ['01', '02', '03', '04', '05', '06', '07']
        if not rtype in types:
            raise UserError(_('Invalid given type of document for field CFDI '
                                'Origin'))
        uuids = [u for u in uuids if isinstance(u, str)]
        ids = ','.join(uuids)
        l10n_mx_edi_origin = self.l10n_mx_edi_origin
        old_rtype = l10n_mx_edi_origin.split('|')[0] if l10n_mx_edi_origin else False
        if old_rtype and old_rtype not in types:
            raise UserError(_('Invalid type of document for field CFDI '
                              'Origin'))
        if not l10n_mx_edi_origin or old_rtype != rtype:
            origin = '%s|%s' % (rtype, ids)
            self.update({'l10n_mx_edi_origin': origin})
            return origin
        try:
            old_ids = l10n_mx_edi_origin.split('|')[1].split(',')
        except IndexError:
            raise UserError(
                _('The cfdi origin field must be filled with type and list of '
                  'cfdi separated by comma like this '
                  '"01|89966ACC-0F5C-447D-AEF3-3EED22E711EE,89966ACC-0F5C-447D-AEF3-3EED22E711EE"'
                  '\n get %s instead' % l10n_mx_edi_origin))
        ids = ','.join(old_ids + uuids)
        origin = '%s|%s' % (rtype, ids)
        self.update({'l10n_mx_edi_origin': origin})
        return origin

    def _l10n_mx_edi_update_hour_timezone(self):
        for inv in self:
            partner = inv.journal_id.l10n_mx_address_issued_id or inv.company_id.partner_id.commercial_partner_id
            # northwest area
            if partner.state_id.code == 'BCN':
                tz = timezone('America/Tijuana')
            # Southeast area
            elif partner.state_id.code == 'ROO':
                tz = timezone('America/Cancun')
            # Pacific area
            elif partner.state_id.code in ('BCS', 'CHH', 'SIN', 'NAY'):
                tz = timezone('America/Chihuahua')
            # Sonora
            elif partner.state_id.code in ('SON',):
                tz = timezone('America/Hermosillo')
            # By default, takes the central area timezone
            else:
                tz = timezone('America/Mexico_City')

            # Check the TZ should be forced for the current journal
            tz_force = self.env['ir.config_parameter'].sudo().get_param(
                'l10n_mx_edi_tz_%s' % inv.journal_id.id, default=None)
            if tz_force:
                tz = timezone(tz_force)

            datetime_mx_tz = datetime.now(tz)
            inv.l10n_mx_edi_time_invoice = datetime_mx_tz.strftime("%H:%M:%S")
