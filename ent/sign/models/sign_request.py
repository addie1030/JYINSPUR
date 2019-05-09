# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import time
import uuid

from email.utils import formataddr
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from werkzeug.urls import url_join
from random import randint

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

def _fix_image_transparency(image):
    """ Modify image transparency to minimize issue of grey bar artefact.

    When an image has a transparent pixel zone next to white pixel zone on a
    white background, this may cause on some renderer grey line artefacts at
    the edge between white and transparent.

    This method sets transparent pixel to white transparent pixel which solves
    the issue for the most probable case. With this the issue happen for a
    black zone on black background but this is less likely to happen.
    """
    pixels = image.load()
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            if pixels[x, y] == (0, 0, 0, 0):
                pixels[x, y] = (255, 255, 255, 0)

class SignRequest(models.Model):
    _name = "sign.request"
    _description = "Signature Request"
    _rec_name = 'reference'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    def _default_access_token(self):
        return str(uuid.uuid4())

    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    template_id = fields.Many2one('sign.template', string="Template", required=True)
    reference = fields.Char(required=True, string="Filename")

    access_token = fields.Char('Security Token', required=True, default=_default_access_token, readonly=True)

    request_item_ids = fields.One2many('sign.request.item', 'sign_request_id', string="Signers")
    state = fields.Selection([
        ("sent", "Signatures in Progress"),
        ("signed", "Fully Signed"),
        ("canceled", "Canceled")
    ], default='sent', track_visibility='onchange', group_expand='_expand_states')

    completed_document = fields.Binary(readonly=True, string="Completed Document", attachment=True)

    nb_wait = fields.Integer(string="Sent Requests", compute="_compute_count", store=True)
    nb_closed = fields.Integer(string="Completed Signatures", compute="_compute_count", store=True)
    nb_total = fields.Integer(string="Requested Signatures", compute="_compute_count", store=True)
    progress = fields.Integer(string="Progress", compute="_compute_count")

    active = fields.Boolean(default=True, string="Active", oldname='archived')
    favorited_ids = fields.Many2many('res.users', string="Favorite of")

    color = fields.Integer()
    request_item_infos = fields.Binary(compute="_compute_request_item_infos")
    last_action_date = fields.Datetime(related="message_ids.create_date", readonly=True, string="Last Action Date")

    @api.one
    @api.depends('request_item_ids.state')
    def _compute_count(self):
        wait, closed = 0, 0
        for s in self.request_item_ids:
            if s.state == "sent":
                wait += 1
            if s.state == "completed":
                closed += 1
        self.nb_wait = wait
        self.nb_closed = closed
        self.nb_total = wait + closed

        if self.nb_wait + self.nb_closed <= 0:
            self.progress = 0
        else:
            self.progress = self.nb_closed*100 / (self.nb_total)

    @api.one
    @api.depends('request_item_ids.state', 'request_item_ids.partner_id.name')
    def _compute_request_item_infos(self):
        infos = []
        for item in self.request_item_ids:
            infos.append({
                'partner_name': item.partner_id.name if item.partner_id else 'Public User',
                'state': item.state,
            })
        self.request_item_infos = infos

    @api.one
    def _check_after_compute(self):
        if self.state == 'sent' and self.nb_closed == len(self.request_item_ids) and len(self.request_item_ids) > 0: # All signed
            self.action_signed()

    @api.multi
    def button_send(self):
        self.action_sent()

    @api.multi
    def go_to_document(self):
        self.ensure_one()
        request_item = self.request_item_ids.filtered(lambda r: r.partner_id and r.partner_id.id == self.env.user.partner_id.id)[:1]
        return {
            'name': "Document \"%(name)s\"" % {'name': self.reference},
            'type': 'ir.actions.client',
            'tag': 'sign.Document',
            'context': {
                'id': self.id,
                'token': self.access_token,
                'sign_token': request_item.access_token if request_item and request_item.state == "sent" else None,
                'create_uid': self.create_uid.id,
                'state': self.state,
            },
        }

    def open_sign_request(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sign.request",
            "views": [[False, "form"]],
            "res_id": self.id,
        }

    @api.multi
    def get_completed_document(self):
        self.ensure_one()
        if not self.completed_document:
            self.generate_completed_document()

        return {
            'name': 'Signed Document',
            'type': 'ir.actions.act_url',
            'url': '/sign/download/%(request_id)s/%(access_token)s/completed' % {'request_id': self.id, 'access_token': self.access_token},
        }

    @api.multi
    def toggle_favorited(self):
        self.ensure_one()
        self.write({'favorited_ids': [(3 if self.env.user in self[0].favorited_ids else 4, self.env.user.id)]})

    @api.multi
    def action_resend(self):
        self.action_draft()
        subject = _("Signature Request - %s") % (self.template_id.attachment_id.name)
        self.action_sent(subject=subject)

    @api.multi
    def action_draft(self):
        self.write({'completed_document': None, 'access_token': self._default_access_token()})

    @api.multi
    def action_sent(self, subject=None, message=None):
        self.write({'state': 'sent'})
        for sign_request in self:
            ignored_partners = []
            for request_item in sign_request.request_item_ids:
                if request_item.state != 'draft':
                    ignored_partners.append(request_item.partner_id.id)
            included_request_items = sign_request.request_item_ids.filtered(lambda r: not r.partner_id or r.partner_id.id not in ignored_partners)

            if sign_request.send_signature_accesses(subject, message, ignored_partners=ignored_partners):
                followers = sign_request.message_follower_ids.mapped('partner_id')
                followers -= sign_request.create_uid.partner_id
                followers -= sign_request.request_item_ids.mapped('partner_id')
                if followers:
                    sign_request.send_follower_accesses(followers, subject, message)
                included_request_items.action_sent()
            else:
                sign_request.action_draft()

    @api.multi
    def action_signed(self):
        self.write({'state': 'signed'})
        self.env.cr.commit()
        self.send_completed_document()

    @api.multi
    def action_canceled(self):
        self.write({'completed_document': None, 'access_token': self._default_access_token(), 'state': 'canceled'})
        for request_item in self.mapped('request_item_ids'):
            request_item.action_draft()

    @api.one
    def set_signers(self, signers):
        self.request_item_ids.filtered(lambda r: not r.partner_id or not r.role_id).unlink()

        ids_to_remove = []
        for request_item in self.request_item_ids:
            for i in range(0, len(signers)):
                if signers[i]['partner_id'] == request_item.partner_id.id and signers[i]['role'] == request_item.role_id.id:
                    signers.pop(i)
                    break
            else:
                ids_to_remove.append(request_item.id)

        SignRequestItem = self.env['sign.request.item']
        SignRequestItem.browse(ids_to_remove).unlink()
        for signer in signers:
            SignRequestItem.create({
                'partner_id': signer['partner_id'],
                'sign_request_id': self.id,
                'role_id': signer['role'],
            })

    @api.multi
    def send_signature_accesses(self, subject=None, message=None, ignored_partners=[]):
        self.ensure_one()
        if len(self.request_item_ids) <= 0 or (set(self.request_item_ids.mapped('role_id')) != set(self.template_id.sign_item_ids.mapped('responsible_id'))):
            return False

        self.request_item_ids.filtered(lambda r: not r.partner_id or r.partner_id.id not in ignored_partners).send_signature_accesses(subject, message)
        return True

    @api.one
    def send_follower_accesses(self, followers, subject=None, message=None):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        tpl = self.env.ref('sign.sign_template_mail_follower')
        body = tpl.render({
            'record': self,
            'link': url_join(base_url, 'sign/document/%s/%s' % (self.id, self.access_token)),
            'subject': subject,
            'body': message,
        }, engine='ir.qweb', minimal_qcontext=True)
        for follower in followers:
            if not follower.email:
                continue
            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': self.reference},
                {'model_description': 'signature', 'company': self.create_uid.company_id},
                {'email_from': formataddr((self.create_uid.name, self.create_uid.email)),
                 'email_to': formataddr((follower.name, follower.email)),
                 'subject': subject or _('%s : Signature request') % self.reference}
            )
            self.message_subscribe(partner_ids=follower.ids)

    @api.multi
    def send_completed_document(self):
        self.ensure_one()
        if len(self.request_item_ids) <= 0 or self.state != 'signed':
            return False

        if not self.completed_document:
            self.generate_completed_document()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for signer in self.request_item_ids:
            if not signer.partner_id or not signer.partner_id.email:
                continue

            tpl = self.env.ref('sign.sign_template_mail_completed')
            body = tpl.render({
                'record': self,
                'link': url_join(base_url, 'sign/document/%s/%s' % (self.id, signer.access_token)),
                'subject': '%s signed' % self.reference,
                'body': False,
            }, engine='ir.qweb', minimal_qcontext=True)

            attachment = self.env['ir.attachment'].create({
                'name': self.reference,
                'datas_fname': "%s.pdf" % self.reference,
                'datas': self.completed_document,
                'type': 'binary',
                'res_model': self._name,
                'res_id': self.id,
            })

            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': self.reference},
                {'model_description': 'signature', 'company': self.create_uid.company_id},
                {'email_from': formataddr((self.create_uid.name, self.create_uid.email)),
                 'email_to': formataddr((signer.partner_id.name, signer.partner_id.email)),
                 'subject': _('%s has been signed') % self.reference,
                 'attachment_ids': [(4, attachment.id)]}
            )

        tpl = self.env.ref('sign.sign_template_mail_completed')
        body = tpl.render({
            'record': self,
            'link': url_join(base_url, 'sign/document/%s/%s' % (self.id, self.access_token)),
            'subject': '%s signed' % self.reference,
            'body': '',
        }, engine='ir.qweb', minimal_qcontext=True)

        for follower in self.mapped('message_follower_ids.partner_id') - self.request_item_ids.mapped('partner_id'):
            if not follower.email:
                continue
            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': self.reference},
                {'model_description': 'signature', 'company': self.create_uid.company_id},
                {'email_from': formataddr((self.create_uid.name, self.create_uid.email)),
                 'email_to': formataddr((follower.name, follower.email)),
                 'subject': _('%s has been signed') % self.reference}
            )

        return True

    @api.one
    def generate_completed_document(self):
        if len(self.template_id.sign_item_ids) <= 0:
            self.completed_document = self.template_id.attachment_id.datas
            return

        old_pdf = PdfFileReader(io.BytesIO(base64.b64decode(self.template_id.attachment_id.datas)), strict=False, overwriteWarnings=False)
        font = "Helvetica"
        normalFontSize = 0.015

        packet = io.BytesIO()
        can = canvas.Canvas(packet)
        itemsByPage = self.template_id.sign_item_ids.getByPage()
        SignItemValue = self.env['sign.item.value']
        for p in range(0, old_pdf.getNumPages()):
            page = old_pdf.getPage(p)
            width = float(page.mediaBox.getUpperRight_x())
            height = float(page.mediaBox.getUpperRight_y())

            # Set page orientation (either 0, 90, 180 or 270)
            rotation = page.get('/Rotate')
            if rotation:
                can.rotate(rotation)
                # Translate system so that elements are placed correctly
                # despite of the orientation
                if rotation == 90:
                    width, height = height, width
                    can.translate(0, -height)
                elif rotation == 180:
                    can.translate(-width, -height)
                elif rotation == 270:
                    width, height = height, width
                    can.translate(-width, 0)

            items = itemsByPage[p + 1] if p + 1 in itemsByPage else []
            for item in items:
                value = SignItemValue.search([('sign_item_id', '=', item.id), ('sign_request_id', '=', self.id)], limit=1)
                if not value or not value.value:
                    continue

                value = value.value

                if item.type_id.type == "text":
                    can.setFont(font, height*item.height*0.8)
                    can.drawString(width*item.posX, height*(1-item.posY-item.height*0.9), value)

                elif item.type_id.type == "textarea":
                    can.setFont(font, height*normalFontSize*0.8)
                    lines = value.split('\n')
                    y = (1-item.posY)
                    for line in lines:
                        y -= normalFontSize*0.9
                        can.drawString(width*item.posX, height*y, line)
                        y -= normalFontSize*0.1

                elif item.type_id.type == "checkbox":
                    can.setFont(font, height*item.height*0.8)
                    value = 'X' if value == 'on' else ''
                    can.drawString(width*item.posX, height*(1-item.posY-item.height*0.9), value)

                elif item.type_id.type == "signature" or item.type_id.type == "initial":
                    image_reader = ImageReader(io.BytesIO(base64.b64decode(value[value.find(',')+1:])))
                    _fix_image_transparency(image_reader._image)
                    can.drawImage(image_reader, width*item.posX, height*(1-item.posY-item.height), width*item.width, height*item.height, 'auto', True)

            can.showPage()

        can.save()

        item_pdf = PdfFileReader(packet, overwriteWarnings=False)
        new_pdf = PdfFileWriter()

        for p in range(0, old_pdf.getNumPages()):
            page = old_pdf.getPage(p)
            page.mergePage(item_pdf.getPage(p))
            new_pdf.addPage(page)

        output = io.BytesIO()
        new_pdf.write(output)
        self.completed_document = base64.b64encode(output.getvalue())
        output.close()

    @api.model
    def _message_send_mail(self, body, notif_template_xmlid, message_values, notif_values, mail_values, **kwargs):
        """ Shortcut to send an email. """
        msg = self.env['mail.message'].sudo().new(dict(body=body, **message_values))

        notif_layout = self.env.ref(notif_template_xmlid)
        body_html = notif_layout.render(dict(message=msg, **notif_values), engine='ir.qweb', minimal_qcontext=True)
        body_html = self.env['mail.thread']._replace_local_links(body_html)

        return self.env['mail.mail'].create(dict(body_html=body_html, state='outgoing', **mail_values))

    @api.model
    def initialize_new(self, id, signers, followers, reference, subject, message, send=True):
        sign_request = self.create({'template_id': id, 'reference': reference, 'favorited_ids': [(4, self.env.user.id)]})
        sign_request.message_subscribe(partner_ids=followers)
        sign_request.set_signers(signers)
        if send:
            sign_request.action_sent(subject, message)
        return {
            'id': sign_request.id,
            'token': sign_request.access_token,
            'sign_token': sign_request.request_item_ids.filtered(lambda r: r.partner_id == self.env.user.partner_id)[:1].access_token,
        }

    @api.model
    def add_followers(self, id, followers):
        sign_request = self.browse(id)
        old_followers = set(sign_request.message_follower_ids.mapped('partner_id.id'))
        followers = list(set(followers) - old_followers)
        if followers:
            sign_request.message_subscribe(partner_ids=followers)
            sign_request.send_follower_accesses(self.env['res.partner'].browse(followers))
        return sign_request.id


