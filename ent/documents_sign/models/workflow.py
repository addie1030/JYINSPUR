# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class WorkflowActionRuleSign(models.Model):
    _inherit = ['documents.workflow.rule']

    has_business_option = fields.Boolean(default=True, compute='_get_business')
    create_model = fields.Selection(selection_add=[('sign.template', "Signature template")])

    def create_record(self, attachments=None):
        rv = super(WorkflowActionRuleSign, self).create_record(attachments=attachments)
        if self.create_model == 'sign.template':
            new_obj = None
            template_ids = []
            for attachment in attachments:
                create_values = {
                    'name': attachment.datas_fname[:attachment.datas_fname.rfind('.')],
                    'attachment_id': attachment.id,
                }
                if self.folder_id:
                    create_values['folder_id'] = self.folder_id.id
                elif self.domain_folder_id:
                    create_values['folder_id'] = self.domain_folder_id.id
                if attachment.tag_ids:
                    create_values['documents_tag_ids'] = [(6, 0, attachment.tag_ids.ids)]

                new_obj = self.env[self.create_model].create(create_values)

                this_attachment = attachment
                if attachment.res_model or attachment.res_id:
                    this_attachment = attachment.copy()

                this_attachment.write({'res_model': self.create_model,
                                       'res_id': new_obj.id,
                                       'folder_id': this_attachment.folder_id.id})

                template_ids.append(new_obj.id)

            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'sign.template',
                'name': "New templates",
                'view_id': False,
                'view_type': 'list',
                'view_mode': 'kanban',
                'views': [(False, "kanban"), (False, "form")],
                'domain': [('id', 'in', template_ids)],
                'context': self._context,
            }
            if len(attachments) == 1:
                return new_obj.go_to_custom_template()
            return action
        return rv
