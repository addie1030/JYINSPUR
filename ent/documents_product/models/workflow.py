# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class WorkflowActionRuleProduct(models.Model):
    _inherit = ['documents.workflow.rule']

    has_business_option = fields.Boolean(default=True, compute='_get_business')
    create_model = fields.Selection(selection_add=[('product.template', "Product template")])

    def create_record(self, attachments=None):
        rv = super(WorkflowActionRuleProduct, self).create_record(attachments=attachments)
        if self.create_model == 'product.template':
            new_obj = self.env[self.create_model].create({'name': 'product created from DMS'})

            for attachment in attachments:
                this_attachment = attachment
                if attachment.res_model or attachment.res_id:
                    this_attachment = attachment.copy()

                this_attachment.write({'res_model': self.create_model,
                                       'res_id': new_obj.id,
                                       'folder_id': this_attachment.folder_id.id})

            view_id = new_obj.get_formview_id()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'name': "New product template",
                'context': self._context,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, "form")],
                'res_id': new_obj.id if new_obj else False,
                'view_id': view_id,
            }
        return rv
