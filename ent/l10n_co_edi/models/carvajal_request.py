# coding: utf-8
import base64
import logging
import os
import pytz
import suds
import socket
import re
from datetime import datetime
from hashlib import sha256
from odoo import _
from suds.client import Client
from suds.plugin import MessagePlugin
from suds.sax.element import Element

from lxml import etree

_logger = logging.getLogger(__name__)

class CarvajalException(Exception):
    pass

class CarvajalPlugin(MessagePlugin):
    def marshalled(self, context):
        context.envelope.nsprefixes['wsse'] = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd'
        context.envelope.nsprefixes['wsu'] = 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd'

    def sending(self, context):
        self.log(context.envelope, 'carvajal_request')

    def received(self, context):
        # When the service returns a response it also includes HTTP headers. E.g.:
        # --uuid:0230b457-8952-4ac2-bcb7-8061a447cf5b Content-Type:
        # application/xop+xml; charset=UTF-8; type="text/xml"
        # Content-Transfer-Encoding: binary Content-ID:
        # <root.message@cxf.apache.org>
        #
        # <soap:Envelope ... </soap:Envelope>
        # --uuid:0230b457-8952-4ac2-bcb7-8061a447cf5b--
        #
        # suds doesn't seem to parse these so manually remove
        # them. Otherwise suds will crash because it will parse the
        # response as XML.
        if b'Content-Type:' in context.reply:
            # HTTP header ends with blank line
            xml_start = re.search(b'^\s*$', context.reply, re.MULTILINE).start()
            context.reply = context.reply[xml_start:]

            # last line will contain '--uuid:...'
            context.reply = context.reply.rsplit(b'\r\n', 1)[0]

        self.log(context.reply, 'carvajal_response')

    def log(self, xml_string, func):
        xml = etree.fromstring(xml_string)
        _logger.debug('%s with\n%s' % (func, etree.tostring(xml, encoding='utf-8', xml_declaration=True, pretty_print=True)))


class CarvajalRequest():
    def __init__(self, username, password, company, account, test_mode):
        self.username = username or ''
        self.password = password or ''
        self.company = company or ''
        self.account = account or ''

        self.client = Client('https://cenfinanciero%s.cen.biz/isows/InvoiceService?wsdl' % ('lab' if test_mode else ''), plugins=[CarvajalPlugin()])
        self.client.set_options(soapheaders=self._create_wsse_header(self.username, self.password))

    def _create_wsse_header(self, username, password):
        username_element = Element('wsse:Username')
        username_element.setText(username)

        password_element = Element('wsse:Password')
        password_element.set('Type', 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText')
        password_element.setText(sha256(password.encode()).hexdigest())

        nonce = Element('wsse:Nonce')
        nonce.set('EncodingType', 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary')
        nonce.setText(base64.b64encode(os.urandom(64)))

        bogota_tz = pytz.timezone('America/Bogota')
        created = Element('wsu:Created')
        created.setText(pytz.utc.localize(datetime.now()).astimezone(bogota_tz).strftime('%Y-%m-%dT%H:%M:%S.000-05:00'))

        username_token = Element('wsse:UsernameToken')
        username_token.set('wsu:Id', 'UsernameToken-1')
        username_token.append(username_element)
        username_token.append(password_element)
        username_token.append(nonce)
        username_token.append(created)

        header = Element('wsse:Security').append(username_token)

        return header

    def upload(self, filename, xml):
        try:
            response = self.client.service.Upload(fileName=filename, fileData=base64.b64encode(xml).decode(),
                                                  companyId=self.company, accountId=self.account)
        except suds.WebFault as fault:
            _logger.error(fault)
            raise CarvajalException(fault.fault.faultstring)
        except socket.timeout as e:
            _logger.error(e)
            raise CarvajalException(_('Connection to Carvajal timed out. Their API is probably down.'))

        return {
            'message': response.status,
            'transactionId': response.transactionId,
        }

    def download(self, document_prefix, document_number, document_type):
        try:
            response = self.client.service.Download(documentPrefix=document_prefix, documentNumber=document_number,
                                                    documentType=document_type, resourceType='PDF,SIGNED_XML',
                                                    companyId=self.company, accountId=self.account)
        except suds.WebFault as fault:
            _logger.error(fault)
            raise CarvajalException(fault.fault.faultstring)

        return {
            'message': response.status,
            'zip_b64': base64.b64decode(response.downloadData),
        }

    def check_status(self, transactionId):
        try:
            response = self.client.service.DocumentStatus(transactionId=transactionId,
                                                          companyId=self.company, accountId=self.account)
        except suds.WebFault as fault:
            _logger.error(fault)
            raise CarvajalException(fault.fault.faultstring)

        return {
            'status': response.processStatus,
            'errorMessage': response.errorMessage if hasattr(response, 'errorMessage') else '',
            'legalStatus': response.legalStatus if hasattr(response, 'legalStatus') else '',
            'governmentResponseDescription': response.governmentResponseDescription if hasattr(response, 'governmentResponseDescription') else '',
        }
