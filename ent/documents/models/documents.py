# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, SUPERUSER_ID, modules
from ast import literal_eval
from dateutil.relativedelta import relativedelta
import base64


class IrAttachment(models.Model):
    _name = 'ir.attachment'
    _description = 'Document'
    _inherit = ['ir.attachment', 'mail.thread', 'mail.activity.mixin']

    type = fields.Selection(selection_add=[('empty', "Empty")])
    favorited_ids = fields.Many2many('res.users', string="Favorite of")
    tag_ids = fields.Many2many('documents.tag', 'document_tag_rel', string="Tags")
    partner_id = fields.Many2one('res.partner', string="Contact", track_visibility='onchange')
    owner_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string="Owner",
                               track_visibility='onchange')
    available_rule_ids = fields.Many2many('documents.workflow.rule', compute='_compute_available_rules',
                                          string='Available Rules')
    folder_id = fields.Many2one('documents.folder', ondelete="restrict", track_visibility="onchange", index=True)
    lock_uid = fields.Many2one('res.users', string="Locked by")

    # AND
    @api.model
    def check(self, mode, values=None):
        super(IrAttachment, self).check(mode, values)
        if self:
            # Upstream check did not raise, so default access is granted.
            # Now perform extra check for folder permissions in the case of files that
            # are not attached to a specific business document (when attached, the permissions
            # of the business document prevail)
            self._cr.execute('''
                SELECT folder_id 
                  FROM ir_attachment
                 WHERE id IN %s AND
                       folder_id IS NOT NULL AND
                       res_id IS NULL AND
                       res_model IS NULL AND
                       (public = false OR public IS NULL)
              GROUP BY folder_id
            ''', [tuple(self.ids)])
            folder_ids = [r[0] for r in self._cr.fetchall()]
            if values and values.get('folder_id'):
                folder_ids.append(values['folder_id'])

            if len(folder_ids):
                # Forbid deleting attachments unless the user has write access to the folder.
                # All other operations are permitted if the user has read access to the folder.
                folders = self.env['documents.folder'].browse(folder_ids).exists()
                folders.check_access_rights('write' if mode == 'unlink' else 'read')
                folders.check_access_rule(mode)

    @api.onchange('url')
    def _on_url_change(self):
        if self.url:
            self.name = self.url[self.url.rfind('/')+1:]

    @api.multi
    def _compute_available_rules(self, folder_id=None):
        """
        loads the rules that can be applied to the attachment.

        :param folder_id: the id of the current folder (used to lighten the search)
        """
        if not folder_id and self[0].folder_id:
            folder_id = self[0].folder_id.id
        rule_domain = [('domain_folder_id', 'parent_of', folder_id)] if folder_id else []
        rules = self.env['documents.workflow.rule'].search(rule_domain)
        for rule in rules:
            domain = []
            if rule.condition_type == 'domain':
                domain = literal_eval(rule.domain) if rule.domain else []
            else:
                if rule.criteria_partner_id:
                    domain += [['partner_id', '=', rule.criteria_partner_id.id]]
                if rule.criteria_owner_id:
                    domain += [['owner_id', '=', rule.criteria_owner_id.id]]
                if rule.create_model:
                    domain += [['type', '=', 'binary']]
                if rule.criteria_tag_ids:
                    contains_array = []
                    not_contains_array = []
                    for criteria_tag in rule.criteria_tag_ids:
                        if criteria_tag.operator == 'contains':
                            contains_array.append(criteria_tag.tag_id.id)
                        elif criteria_tag.operator == 'notcontains':
                            not_contains_array.append(criteria_tag.tag_id.id)
                    if len(contains_array):
                        domain += [['tag_ids', 'in', contains_array]]
                    domain += [['tag_ids', 'not in', not_contains_array]]

            folder_domain = [['folder_id', 'child_of', rule.domain_folder_id.id]]
            subset = [['id', 'in', self.ids]] + domain + folder_domain
            attachment_ids = self.env['ir.attachment'].search(subset)
            for attachment in attachment_ids:
                attachment.available_rule_ids = [(4, rule.id, False)]

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        creates a new attachment from any email sent to the alias
        and adds the values defined in the share link upload settings
        to the custom values.
        """
        subject = msg_dict.get('subject', '')
        body = msg_dict.get('body', '')
        if custom_values is None:
            custom_values = {}
        defaults = {
            'datas_fname': "Mail: %s.txt" % subject,
            'mimetype': 'text/plain',
            'datas': base64.b64encode(bytes(body, 'utf-8')),
            'active': False,
        }
        defaults.update(custom_values)

        email_from = msg_dict.get('to')
        alias = email_from[:email_from.find('@')]
        share = self.env['documents.share'].search([('alias_name', '=', alias)])
        return super(IrAttachment, self).message_new(msg_dict, defaults).with_context(attachment_values=custom_values,
                                                                                      share=share,
                                                                                      res_mail_dict=msg_dict)

    @api.model
    def _message_post_process_attachments(self, attachments, attachment_ids, message_data):
        """
        If the res model was an attachment and a mail, adds all the custom values of the share link
            settings to the attachments of the mail.

        rv: a list of write commands [(4, attachment_id),]
        """
        rv = super(IrAttachment, self)._message_post_process_attachments(attachments, attachment_ids, message_data)
        dv = self._context.get('attachment_values')
        res_mail_dict = self._context.get('res_mail_dict')
        share = self._context.get('share')
        if message_data['model'] == 'ir.attachment' and dv:
            write_vals = {
                'partner_id': dv['partner_id'],
                'tag_ids': dv['tag_ids'],
                'folder_id': dv['folder_id'],
                'res_model': False,
                'res_id': False,
            }
            attachments = self.env['ir.attachment'].browse([x[1] for x in rv])
            for attachment in attachments:
                attachment.write(write_vals)
                attachment.message_post(body=res_mail_dict.get('body', ''), subject=res_mail_dict.get('subject', ''))
                if share.activity_option:
                    attachment.documents_set_activity(settings_model=share)

        return rv

    @api.multi
    def documents_set_activity(self, settings_model=None):
        """
        Generate an activity based on the fields of settings_model.

        :param settings_model: the model that contains the activity fields.
                    settings_model.activity_type_id (required)
                    settings_model.activity_summary
                    settings_model.activity_note
                    settings_model.activity_date_deadline_range
                    settings_model.activity_date_deadline_range_type
                    settings_model.activity_user_id
        """
        if settings_model and settings_model.activity_type_id:
            activity_vals = {
                'activity_type_id': settings_model.activity_type_id.id,
                'summary': settings_model.activity_summary or '',
                'note': settings_model.activity_note or '',
            }
            if settings_model.activity_date_deadline_range > 0:
                activity_vals['date_deadline'] = fields.Date.context_today(settings_model) + relativedelta(
                    **{settings_model.activity_date_deadline_range_type: settings_model.activity_date_deadline_range})

            if settings_model._fields.get('activity_user_id') and settings_model.activity_user_id:
                user = settings_model.activity_user_id
            elif settings_model._fields.get('user_id') and settings_model.user_id:
                user = settings_model.user_id
            elif settings_model._fields.get('owner_id') and settings_model.owner_id:
                user = settings_model.owner_id
            else:
                user = self.env.user
            if user:
                activity_vals['user_id'] = user.id
            self.activity_schedule(**activity_vals)

    @api.multi
    def toggle_favorited(self):
        self.ensure_one()
        self.write({'favorited_ids': [(3 if self.env.user in self[0].favorited_ids else 4, self.env.user.id)]})

    @api.multi
    def toggle_lock(self):
        """
        sets a lock user, the lock user is the user who locks a file for themselves, preventing data replacement
        and archive (therefore deletion) for any user but himself.

        Members of the group documents.group_document_manager and the superuser can unlock the file regardless.
        """
        self.ensure_one()
        if self.lock_uid:
            if self.env.user == self.lock_uid or self.env.user._is_admin() or self.user_has_groups(
                    'documents.group_document_manager'):
                self.lock_uid = False
        else:
            self.lock_uid = self.env.uid

    def _set_folder_settings(self, vals):
        """Implemented by bridge modules to set their folders and tags to attachments
        @param vals: a create/write dict.
        """
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals_dict in vals_list:
            if vals_dict.get('res_model'):
                vals_dict.update(self._set_folder_settings(vals_dict))

        return super(IrAttachment, self).create(vals_list)

    def write(self, vals):
        if len(self) == 1 and self.type == 'empty' and len(self.activity_ids):
            if not vals.get('type'):
                if vals.get('url'):
                    vals['type'] = 'url'
                if vals.get('datas'):
                    vals['type'] = 'binary'
            if vals.get('type') in ['url', 'binary']:
                self.activity_ids.action_feedback()

        vals = self._set_folder_settings(vals)
        return super(IrAttachment, self).write(vals)


