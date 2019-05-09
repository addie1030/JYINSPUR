# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.tools.translate import _
import uuid


class DocumentShare(models.Model):
    _name = 'documents.share'
    _inherit = ['mail.thread', 'mail.alias.mixin']
    _description = 'Documents Share'

    folder_id = fields.Many2one('documents.folder', required=True)
    name = fields.Char(string="Name")

    access_token = fields.Char(default=lambda x: str(uuid.uuid4()), groups="documents.group_documents_user")
    full_url = fields.Char(string="URL", compute='_compute_full_url')
    date_deadline = fields.Date(string="Valid Until")
    state = fields.Selection([
        ('live', "Live"),
        ('expired', "Expired"),
    ], default='live', compute='_compute_state', string="Status")

    type = fields.Selection([
        ('ids', "Document list"),
        ('domain', "Domain"),
    ], default='ids', string="Share type")
    # type == 'ids'
    attachment_ids = fields.Many2many('ir.attachment', string='Shared attachments')
    # type == 'domain'
    domain = fields.Char()

    action = fields.Selection([
        ('download', "Download"),
        ('downloadupload', "Download and Upload"),
    ], default='download', string="Allows to")
    tag_ids = fields.Many2many('documents.tag', string="Shared Tags")
    partner_id = fields.Many2one('res.partner', string="Contact")
    owner_id = fields.Many2one('res.users', string="Document Owner")
    email_drop = fields.Boolean(string='Upload by Email')

    # Activity
    activity_option = fields.Boolean(string='Create a new activity')
    activity_type_id = fields.Many2one('mail.activity.type', string="Activity type")
    activity_summary = fields.Char('Summary')
    activity_date_deadline_range = fields.Integer(string='Due Date In')
    activity_date_deadline_range_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Due type', default='days')
    activity_note = fields.Html(string="Note")
    activity_user_id = fields.Many2one('res.users', string='Responsible')

    _sql_constraints = [
        ('share_unique', 'unique (access_token)', "This access token already exists"),
    ]

    @api.multi
    def name_get(self):
        name_array = []
        for record in self:
            name_array.append((record.id, record.name or "unnamed link"))
        return name_array

    def _compute_state(self):
        """
        changes the state based on the expiration date,
         an expired share link cannot be used to upload or download files.
        """
        for record in self:
            record.state = 'live'
            if record.date_deadline:
                today = fields.Date.from_string(fields.Date.today())
                exp_date = fields.Date.from_string(record.date_deadline)
                diff_time = (exp_date - today).days
                if diff_time <= 0:
                    record.state = 'expired'

    def get_alias_model_name(self, vals):
        return vals.get('alias_model', 'ir.attachment')

    @api.multi
    def _compute_alias_domain(self):
        alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")
        for record in self:
            record.alias_domain = alias_domain

    @api.multi
    @api.onchange('access_token')
    def _compute_full_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.full_url = "%s/document/share/%s/%s" % (base_url, record.id, record.access_token)

    @api.multi
    def update_alias_defaults(self):
        for share in self:
            values = {
                'tag_ids': [(6, 0, self.tag_ids.ids)],
                'folder_id': self.folder_id.id,
                'partner_id': self.partner_id.id,
            }
            share.alias_id.alias_defaults = values

    @api.multi
    def write(self, vals):
        result = super(DocumentShare, self).write(vals)
        self.update_alias_defaults()
        return result

    @api.model
    def create(self, vals):
        if 'owner_id' not in vals:
            vals['owner_id'] = self.env.uid
        share = super(DocumentShare, self).create(vals)
        share.update_alias_defaults()
        return share

    @api.model
    def create_share(self, vals):
        """
        creates a share link and returns a view.
        :return: a form action that opens the share window to display the URL and the settings.
        """

        share = self.create(vals)
        view_id = self.env.ref('documents.share_view_form_popup').id
        return {
            'context': self._context,
            'res_model': 'documents.share',
            'target': 'new',
            'name': _('Share'),
            'res_id': share.id,
            'type': 'ir.actions.act_window',
            'views': [[view_id, 'form']],
        }
