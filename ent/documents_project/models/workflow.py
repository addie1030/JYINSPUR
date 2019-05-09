# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class WorkflowActionRuleTask(models.Model):
    _inherit = ['documents.workflow.rule']

    has_business_option = fields.Boolean(default=True, compute='_get_business')
    create_model = fields.Selection(selection_add=[('project.task', "Task")])

    def create_record(self, attachments=None):
        rv = super(WorkflowActionRuleTask, self).create_record(attachments=attachments)
        if self.create_model == 'project.task':
            new_obj = self.env[self.create_model].create({'name': "new task from document management"})
            task_action = {
                'type': 'ir.actions.act_window',
                'res_model': self.create_model,
                'res_id': new_obj.id,
                'name': "new %s from %s" % (self.create_model, new_obj.name),
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(False, "form")],
                'context': self._context,
            }
            for attachment in attachments:
                this_attachment = attachment
                if attachment.res_model or attachment.res_id:
                    this_attachment = attachment.copy()

                this_attachment.write({'res_model': self.create_model,
                                       'res_id': new_obj.id,
                                       'folder_id': this_attachment.folder_id.id})
            return task_action
        return rv
