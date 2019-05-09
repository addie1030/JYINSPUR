# -*- coding: utf-8 -*-

from odoo.addons.iap import jsonrpc
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import AccessError
import logging
import base64
import re

_logger = logging.getLogger(__name__)

PARTNER_REMOTE_URL = 'https://partner-autocomplete.odoo.com/iap/partner_autocomplete'
CLIENT_OCR_VERSION = 100

def to_float(text):
    """format a text to try to find a float in it. Ex: 127,00  320.612,8  15.9"""
    t_no_space = text.replace(" ", "")
    char = ""
    for c in t_no_space:
        if c in ['.', ',']:
            char = c
    if char == ",":
        t_no_space = t_no_space.replace(".", "")
        t_no_space = t_no_space.replace(",", ".")
    elif char == ".":
        t_no_space = t_no_space.replace(",", "")
    try:
        return float(t_no_space)
    except (AttributeError, ValueError):
        return None 

class AccountInvoiceExtractionWords(models.Model):

    _name = "account.invoice_extract.words"
    _description = "Extracted words from invoice scan"

    invoice_id = fields.Many2one("account.invoice", help="Invoice id")
    field = fields.Char()
    selected_status = fields.Integer("Invoice extract selected status.",
        help="0 for 'not selected', 1 for ocr choosed and 2 for ocr selected but not choosed by user")
    user_selected = fields.Boolean()
    word_text = fields.Char()
    word_page = fields.Integer()
    word_box_midX = fields.Float()
    word_box_midY = fields.Float()
    word_box_width = fields.Float()
    word_box_height = fields.Float()
    word_box_angle = fields.Float()
    

