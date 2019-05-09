# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class SignRequest(models.Model):
    _inherit = ['sign.request']

    folder_id = fields.Many2one('documents.folder', 'Attachment Folder', related='template_id.folder_id', readonly=False)
    documents_tag_ids = fields.Many2many('documents.tag', string="Attachment Tags",
                                         related='template_id.documents_tag_ids', readonly=False)

