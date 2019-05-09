# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def _set_folder_settings(self, vals):
        vals = super(IrAttachment, self)._set_folder_settings(vals)
        if vals.get('res_model') == 'account.invoice' \
                and self.env.user.company_id.dms_account_settings \
                and not vals.get('folder_id'):
            folder = self.env.user.company_id.account_folder
            if folder.exists():
                vals.setdefault('folder_id', folder.id)
                vals.setdefault('tag_ids', [(6, 0, self.env.user.company_id.account_tags.ids)])
        return vals
