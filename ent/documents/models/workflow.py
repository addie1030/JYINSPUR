# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class WorkflowActionRule(models.Model):
    _name = "documents.workflow.rule"
    _description = "A set of condition and actions which will be available to all attachments matching the conditions"

    domain_folder_id = fields.Many2one('documents.folder', string="Folder", required=True, ondelete='cascade')
    name = fields.Char(required=True, string="Rule name", translate=True)
    note = fields.Char(string="Tooltip")

    # Conditions
    condition_type = fields.Selection([
        ('criteria', "Criteria"),
        ('domain', "Domain"),
    ], default='criteria', string="Condition type")

    # Domain
    domain = fields.Char()

    # Criteria
    criteria_partner_id = fields.Many2one('res.partner', string="Contact")
    criteria_owner_id = fields.Many2one('res.users', string="Owner")
    criteria_tag_ids = fields.One2many('documents.workflow.tag.criteria', 'workflow_rule_id', string="Tags")

    # Actions
    partner_id = fields.Many2one('res.partner', string="Set Contact")
    user_id = fields.Many2one('res.users', string="Set Owner")
    tag_action_ids = fields.One2many('documents.workflow.action', 'workflow_rule_id', string='Set Tags')
    folder_id = fields.Many2one('documents.folder', string="Move to Folder")
    has_business_option = fields.Boolean(compute='_get_business')
    create_model = fields.Selection([], string="Create")

    # Activity
    remove_activities = fields.Boolean(string='Mark all Activities as done')
    activity_option = fields.Boolean(string='Create a new activity')
    activity_type_id = fields.Many2one('mail.activity.type', string="Activity type")
    activity_summary = fields.Char('Summary')
    activity_date_deadline_range = fields.Integer(string='Due Date In')
    activity_date_deadline_range_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], string='Due type', default='days')
    activity_note = fields.Html(string="Activity Note")
    activity_user_id = fields.Many2one('res.users', string='Responsible')

    @api.multi
    def _get_business(self):
        """
        Checks if the workflow rule has available create models to display the option.
        """
        for record in self:
            record.has_business_option = len(self._fields['create_model'].selection)

    def create_record(self, attachments=None):
        """
        implemented by each link module to define specific fields for the new business model (create_values)

        :param attachments: the list of the attachments of the selection
        :return: the action dictionary that will be called after the workflow action is done or True.
        """

        return True

    def apply_actions(self, attachment_ids):
        """
        called by the front-end Document Inspector to apply the actions to the selection of ID's.

        :param context:  attachment_ids[]: the list of attachments to apply the action.
        :return: if the action was to create a new business object, returns an action to open the view of the
                newly created object, else returns True.
        """
        attachments = self.env['ir.attachment'].browse(attachment_ids)

        for attachment in attachments:
            # partner/owner/share_link/folder changes
            attachment_dict = {}
            if self.user_id:
                attachment_dict['owner_id'] = self.user_id.id
            if self.partner_id:
                attachment_dict['partner_id'] = self.partner_id.id
            if self.folder_id:
                attachment_dict['folder_id'] = self.folder_id.id

            attachment.write(attachment_dict)

            if self.remove_activities:
                attachment.activity_ids.action_feedback(
                    feedback="completed by rule: %s. %s" % (self.name, self.note or '')
                )

            if self.activity_option and self.activity_type_id:
                attachment.documents_set_activity(settings_model=self)

            # tag and facet actions
            for tag_action in self.tag_action_ids:
                tag_action.execute_action(attachment)

        if self.create_model:
            return self.create_record(attachments=attachments)

        return True


class WorkflowTagCriteria(models.Model):
    _name = "documents.workflow.tag.criteria"
    _description = "Document Workflow Tag Criteria"

    workflow_rule_id = fields.Many2one('documents.workflow.rule', ondelete='cascade')

    operator = fields.Selection([
        ('contains', "Contains"),
        ('notcontains', "Does not contain"),
    ], default='contains', required=True)

    facet_id = fields.Many2one('documents.facet', string="Category")
    tag_id = fields.Many2one('documents.tag', string="Tag", required=True)


class WorkflowAction(models.Model):
    _name = "documents.workflow.action"
    _description = "Document Workflow Tag Action"

    workflow_rule_id = fields.Many2one('documents.workflow.rule', ondelete='cascade')

    action = fields.Selection([
        ('add', "Add"),
        ('replace', "Replace by"),
        ('remove', "Remove"),
    ], default='add', required=True)

    facet_id = fields.Many2one('documents.facet', string="Category")
    tag_id = fields.Many2one('documents.tag', string="Tag")

    def execute_action(self, attachment):
        if self.action == 'add' and self.tag_id.id:
            return attachment.write({'tag_ids': [(4, self.tag_id.id, False)]})
        elif self.action == 'replace' and self.facet_id.id:
            faceted_tags = self.env['documents.tag'].search([('facet_id', '=', self.facet_id.id)])
            if faceted_tags.ids:
                for tag in faceted_tags:
                    attachment.write({'tag_ids': [(3, tag.id, False)]})
            return attachment.write({'tag_ids': [(4, self.tag_id.id, False)]})
        elif self.action == 'remove':
            if self.tag_id.id:
                return attachment.write({'tag_ids': [(3, self.tag_id.id, False)]})
            elif self.facet_id:
                faceted_tags = self.env['documents.tag'].search([('facet_id', '=', self.facet_id.id)])
                for tag in faceted_tags:
                    return attachment.write({'tag_ids': [(3, tag.id, False)]})
