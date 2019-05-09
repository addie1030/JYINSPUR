import base64
import logging
from os.path import splitext
from codecs import BOM_UTF8

from lxml import objectify

from odoo import _, api, models
from odoo.exceptions import ValidationError

BOM_UTF8U = BOM_UTF8.decode('UTF-8')

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.multi
    def unlink(self):
        """In order to deny XML attachments deletion from an invoice, because
        the xml attachments are legal documents.
        This method validates the content of the xml in the deletion process,
        looking for a valid UUID that matches against the 'cfdi_uuid' in the
        invoice related to the attachment
        """
        attachment_ids = self.filtered(
            lambda r: r.datas and r.res_model == 'account.invoice' and
            splitext(r.name)[1].lower() in ('.pdf', '.xml'))
        for attach in attachment_ids:
            # If it's a PDF, looks for an XML with the same name
            if splitext(attach.name)[1].lower() == '.pdf':
                file_name = '%s.xml' % splitext(attach.name)[0]
                attach = self.search([
                    ('name', '=', file_name),
                    ('res_model', '=', attach.res_model),
                    ('res_id', '=', attach.res_id)])
            attach.check_valid_uuid()
        return super(IrAttachment, self).unlink()

    @api.multi
    def check_valid_uuid(self):
        for attach in self:
            datas = attach.datas
            xml_string = base64.b64decode(datas).lstrip(BOM_UTF8)
            try:
                xml = objectify.fromstring(xml_string)
            except (SyntaxError, ValueError) as err:
                _logger.error(str(err))
                continue
            invoice = self.env['account.invoice'].browse(attach.res_id)
            tree = invoice.l10n_mx_edi_get_tfd_etree(xml)
            if tree is None:
                continue
            uuid = tree.get('UUID', '')
            if uuid:
                raise ValidationError(_(
                    "You cannot delete a set of documents which has a legal "
                    "information and it's declared to the SAT, please try to "
                    "cancel the document linked to the record: %s in the "
                    "model: %s and named: %s with the UUID: %s first and then "
                    "resign it if necessary.") % (
                        attach.res_id, attach.res_model, attach.name, uuid))
