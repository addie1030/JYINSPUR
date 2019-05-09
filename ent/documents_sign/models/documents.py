# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def _set_folder_settings(self, vals):
        vals = super(IrAttachment, self)._set_folder_settings(vals)
        if vals.get('res_model') in ['sign.request', 'sign.template'] \
                and vals.get('res_id') \
                and not vals.get('folder_id'):
            record = self.env[vals['res_model']].browse(vals.get('res_id'))
            if record.exists():
                vals.setdefault('folder_id', record.folder_id.id)
                vals.setdefault('tag_ids', [(6, 0, record.documents_tag_ids.ids)])
        return vals
