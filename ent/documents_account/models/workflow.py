# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class WorkflowActionRuleAccount(models.Model):
    _inherit = ['documents.workflow.rule']

    has_business_option = fields.Boolean(default=True, compute='_get_business')
    create_model = fields.Selection(selection_add=[('account.invoice.in_invoice', "Vendor bill"),
                                                   ('account.invoice.out_refund', "Credit note"),
                                                   ('account.invoice.in_refund', 'Vendor Credit Note')])

    def create_record(self, attachments=None):
        rv = super(WorkflowActionRuleAccount, self).create_record(attachments=attachments)
        if self.create_model.startswith('account.invoice'):
            invoice_type = self.create_model.split('.')[2]
            journal = self.env['account.invoice'].with_context({'type': invoice_type})._default_journal()
            new_obj = None
            invoice_ids = []
            for attachment in attachments:
                create_values = {
                    'type': invoice_type,
                    'journal_id': journal.id,
                }
                if invoice_type != 'out_refund':
                    create_values['comment'] = False

                if self.partner_id:
                    create_values.update(partner_id=self.partner_id.id)
                elif attachment.partner_id:
                    create_values.update(partner_id=attachment.partner_id.id)

                new_obj = self.env['account.invoice'].create(create_values)
                body = "<p>created with DMS</p>"
                new_obj.message_post(body=body, attachment_ids=[attachment.id])
                this_attachment = attachment
                if attachment.res_model or attachment.res_id:
                    this_attachment = attachment.copy()

                this_attachment.write({'res_model': 'account.invoice',
                                       'res_id': new_obj.id,
                                       'folder_id': this_attachment.folder_id.id})

                invoice_ids.append(new_obj.id)

            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'name': "Invoices",
                'view_id': False,
                'view_type': 'list',
                'view_mode': 'tree',
                'views': [(False, "list"), (False, "form")],
                'domain': [('id', 'in', invoice_ids)],
                'context': self._context,
            }
            if len(attachments) == 1:
                view_id = new_obj.get_formview_id() if new_obj else False
                action.update({'view_type': 'form',
                               'view_mode': 'form',
                               'views': [(view_id, "form")],
                               'res_id': new_obj.id if new_obj else False,
                               'view_id': view_id,
                               })
            return action
        return rv