class SignRequestItem(models.Model):
    _name = "sign.request.item"
    _description = "Signature Request Item"
    _rec_name = 'partner_id'

    @api.multi
    def _default_access_token(self):
        return str(uuid.uuid4())

    partner_id = fields.Many2one('res.partner', string="Partner", ondelete='cascade')
    sign_request_id = fields.Many2one('sign.request', string="Signature Request", ondelete='cascade', required=True)

    access_token = fields.Char('Security Token', required=True, default=_default_access_token, readonly=True)
    role_id = fields.Many2one('sign.item.role', string="Role")
    sms_number = fields.Char(related='partner_id.mobile', readonly=False)
    sms_token = fields.Char('SMS Token', readonly=True)

    signature = fields.Binary(attachment=True)
    signing_date = fields.Date('Signed on', readonly=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Waiting for completion"),
        ("completed", "Completed")
    ], readonly=True, default="draft")

    signer_email = fields.Char(related='partner_id.email', readonly=False)

    latitude = fields.Float(digits=(10, 7))
    longitude = fields.Float(digits=(10, 7))

    @api.multi
    def action_draft(self):
        self.write({
            'signature': None,
            'signing_date': None,
            'access_token': self._default_access_token(),
            'state': 'draft',
        })
        for request_item in self:
            itemsToClean = request_item.sign_request_id.template_id.sign_item_ids.filtered(lambda r: r.responsible_id == request_item.role_id or not r.responsible_id)
            self.env['sign.item.value'].search([('sign_item_id', 'in', itemsToClean.mapped('id')), ('sign_request_id', '=', request_item.sign_request_id.id)]).unlink()
        self.mapped('sign_request_id')._check_after_compute()

    @api.multi
    def action_sent(self):
        self.write({'state': 'sent'})
        self.mapped('sign_request_id')._check_after_compute()

    @api.multi
    def action_completed(self):
        self.write({'signing_date': time.strftime(DEFAULT_SERVER_DATE_FORMAT), 'state': 'completed'})
        self.mapped('sign_request_id')._check_after_compute()

    @api.multi
    def send_signature_accesses(self, subject=None, message=None):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for signer in self:
            if not signer.partner_id or not signer.partner_id.email:
                continue
            if not signer.create_uid.email:
                continue
            tpl = self.env.ref('sign.sign_template_mail_request')
            body = tpl.render({
                'record': signer,
                'link': url_join(base_url, "sign/document/%(request_id)s/%(access_token)s" % {'request_id': signer.sign_request_id.id, 'access_token': signer.access_token}),
                'subject': subject,
                'body': message if message != '<p><br></p>' else False,
            }, engine='ir.qweb', minimal_qcontext=True)

            self.env['sign.request']._message_send_mail(
                body, 'mail.mail_notification_light',
                {'record_name': signer.sign_request_id.reference},
                {'model_description': 'signature', 'company': signer.create_uid.company_id},
                {'email_from': formataddr((signer.create_uid.name, signer.create_uid.email)),
                 'email_to': formataddr((signer.partner_id.name, signer.partner_id.email)),
                 'subject': subject}
            )

    @api.multi
    def sign(self, signature):
        self.ensure_one()
        if not isinstance(signature, dict):
            self.signature = signature
        else:
            SignItemValue = self.env['sign.item.value']
            request = self.sign_request_id

            signerItems = request.template_id.sign_item_ids.filtered(lambda r: not r.responsible_id or r.responsible_id.id == self.role_id.id)
            autorizedIDs = set(signerItems.mapped('id'))
            requiredIDs = set(signerItems.filtered('required').mapped('id'))

            itemIDs = {int(k) for k in signature}
            if not (itemIDs <= autorizedIDs and requiredIDs <= itemIDs): # Security check
                return False

            user = self.env['res.users'].search([('partner_id', '=', self.partner_id.id)], limit=1).sudo()
            for itemId in signature:
                item_value = SignItemValue.search([('sign_item_id', '=', int(itemId)), ('sign_request_id', '=', request.id)])
                if not item_value:
                    item_value = SignItemValue.create({'sign_item_id': int(itemId), 'sign_request_id': request.id, 'value': signature[itemId]})
                    if item_value.sign_item_id.type_id.type == 'signature':
                        self.signature = signature[itemId][signature[itemId].find(',')+1:]
                        if user:
                            user.sign_signature = self.signature
                    if item_value.sign_item_id.type_id.type == 'initial' and user:
                        user.sign_initials = signature[itemId][signature[itemId].find(',')+1:]

        return True

    @api.model
    def resend_access(self, id):
        sign_request_item = self.browse(id)
        subject = _("Signature Request - %s") % (sign_request_item.sign_request_id.template_id.attachment_id.name)
        self.browse(id).send_signature_accesses(subject=subject)

    @api.multi
    def _reset_sms_token(self):
        for record in self:
            record.sms_token = randint(100000, 999999)

    @api.one
    def _send_sms(self):
        self.ensure_one()
        self._reset_sms_token()
        self.env['sms.api']._send_sms([self.sms_number], _('Your confirmation code is %s') % self.sms_token)
