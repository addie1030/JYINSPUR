# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_default_product_folder(self):
        return self.env.ref('documents_product_folder', raise_if_not_found=False)

    dms_product_settings = fields.Boolean()
    product_folder = fields.Many2one('documents.folder', default=_get_default_product_folder)
    product_tags = fields.Many2many('documents.tag', 'product_tags_table')

    @api.multi
    def write(self, values):
        for company in self:
            if not company.dms_product_settings and values.get('dms_product_settings'):
                attachments = self.env['ir.attachment'].search([('folder_id', '=', False),
                                                                ('res_model', 'in', ['product.product',
                                                                                     'product.template'])])
                if attachments.exists():
                    vals = {}
                    if values.get('product_folder'):
                        vals['folder_id'] = values['product_folder']
                    elif company.product_folder:
                        vals['folder_id'] = company.product_folder.id

                    if values.get('product_tags'):
                        vals['tag_ids'] = values['product_tags']
                    elif company.product_tags:
                        vals['tag_ids'] = [(6, 0, company.product_tags.ids)]
                    if len(vals):
                        attachments.write(vals)

        return super(ResCompany, self).write(values)
