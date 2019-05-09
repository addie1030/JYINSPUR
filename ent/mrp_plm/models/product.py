# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    version = fields.Integer('Version', default=1 ,help="The current version of the product.")
    eco_count = fields.Integer('# ECOs',compute='_compute_eco_count')
    eco_ids = fields.One2many('mrp.eco', 'product_tmpl_id', 'ECOs')
    template_attachment_count = fields.Integer('# Attachments', compute='_compute_attachments')

    @api.multi
    def _compute_eco_count(self):
        for p in self:
            p.eco_count = len(p.eco_ids)

    @api.multi
    def _compute_attachments(self):
        if not self.user_has_groups('mrp.group_mrp_user'):
            return
        for p in self:
            attachments = self.env['mrp.document'].search(['&', ('res_model', '=', 'product.template'), ('res_id', '=', p.id)])
            p.template_attachment_count = len(attachments)

    @api.multi
    def action_see_attachments(self):
        domain = ['&', ('res_model', '=', 'product.template'), ('res_id', '=', self.id)]
        attachment_view = self.env.ref('mrp.view_document_file_kanban_mrp')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'mrp.document',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.template', self.id)
        }

class ProductProduct(models.Model):
    _inherit = "product.product"

    product_attachment_count = fields.Integer('# Attachment', compute='_compute_attachments')

    def _get_documents(self):
        return [
            '|',
                '&',
                    ('res_model', '=', 'product.product'),
                    ('res_id', '=', self.id),
                '&',
                    ('res_model', '=', 'product.template'),
                    ('res_id', '=', self.product_tmpl_id.id)
        ]

    @api.multi
    def _compute_attachments(self):
        if not self.user_has_groups('mrp.group_mrp_user'):
            return
        for product in self:
            domain = product._get_documents()
            product.product_attachment_count = self.env['mrp.document'].search_count(domain)

    @api.multi
    def action_see_attachments(self):
        domain = self._get_documents()
        attachment_view = self.env.ref('mrp.view_document_file_kanban_mrp')
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'mrp.document',
            'type': 'ir.actions.act_window',
            'view_id': attachment_view.id,
            'views': [(attachment_view.id, 'kanban'), (False, 'form')],
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Upload files to your product
                    </p><p>
                        Use this feature to store any files, like drawings or specifications.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('product.product', self.id)
        }
