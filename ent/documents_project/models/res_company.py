# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    dms_project_settings = fields.Boolean()
    project_folder = fields.Many2one('documents.folder',
                                     default=lambda self: self.env.ref('documents.documents_internal_folder',
                                                                       raise_if_not_found=False))
    project_tags = fields.Many2many('documents.tag', 'project_tags_table')

    @api.multi
    def write(self, values):
        for company in self:
            if not company.dms_project_settings and values.get('dms_project_settings'):
                attachments = self.env['ir.attachment'].search([('folder_id', '=', False),
                                                                ('res_model', 'in', ['project.project',
                                                                                     'project.task'])])
                if attachments.exists():
                    vals = {}
                    if values.get('project_folder'):
                        vals['folder_id'] = values['project_folder']
                    elif company.project_folder:
                        vals['folder_id'] = company.project_folder.id

                    if values.get('project_tags'):
                        vals['tag_ids'] = values['project_tags']
                    elif company.project_tags:
                        vals['tag_ids'] = [(6, 0, company.project_tags.ids)]
                    if len(vals):
                        attachments.write(vals)

        return super(ResCompany, self).write(values)
