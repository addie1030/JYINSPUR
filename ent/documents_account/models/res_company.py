# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    dms_account_settings = fields.Boolean()
    account_folder = fields.Many2one('documents.folder',
                                     default=lambda self: self.env.ref('documents.documents_finance_folder',
                                                                       raise_if_not_found=False))
    account_tags = fields.Many2many('documents.tag', 'account_tags_table')

    @api.multi
    def write(self, values):
        for company in self:
            if not company.dms_account_settings and values.get('dms_account_settings'):
                attachments = self.env['ir.attachment'].search([('folder_id', '=', False),
                                                                ('res_model', '=', 'account.invoice')])
                if attachments.exists():
                    vals = {}
                    if values.get('account_folder'):
                        vals['folder_id'] = values['account_folder']
                    elif company.account_folder:
                        vals['folder_id'] = company.account_folder.id

                    if values.get('account_tags'):
                        vals['tag_ids'] = values['account_tags']
                    elif company.account_tags:
                        vals['tag_ids'] = [(6, 0, company.account_tags.ids)]
                    if len(vals):
                        attachments.write(vals)

        return super(ResCompany, self).write(values)
