# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def _set_folder_settings(self, vals):
        vals = super(IrAttachment, self)._set_folder_settings(vals)
        if vals.get('res_model') in ('product.template', 'product.product') \
                and self.env.user.company_id.dms_product_settings \
                and not vals.get('folder_id'):
            folder = self.env.user.company_id.product_folder
            if folder.exists():
                vals.setdefault('folder_id', folder.id)
                vals.setdefault('tag_ids', [(6, 0, self.env.user.company_id.product_tags.ids)])
        return vals
