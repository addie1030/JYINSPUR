# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_default_project_folder(self):
        folder_id = self.env.user.company_id.project_folder
        if folder_id.exists():
            return folder_id
        return False

    dms_project_settings = fields.Boolean(related='company_id.dms_project_settings', readonly=False,
                                          default=lambda self: self.env.user.company_id.dms_project_settings,
                                          string="Project Folder")
    project_folder = fields.Many2one('documents.folder', related='company_id.project_folder', readonly=False,
                                     default=_get_default_project_folder,
                                     string="project default folder")
    project_tags = fields.Many2many('documents.tag', 'project_tags_table',
                                    related='company_id.project_tags', readonly=False,
                                    default=lambda self: self.env.user.company_id.project_tags.ids,
                                    string="Project Tags")


