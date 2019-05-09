# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class SignTemplate(models.Model):
    _inherit = ['sign.template']

    folder_id = fields.Many2one('documents.folder', 'Attachment Folder')
    documents_tag_ids = fields.Many2many('documents.tag', string="Attachment Tags")

