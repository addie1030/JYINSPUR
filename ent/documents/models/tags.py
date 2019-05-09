# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import expression


class TagsCategories(models.Model):
    _name = "documents.facet"
    _description = "Facet"
    _order = "sequence, name"

    folder_id = fields.Many2one('documents.folder', ondelete="cascade")
    name = fields.Char(required=True)
    tag_ids = fields.One2many('documents.tag', 'facet_id')
    tooltip = fields.Char(help="hover text description", string="Tooltip")
    sequence = fields.Integer('Sequence', default=10)

    _sql_constraints = [
        ('name_unique', 'unique (folder_id, name)', "Facet already exists in this folder"),
    ]


class Tags(models.Model):
    _name = "documents.tag"
    _description = "Tag"
    _order = "sequence, name"

    folder_id = fields.Many2one('documents.folder', related='facet_id.folder_id', store=True, readonly=False)
    facet_id = fields.Many2one('documents.facet', ondelete='cascade', required=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)

    @api.multi
    def name_get(self):
        name_array = []
        for record in self:
            name_array.append((record.id, "%s > %s" % (record.facet_id.name, record.name)))
        return name_array

    _sql_constraints = [
        ('facet_name_unique', 'unique (facet_id, name)', "Tag already exists for this facet"),
    ]

    @api.model
    def group_by_documents(self, folder_id, domain=None):
        """
        fetches the tag and facet ids for the document selector (custom left sidebar of the kanban view)
        """
        if not domain:
            domain = []

        attachments = self.env['ir.attachment'].search(expression.AND([domain, [('folder_id', '=', folder_id)]]))
        folders = self.env['documents.folder'].search([('parent_folder_id', 'parent_of', folder_id)])
        query = """
            SELECT  facet.sequence AS facet_sequence,
                    facet.name AS facet_name,
                    facet.id AS facet_id,
                    facet.tooltip AS facet_tooltip,
                    documents_tag.sequence AS tag_sequence,
                    documents_tag.name AS tag_name,
                    documents_tag.id AS tag_id,
                    COUNT(rel.ir_attachment_id) AS __count
            FROM documents_tag
                JOIN documents_facet facet ON documents_tag.facet_id = facet.id
                    AND facet.folder_id = ANY(%s)
                LEFT JOIN document_tag_rel rel ON documents_tag.id = rel.documents_tag_id
                    AND rel.ir_attachment_id = ANY(%s)
            GROUP BY facet.sequence, facet.name, facet.id, facet.tooltip, documents_tag.sequence, documents_tag.name, documents_tag.id
            ORDER BY facet.sequence, facet.name, facet.id, facet.tooltip, documents_tag.sequence, documents_tag.name, documents_tag.id
        """
        params = [
            list(folders.ids),
            list(attachments.ids),  # using Postgresql's ANY() with a list to prevent empty list of attachments
        ]
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