class AccountInvoice(models.Model):

    _name = "account.invoice"
    _inherit = ['account.invoice']

    def _compute_can_show_send_resend(self, record):
        can_show = True
        if self.env.user.company_id.extract_show_ocr_option_selection == 'no_send':
            can_show = False
        if record.state not in 'draft':
            can_show = False
        if record.type in ["out_invoice", "out_refund"]:
            can_show = False
        if record.message_main_attachment_id == None or len(record.message_main_attachment_id) == 0:
            can_show = False
        return can_show

    @api.depends('state', 'extract_state', 'message_ids')
    def _compute_show_resend_button(self):
        for record in self:
            record.extract_can_show_resend_button = self._compute_can_show_send_resend(record)
            if record.extract_state not in ['error_status', 'not_enough_credit', 'module_not_up_to_date']:
                record.extract_can_show_resend_button = False

    @api.depends('state', 'extract_state', 'message_ids')
    def _compute_show_send_button(self):
        for record in self:
            record.extract_can_show_send_button = self._compute_can_show_send_resend(record)
            if record.extract_state not in ['no_extract_requested']:
                record.extract_can_show_send_button = False

    extract_state = fields.Selection([('no_extract_requested', 'No extract requested'),
                            ('not_enough_credit', 'Not enough credit'),
                            ('error_status', 'An error occured'),
                            ('waiting_extraction', 'Waiting extraction'),
                            ('extract_not_ready', 'waiting extraction, but it is not ready'),
                            ('waiting_validation', 'Waiting validation'),
                            ('done', 'Completed flow')],
                            'Extract state', default='no_extract_requested', required=True)
    extract_remoteid = fields.Integer("Id of the request to IAP-OCR", default="-1", help="Invoice extract id")
    extract_word_ids = fields.One2many("account.invoice_extract.words", inverse_name="invoice_id")

    extract_can_show_resend_button = fields.Boolean("Can show the ocr resend button", compute=_compute_show_resend_button)
    extract_can_show_send_button = fields.Boolean("Can show the ocr send button", compute=_compute_show_send_button)

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        """When a message is posted on an account.invoice, send the attachment to iap-ocr if
        the res_config is on "auto_send" and if this is the first attachment."""
        res = super(AccountInvoice, self).message_post(**kwargs)
        if self.env.user.company_id.extract_show_ocr_option_selection == 'auto_send':
            account_token = self.env['iap.account'].get('invoice_ocr')
            for record in self:
                if record.type in ["out_invoice", "out_refund"]:
                    return res
                if record.extract_state == "no_extract_requested":
                    attachments = res.attachment_ids
                    if attachments:
                        endpoint = self.env['ir.config_parameter'].sudo().get_param(
                            'account_invoice_extract_endpoint', 'https://iap-extract.odoo.com') + '/iap/invoice_extract/parse'
                        params = {
                            'account_token': account_token.account_token,
                            'version': CLIENT_OCR_VERSION,
                            'dbuuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
                            'documents': [x.datas.decode('utf-8') for x in attachments],
                            'file_names': [x.datas_fname for x in attachments],
                        }
                        try:
                            result = jsonrpc(endpoint, params=params)
                            if result[1] == "Not enough credits":
                                record.extract_state = 'not_enough_credit'
                            elif result[0] == -1:
                                record.extract_state = 'error_status'
                            else:
                                record.extract_remoteid = result[0]
                                record.extract_state = 'waiting_extraction'
                        except AccessError:
                            record.extract_state = 'error_status'
        for record in self:
            record._compute_show_resend_button()
        return res

    def retry_ocr(self):
        """Retry to contact iap to submit the first attachment in the chatter"""
        if self.env.user.company_id.extract_show_ocr_option_selection == 'no_send':
            return False
        attachments = self.message_main_attachment_id
        if attachments and attachments.exists() and self.extract_state in ['no_extract_requested', 'not_enough_credit', 'error_status', 'module_not_up_to_date']:
            account_token = self.env['iap.account'].get('invoice_ocr')
            endpoint = self.env['ir.config_parameter'].sudo().get_param(
                'account_invoice_extract_endpoint', 'https://iap-extract.odoo.com')  + '/iap/invoice_extract/parse'
            params = {
                'account_token': account_token.account_token,
                'version': CLIENT_OCR_VERSION,
                'dbuuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
                'documents': [x.datas.decode('utf-8') for x in attachments], 
                'file_names': [x.datas_fname for x in attachments],
            }
            try:
                result = jsonrpc(endpoint, params=params)
                if result[1] == "Not enough credits":
                    self.extract_state = 'not_enough_credit'
                elif result[0] == -1:
                    self.extract_state = 'error_status'
                    _logger.warning('There was an issue while doing the OCR operation on this file. Error: -1')
                else:
                    self.extract_state = 'waiting_extraction'
                    self.extract_remoteid = result[0]
            except AccessError:
                self.extract_state = 'error_status'

    @api.multi
    def get_validation(self, field):
        """
        return the text or box corresponding to the choice of the user.
        If the user selected a box on the document, we return this box, 
        but if he entered the text of the field manually, we return only the text, as we 
        don't know which box is the right one (if it exists)
        """
        selected = self.env["account.invoice_extract.words"].search([("invoice_id", "=", self.id), ("field", "=", field), ("user_selected", "=", True)])
        if not selected.exists():
            selected = self.env["account.invoice_extract.words"].search([("invoice_id", "=", self.id), ("field", "=", field), ("selected_status", "!=", 0)])
        return_box = {}
        if selected.exists():
            return_box["box"] = [selected.word_text, selected.word_page, selected.word_box_midX, 
                selected.word_box_midY, selected.word_box_width, selected.word_box_height, selected.word_box_angle]
        #now we have the user or ocr selection, check if there was manual changes
        text_to_send = {}
        if field == "total":
            text_to_send["text"] = self.amount_total
        elif field == "date":
            text_to_send["text"] = str(self.date_invoice)
        elif field == "due_date":
            text_to_send["text"] = str(self.date_due)
        elif field == "invoice_id":
            text_to_send["text"] = self.reference
        elif field == "supplier":
            text_to_send["text"] = self.partner_id.name
        elif field == "VAT_Number":
            text_to_send["text"] = self.partner_id.vat
        elif field == "currency":
            text_to_send["text"] = self.currency_id.name
        else:
            return None
        
        return_box.update(text_to_send)
        return return_box

    @api.multi
    def invoice_validate(self):
        """On the validation of an invoice, send the differents corrected fields to iap to improve
        the ocr algorithm"""
        res = super(AccountInvoice, self).invoice_validate()
        for record in self:
            if record.type in ["out_invoice", "out_refund"]:
                return
            if record.extract_state == 'waiting_validation':
                endpoint = self.env['ir.config_parameter'].sudo().get_param(
                    'account_invoice_extract_endpoint', 'https://iap-extract.odoo.com')  + '/iap/invoice_extract/validate'
                values = {
                    'total': record.get_validation('total'),
                    'date': record.get_validation('date'),
                    'due_date': record.get_validation('due_date'),
                    'invoice_id': record.get_validation('invoice_id'),
                    'partner': record.get_validation('supplier'),
                    'VAT_Number': record.get_validation('VAT_Number'),
                    'currency': record.get_validation('currency')
                }
                params = {
                    'document_id': record.extract_remoteid, 
                    'version': CLIENT_OCR_VERSION,
                    'values': values
                }
                try:
                    _logger.warning(params) #TODO remove
                    result = jsonrpc(endpoint, params=params)
                    record.extract_state = 'done'
                except AccessError:
                    pass
        #we don't need word data anymore, we can delete them
        self.mapped('extract_word_ids').unlink()
        return res

    @api.multi
    def get_boxes(self):
        return [{
            "id": data.id,
            "feature": data.field, 
            "text": data.word_text, 
            "selected_status": data.selected_status, 
            "user_selected": data.user_selected,
            "page": data.word_page,
            "box_midX": data.word_box_midX, 
            "box_midY": data.word_box_midY, 
            "box_width": data.word_box_width, 
            "box_height": data.word_box_height,
            "box_angle": data.word_box_angle} for data in self.extract_word_ids]

    @api.multi
    def remove_user_selected_box(self, id):
        """Set the selected box for a feature. The id of the box indicates the concerned feature.
        The method returns the text that can be set in the view (possibly different of the text in the file)"""
        self.ensure_one()
        word = self.env["account.invoice_extract.words"].browse(int(id))
        to_unselect = self.env["account.invoice_extract.words"].search([("invoice_id", "=", self.id), \
            ("field", "=", word.field), '|', ("user_selected", "=", True), ("selected_status", "!=", 0)])
        user_selected_found = False
        for box in to_unselect:
            if box.user_selected:
                user_selected_found = True
                box.user_selected = False
        ocr_new_value = 0
        new_word = None
        if user_selected_found:
            ocr_new_value = 1
        for box in to_unselect:
            if box.selected_status != 0:
                box.selected_status = ocr_new_value
                if ocr_new_value != 0:
                    new_word = box
        word.user_selected = False
        if new_word is None:
            if word.field == "total":
                return {
                    "line_id": self.invoice_line_ids[0].id if len(self.invoice_line_ids) == 1 else -1,
                    "total": 0.0,
                }
            if word.field in ["VAT_Number", "supplier", "currency"]:
                return 0
            return ""
        if new_word.field == "total":
            return {
                "line_id": self.invoice_line_ids[0].id if len(self.invoice_line_ids) == 1 else -1,
                "total": str(to_float(new_word.word_text)),
            }
        if new_word.field in ["date", "due_date", "invoice_id", "currency"]:
            pass
        #if "taxes" in result:
        #    box.amount_total = box.word_text
        if new_word.field == "VAT_Number":
            partner_vat = self.env["res.partner"].search([("vat", "=", new_word.word_text.replace(" ", ""))], limit=1)
            if partner_vat.exists():
                return partner_vat.id
            return 0
        if new_word.field == "supplier":
            partner_names = self.env["res.partner"].search([("name", "ilike", new_word.word_text)])
            if partner_names.exists():
                partner = min(partner_names, key=len)
                return partner.id
            else:
                partners = {}
                for single_word in new_word.word_text.split(" "):
                    partner_names = self.env["res.partner"].search([("name", "ilike", single_word)], limit=30)
                    for partner in partner_names:
                        partners[partner.id] = partners[partner.id] + 1 if partner.id in partners else 1
                if len(partners) > 0:
                    key_max = max(partners.keys(), key=(lambda k: partners[k]))
                    return key_max
            return 0
        return new_word.word_text.strip()

    @api.multi
    def set_user_selected_box(self, id):
        """Set the selected box for a feature. The id of the box indicates the concerned feature.
        The method returns the text that can be set in the view (possibly different of the text in the file)"""
        self.ensure_one()
        word = self.env["account.invoice_extract.words"].browse(int(id))
        to_unselect = self.env["account.invoice_extract.words"].search([("invoice_id", "=", self.id), ("field", "=", word.field), ("user_selected", "=", True)])
        for box in to_unselect:
            box.user_selected = False
        ocr_boxes = self.env["account.invoice_extract.words"].search([("invoice_id", "=", self.id), ("field", "=", word.field), ("selected_status", "=", 1)])
        for box in ocr_boxes:
            if box.selected_status != 0:
                box.selected_status = 2
        word.user_selected = True
        if word.field == "total":
            return {
                "line_id": self.invoice_line_ids[0].id if len(self.invoice_line_ids) == 1 else -1,
                "total": str(to_float(word.word_text)),
            }
        if word.field == "date":
            pass
        if word.field == "due_date":
            pass
        if word.field == "invoice_id":
            pass
        if word.field == "currency":
            text = word.word_text.strip()
            currency = None
            currencies = self.env["res.currency"].search([])
            for curr in currencies:
                if text == curr.currency_unit_label:
                    currency = curr
                if text.replace(" ", "") == curr.name or text.replace(" ", "") == curr.symbol:
                    currency = curr
            if currency.exists():
                return currency.id
            return ""
        #if "taxes" in result:
        #    box.amount_total = box.word_text
        if word.field == "VAT_Number":
            partner_vat = self.env["res.partner"].search([("vat", "=", word.word_text.replace(" ", ""))], limit=1)
            if partner_vat.exists():
                return partner_vat.id
            else:
                vat = word.word_text.replace(" ", "")
                url = '%s/check_vat' % PARTNER_REMOTE_URL
                params = {
                    'db_uuid': self.env['ir.config_parameter'].sudo().get_param('database.uuid'),
                    'vat': vat,
                }
                try:
                    response = jsonrpc(url=url, params=params)
                except Exception as exception:
                    _logger.error('Check VAT error: %s' % str(exception))
                    return 0

                if response and response.get('name'):
                    country_id = self.env['res.country'].search([('code', '=', response.pop('country_code',''))])
                    values = {field: response.get(field, None) for field in self._get_partner_fields()}
                    values.update({
                        'supplier': True,
                        'customer': False,
                        'is_company': True,
                        'country_id': country_id and country_id.id,
                        })
                    new_partner = self.env["res.partner"].create(values)
                    return new_partner.id
            return 0

        if word.field == "supplier":
            return self.find_partner_id_with_name(word.word_text)
        return word.word_text.strip()

    def _get_partner_fields(self): 
        return ['name','vat' ,'street', 'city', 'zip']
        

    @api.multi
    def _set_vat(self, text):
        partner_vat = self.env["res.partner"].search([("vat", "=", text.replace(" ", ""))], limit=1)
        if partner_vat.exists():
            self.partner_id = partner_vat
            return True
        return False

    @api.multi
    def find_partner_id_with_name(self, partner_name):
        partner_names = self.env["res.partner"].search([("name", "ilike", partner_name)])
        if partner_names.exists():
            partner = min(partner_names, key=len)
            return partner.id
        else:
            partners = {}
            for single_word in re.findall(r"[\w]+", partner_name):
                partner_names = self.env["res.partner"].search([("name", "ilike", single_word)], limit=30)
                for partner in partner_names:
                    partners[partner.id] = partners[partner.id] + 1 if partner.id in partners else 1
            if len(partners) > 0:
                key_max = max(partners.keys(), key=(lambda k: partners[k]))
                return key_max
        return 0

    @api.multi
    def set_field_with_text(self, field, text):
        """change a field with the data present in the text parameter"""
        self.ensure_one()
        if field == "total":
            if len(self.invoice_line_ids) == 1:
                self.invoice_line_ids[0].price_unit = to_float(text)
                self.invoice_line_ids[0].price_total = to_float(text)
            elif len(self.invoice_line_ids) == 0:
                self.invoice_line_ids.with_context(set_default_account=True, journal_id=self.journal_id.id).create({'name': "/",
                    'invoice_id': self.id,
                    'price_unit': to_float(text),
                    'price_total': to_float(text),
                    'quantity': 1,
                    })
                if getattr(self.invoice_line_ids[0],'_predict_account', False):
                    predicted_account_id = self.invoice_line_ids[0]._predict_account(text, self.invoice_line_ids[0].partner_id)
                    # We only change the account if we manage to predict its value
                    if predicted_account_id:
                        self.invoice_line_ids[0].account_id = predicted_account_id
                self.invoice_line_ids[0]._set_taxes()

        if field == "description":
            if len(self.invoice_line_ids) == 1:
                self.invoice_line_ids[0].name = text
                if getattr(self.invoice_line_ids[0],'_predict_account', False):
                    predicted_account_id = self.invoice_line_ids[0]._predict_account(text, self.invoice_line_ids[0].partner_id)
                    # We only change the account if we manage to predict its value
                    if predicted_account_id:
                        self.invoice_line_ids[0].account_id = predicted_account_id
                self.invoice_line_ids[0]._set_taxes()

            elif len(self.invoice_line_ids) == 0:
                self.invoice_line_ids.with_context(set_default_account=True, journal_id=self.journal_id.id).create({'name': text,
                    'invoice_id': self.id,
                    'price_unit': 0,
                    'price_total': 0,
                    'quantity': 1,
                    })
                if getattr(self.invoice_line_ids[0],'_predict_account', False):
                    predicted_account_id = self.invoice_line_ids[0]._predict_account(text, self.invoice_line_ids[0].partner_id)
                    # We only change the account if we manage to predict its value
                    if predicted_account_id:
                        self.invoice_line_ids[0].account_id = predicted_account_id
                self.invoice_line_ids[0]._set_taxes()

        if field == "date":
            self.date_invoice = text
        if field == "due_date":
            self.date_due = text
        if field == "invoice_id":
            self.reference = text.strip()
        if field == "currency" and self.user_has_groups('base.group_multi_currency'):
            text = text.strip()
            currency = None
            currencies = self.env["res.currency"].search([])
            for curr in currencies:
                if text == curr.currency_unit_label:
                    currency = curr
                if text.replace(" ", "") == curr.name or text.replace(" ", "") == curr.symbol:
                    currency = curr
            if currency:
                self.currency_id = currency.id
        #partner
        partner_found = False
        if field == "VAT_Number":
            partner_vat = self.env["res.partner"].search([("vat", "=", text.replace(" ", ""))], limit=1)
            if partner_vat.exists():
                self.partner_id = partner_vat
                self._onchange_partner_id()
                partner_found = True
        if not partner_found and field == "supplier":
            partner_id = self.find_partner_id_with_name(text)
            if partner_id != 0:
                self.partner_id = partner_id
                self._onchange_partner_id()

    @api.multi
    def check_status(self):
        """contact iap to get the actual status of the ocr request"""
        for record in self:
            if record.extract_state not in ["waiting_extraction", "extract_not_ready"]:
                continue
            endpoint = self.env['ir.config_parameter'].sudo().get_param(
                'account_invoice_extract_endpoint', 'https://iap-extract.odoo.com')  + '/iap/invoice_extract/get_result'
            params = {
                'version': CLIENT_OCR_VERSION,
                'document_id': record.extract_remoteid
            }
            result = jsonrpc(endpoint, params=params)
            if result == "Not ready":
                record.extract_state = "extract_not_ready"
            elif result == "An error occured":
                record.extract_state = "error_status"
            else:
                record.extract_state = "waiting_validation"
                self.extract_word_ids.unlink()
                if "supplier" in result: #be sure to execut supplier in first as it set some other values in invoice
                    self.set_field_with_text("supplier", result["supplier"]["selected_text"][0])
                for feature, value in result.items():
                    if feature != "supplier":
                        self.set_field_with_text(feature, value["selected_text"][0])
                    data = []
                    for word in value["words"]:
                        data.append((0, 0, {
                            "field": feature,
                            "selected_status": 1 if value["selected_text"] == word else 0,
                            "word_text": word[0],
                            "word_page": word[1],
                            "word_box_midX": word[2][0],
                            "word_box_midY": word[2][1],
                            "word_box_width": word[2][2],
                            "word_box_height": word[2][3],
                            "word_box_angle": word[2][4],
                        }))
                    self.write({'extract_word_ids': data})

    @api.multi
    def buy_credits(self):
        url = self.env['iap.account'].get_credits_url(base_url='', service_name='invoice_ocr')
        return {
            'type': 'ir.actions.act_url',
            'url': url,
        }
