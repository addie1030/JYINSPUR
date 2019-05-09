# -*- coding: utf-8 -*-

import mimetypes

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError


class Slide(models.TransientModel):
    _name = "slide.upload.wizard"
    _description = 'Slide Upload Wizard'

    name = fields.Char('Title', required=True)
    file_name = fields.Char(string="Filename")
    description = fields.Text('Description')
    channel_id = fields.Many2one('slide.channel', string="Channel", required=True)
    category_id = fields.Many2one('slide.category', string="Category", domain="[('channel_id', '=', channel_id)]")
    tag_ids = fields.Many2many('slide.tag', 'rel_slide_wiz_tag', 'slide_id', 'tag_id', string='Tags')
    slide_type = fields.Selection([
        ('infographic', 'Infographic'),
        ('presentation', 'Presentation'),
        ('document', 'Document'),
        ('video', 'Video')],
        string='Type', required=True,
        default='document',
        help="The document type will be set automatically based on the document URL and properties (e.g. height and width for presentation and document).")
    datas = fields.Binary('Content')
    url = fields.Char('Document URL', help="Youtube or Google Document URL")
    mime_type = fields.Char('Mime-type')
    document_id = fields.Char('Document ID', help="Youtube or Google Document ID")

    @api.onchange('url')
    def on_change_url(self):
        '''Check enterd url is valid Youtube or Google Doc URL.'''
        if self.url:
            res = self.env['slide.slide']._parse_document_url(self.url)
            if res.get('error'):
                raise Warning(_('Could not fetch data from url. Document or access right not available:\n%s') % res['error'])
            values = res['values']
            if not values.get('document_id'):
                raise Warning(_('Please enter valid Youtube or Google Doc URL'))
            for key, value in values.items():
                self[key] = value

    @api.onchange('datas')
    def onchange_file_upload(self):
        if self.file_name and not self.url:
            self.mime_type = mimetypes.guess_type(self.file_name)[0]

    def _check_valid_file_type(self):
        if self.file_name and not self.url:
            if not self.mime_type or (self.mime_type and not self.mime_type.startswith('image/') and not self.mime_type.startswith('application/pdf')):
                raise UserError(_("Invalid file type. Please select pdf or image file"))
            if self.mime_type.startswith('image/'):
                # set slide type if file type is image.
                self.slide_type = 'infographic'
            if self.mime_type.startswith('application/pdf'):
                # user can set mannual slide type if file type is pdf.
                # Because of here complex to handle the code for find out uploded file is Document or Presentation.
                if self.slide_type in ['video', 'infographic']:
                    raise UserError(_("Invalid slide type. Please select document or presentation type."))

    @api.multi
    def upload_slide(self):
        '''create a new slide if does not exists in slide.slide model.
        set slide link if exists in model and message post in current channel.'''
        self.ensure_one()
        Slide = self.env['slide.slide']
        if self.url and self.document_id:
            Slide |= Slide.search([('document_id', '=', self.document_id)], limit=1)
        if Slide:
            msg = _('Already exists in %s : <a href="%s">click here to view it.</a>') % (Slide.channel_id.name, Slide.website_url)
        else:
            self._check_valid_file_type()
            val = {
                'name': self.name,
                'channel_id': self.channel_id.id,
                'category_id': self.category_id.id,
                'tag_ids': [(6, 0, self.tag_ids.ids)],
                'url': self.url,
                'slide_type': self.slide_type,
                'datas': self.datas,
                'mime_type': self.mime_type,
                'description': self.description,
            }
            slide = Slide.create(val)
            msg = _('Uploded new slide : <a href="%s">click here to view it.</a>') % (slide.website_url)
        channel = self.env['mail.channel'].browse(self.env.context.get('active_id'))
        return bool(channel.message_post(body=msg, subtype='mail.mt_comment'))
