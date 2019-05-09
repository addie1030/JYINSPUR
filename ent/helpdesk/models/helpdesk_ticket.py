# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import AccessError
from odoo.tools import pycompat

TICKET_PRIORITY = [
    ('0', 'All'),
    ('1', 'Low priority'),
    ('2', 'High priority'),
    ('3', 'Urgent'),
]


class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tags'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer('Color')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class HelpdeskTicketType(models.Model):
    _name = 'helpdesk.ticket.type'
    _description = 'Helpdesk Ticket Type'
    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists !"),
    ]


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _order = 'priority desc, id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'utm.mixin', 'rating.mixin', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        res = super(HelpdeskTicket, self).default_get(fields)
        if res.get('team_id'):
            update_vals = self._onchange_team_get_values(self.env['helpdesk.team'].browse(res['team_id']))
            if (not fields or 'user_id' in fields) and 'user_id' not in res:
                res['user_id'] = update_vals['user_id']
            if (not fields or 'stage_id' in fields) and 'stage_id' not in res:
                res['stage_id'] = update_vals['stage_id']
        return res

    def _default_team_id(self):
        team_id = self._context.get('default_team_id')
        if not team_id:
            team_id = self.env['helpdesk.team'].search([('member_ids', 'in', self.env.uid)], limit=1).id
        if not team_id:
            team_id = self.env['helpdesk.team'].search([], limit=1).id
        return team_id

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('team_ids', '=', team_id) if team_id: add team columns
        search_domain = [('id', 'in', stages.ids)]
        if self.env.context.get('default_team_id'):
            search_domain = ['|', ('team_ids', 'in', self.env.context['default_team_id'])] + search_domain

        return stages.search(search_domain, order=order)

    name = fields.Char(string='Subject', required=True, index=True)
    team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team', default=_default_team_id, index=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket Type")
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags')
    company_id = fields.Many2one(related='team_id.company_id', string='Company', store=True, readonly=True)
    color = fields.Integer(string='Color Index')
    kanban_state = fields.Selection([
        ('normal', 'Normal'),
        ('blocked', 'Blocked'),
        ('done', 'Ready for next stage')], string='Kanban State',
        default='normal', required=True, track_visibility='onchange',
        help="A ticket's kanban state indicates special situations affecting it:\n"
             "* Normal is the default situation\n"
             "* Blocked indicates something is preventing the progress of this issue\n"
             "* Ready for next stage indicates the issue is ready to be pulled to the next stage")
    user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange', domain=lambda self: [('groups_id', 'in', self.env.ref('helpdesk.group_helpdesk_user').id)])
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_tickets = fields.Integer('Number of tickets from the same partner', compute='_compute_partner_tickets')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string="Number of Attachments")

    # Used to submit tickets from a contact form
    partner_name = fields.Char(string='Customer Name')
    partner_email = fields.Char(string='Customer Email')

    # Used in message_get_default_recipients, so if no partner is created, email is sent anyway
    email = fields.Char(related='partner_email', string='Email on Customer', readonly=False)

    priority = fields.Selection(TICKET_PRIORITY, string='Priority', default='0')
    stage_id = fields.Many2one('helpdesk.stage', string='Stage', ondelete='restrict', track_visibility='onchange',
                               group_expand='_read_group_stage_ids', copy=False,
                               index=True, domain="[('team_ids', '=', team_id)]")

    # next 4 fields are computed in write (or create)
    assign_date = fields.Datetime(string='First assignation date')
    assign_hours = fields.Integer(string='Time to first assignation (hours)', compute='_compute_assign_hours', store=True)
    close_date = fields.Datetime(string='Close date')
    close_hours = fields.Integer(string='Open Time (hours)', compute='_compute_close_hours', store=True)

    sla_id = fields.Many2one('helpdesk.sla', string='SLA Policy', compute='_compute_sla', store=True)
    sla_name = fields.Char(string='SLA Policy name', compute='_compute_sla', store=True)  # care if related -> crash on creation with a team.
    deadline = fields.Datetime(string='Deadline', compute='_compute_sla', store=True)
    sla_active = fields.Boolean(string='SLA active', compute='_compute_sla_fail', store=True)
    sla_fail = fields.Boolean(string='Failed SLA Policy', compute='_compute_sla_fail', store=True)

    # customer portal: include comment and incoming emails in communication history
    website_message_ids = fields.One2many(domain=lambda self: [('model', '=', self._name), ('message_type', 'in', ['email', 'comment'])])

    def _compute_access_url(self):
        super(HelpdeskTicket, self)._compute_access_url()
        for ticket in self:
            ticket.access_url = '/my/ticket/%s' % ticket.id

    def _onchange_team_get_values(self, team):
        return {
            'user_id': team.get_new_user().id,
            'stage_id': self.env['helpdesk.stage'].search([('team_ids', 'in', team.id)], order='sequence', limit=1).id
        }

    @api.multi
    def _compute_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'helpdesk.ticket'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = { res['res_id']: res['res_id_count'] for res in read_group_res }
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    @api.multi
    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        return action

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            update_vals = self._onchange_team_get_values(self.team_id)
            if not self.user_id:
                self.user_id = update_vals['user_id']
            if not self.stage_id or self.stage_id not in self.team_id.stage_ids:
                self.stage_id = update_vals['stage_id']

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_email = self.partner_id.email

    @api.depends('partner_id')
    def _compute_partner_tickets(self):
        for ticket in self:
            ticket_data = self.env['helpdesk.ticket'].read_group([
                ('partner_id', '=', ticket.partner_id.id),
                ('stage_id.is_close', '=', False)
            ], ['partner_id'], ['partner_id'])
            if ticket_data:
                ticket.partner_tickets = ticket_data[0]['partner_id_count']

    @api.depends('assign_date')
    def _compute_assign_hours(self):
        for ticket in self:
            if not ticket.create_date:
                continue;
            time_difference = datetime.datetime.now() - fields.Datetime.from_string(ticket.create_date)
            ticket.assign_hours = (time_difference.seconds) / 3600 + time_difference.days * 24

    @api.depends('close_date')
    def _compute_close_hours(self):
        for ticket in self:
            if not ticket.create_date:
                continue;
            time_difference = datetime.datetime.now() - fields.Datetime.from_string(ticket.create_date)
            ticket.close_hours = (time_difference.seconds) / 3600 + time_difference.days * 24

    @api.depends('team_id', 'priority', 'ticket_type_id', 'create_date')
    def _compute_sla(self):
        if not self.user_has_groups("helpdesk.group_use_sla"):
            return
        for ticket in self:
            dom = [('team_id', '=', ticket.team_id.id), ('priority', '<=', ticket.priority), '|', ('ticket_type_id', '=', ticket.ticket_type_id.id), ('ticket_type_id', '=', False)]
            sla = ticket.env['helpdesk.sla'].search(dom, order="time_days, time_hours", limit=1)
            working_calendar = ticket.team_id.resource_calendar_id
            if sla and ticket.sla_id != sla and ticket.active and ticket.create_date:
                ticket.sla_id = sla.id
                ticket.sla_name = sla.name
                ticket_create_date = fields.Datetime.from_string(ticket.create_date)
                if sla.time_days > 0:
                    deadline = working_calendar.plan_days(
                        sla.time_days+1,
                        ticket_create_date,
                        compute_leaves=True)
                    # We should also depend on ticket creation time, otherwise for 1 day SLA for example all tickets
                    # created on monday will have the deadline as tuesday 8:00
                    deadline = deadline.replace(hour=ticket_create_date.hour, minute=ticket_create_date.minute, second=ticket_create_date.second, microsecond=ticket_create_date.microsecond)
                else:
                    deadline = ticket_create_date
                # We should execute the function plan_hours in any case because
                # if i create a ticket for 1 day sla configuration and tomorrow at the same time i don't work,
                # deadline falls on the time that i don't work which is ticket creation time and is not correct
                ticket.deadline = working_calendar.plan_hours(
                    sla.time_hours,
                    deadline,
                    compute_leaves=True)

    @api.depends('deadline', 'stage_id.sequence', 'sla_id.stage_id.sequence')
    def _compute_sla_fail(self):
        if not self.user_has_groups("helpdesk.group_use_sla"):
            return
        for ticket in self:
            ticket.sla_active = True
            if not ticket.deadline:
                ticket.sla_active = False
                ticket.sla_fail = False
            elif ticket.sla_id.stage_id.sequence <= ticket.stage_id.sequence:
                ticket.sla_active = False
                prev_stage_ids = self.env['helpdesk.stage'].search([('sequence', '<', ticket.sla_id.stage_id.sequence)])
                next_stage_ids = self.env['helpdesk.stage'].search([('sequence', '>=', ticket.sla_id.stage_id.sequence)])
                stage_id_tracking_value = self.env['mail.tracking.value'].sudo().search([('field', '=', 'stage_id'),
                                                                                  ('old_value_integer', 'in', prev_stage_ids.ids),
                                                                                  ('new_value_integer', 'in', next_stage_ids.ids),
                                                                                  ('mail_message_id.model', '=', 'helpdesk.ticket'),
                                                                                  ('mail_message_id.res_id', '=', ticket.id)], order='create_date ASC', limit=1)

                if stage_id_tracking_value:
                    if stage_id_tracking_value.create_date > ticket.deadline:
                        ticket.sla_fail = True
                # If there are no tracking messages, it means we *just* (now!) changed the state
                elif fields.Datetime.now() > ticket.deadline:
                    ticket.sla_fail = True

    @api.model
    def create(self, vals):
        if vals.get('team_id'):
            vals.update(item for item in self._onchange_team_get_values(self.env['helpdesk.team'].browse(vals['team_id'])).items() if item[0] not in vals)

        # context: no_log, because subtype already handle this
        ticket = super(HelpdeskTicket, self.with_context(mail_create_nolog=True)).create(vals)
        if ticket.partner_id:
            ticket.message_subscribe(partner_ids=ticket.partner_id.ids)
            ticket._onchange_partner_id()
        if ticket.user_id:
            ticket.assign_date = ticket.create_date
            ticket.assign_hours = 0

        return ticket

    @api.multi
    def write(self, vals):
        # we set the assignation date (assign_date) to now for tickets that are being assigned for the first time
        # same thing for the closing date
        assigned_tickets = closed_tickets = self.browse()
        if vals.get('user_id'):
            assigned_tickets = self.filtered(lambda ticket: not ticket.assign_date)
        if vals.get('stage_id') and self.env['helpdesk.stage'].browse(vals.get('stage_id')).is_close:
            closed_tickets = self.filtered(lambda ticket: not ticket.close_date)

        now = datetime.datetime.now()
        res = super(HelpdeskTicket, self - assigned_tickets - closed_tickets).write(vals)
        res &= super(HelpdeskTicket, assigned_tickets - closed_tickets).write(dict(vals, **{
            'assign_date': now,
        }))
        res &= super(HelpdeskTicket, closed_tickets - assigned_tickets).write(dict(vals, **{
            'close_date': now,
        }))
        res &= super(HelpdeskTicket, assigned_tickets & closed_tickets).write(dict(vals, **{
            'assign_date': now,
            'close_date': now,
        }))

        if vals.get('partner_id'):
            self.message_subscribe([vals['partner_id']])

        return res

    @api.multi
    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, "%s (#%d)" % (ticket.name, ticket.id)))
        return result

    # Method to called by CRON to update SLA & statistics
    @api.model
    def recompute_all(self):
        tickets = self.search([('stage_id.is_close', '=', False)])
        tickets._compute_sla()
        tickets._compute_close_hours()
        return True

    @api.multi
    def assign_ticket_to_self(self):
        self.ensure_one()
        self.user_id = self.env.user

    @api.multi
    def open_customer_tickets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form,pivot,graph',
            'context': {'search_default_is_open': True, 'search_default_partner_id': self.partner_id.id}
        }

    #DVE FIXME: if partner gets created when sending the message it should be set as partner_id of the ticket.
    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(HelpdeskTicket, self).message_get_suggested_recipients()
        try:
            for ticket in self:
                if ticket.partner_id and ticket.partner_id.email:
                    ticket._message_add_suggested_recipient(recipients, partner=ticket.partner_id, reason=_('Customer'))
                elif ticket.partner_email:
                    ticket._message_add_suggested_recipient(recipients, email=ticket.partner_email, reason=_('Customer Email'))
        except AccessError:  # no read access rights -> just ignore suggested recipients because this implies modifying followers
            pass
        return recipients

    @api.multi
    def _ticket_email_split(self, msg):
        email_list = tools.email_split((msg.get('to') or '') + ',' + (msg.get('cc') or ''))
        # check left-part is not already an alias
        return [
            x for x in email_list
            if x.split('@')[0] not in self.mapped('team_id.alias_name')
        ]

    @api.model
    def message_new(self, msg, custom_values=None):
        values = dict(custom_values or {}, partner_email=msg.get('from'), partner_id=msg.get('author_id'))
        ticket = super(HelpdeskTicket, self).message_new(msg, custom_values=values)

        partner_ids = [x for x in ticket._find_partner_from_emails(self._ticket_email_split(msg)) if x]
        customer_ids = ticket._find_partner_from_emails(tools.email_split(values['partner_email']))
        partner_ids += customer_ids

        if customer_ids and not values.get('partner_id'):
            ticket.partner_id = customer_ids[0]
        if partner_ids:
            ticket.message_subscribe(partner_ids)
        return ticket

    @api.multi
    def message_update(self, msg, update_vals=None):
        partner_ids = [x for x in self._find_partner_from_emails(self._ticket_email_split(msg)) if x]
        if partner_ids:
            self.message_subscribe(partner_ids)
        return super(HelpdeskTicket, self).message_update(msg, update_vals=update_vals)

    def _message_post_after_hook(self, message, *args, **kwargs):
        if self.partner_email and self.partner_id and not self.partner_id.email:
            self.partner_id.email = self.partner_email

        if self.partner_email and not self.partner_id:
            # we consider that posting a message with a specified recipient (not a follower, a specific one)
            # on a document without customer means that it was created through the chatter using
            # suggested recipients. This heuristic allows to avoid ugly hacks in JS.
            new_partner = message.partner_ids.filtered(lambda partner: partner.email == self.partner_email)
            if new_partner:
                self.search([
                    ('partner_id', '=', False),
                    ('partner_email', '=', new_partner.email),
                    ('stage_id.fold', '=', False)]).write({'partner_id': new_partner.id})
        return super(HelpdeskTicket, self)._message_post_after_hook(message, *args, **kwargs)

    @api.multi
    def _track_template(self, tracking):
        res = super(HelpdeskTicket, self)._track_template(tracking)
        ticket = self[0]
        changes, tracking_value_ids = tracking[ticket.id]
        if 'stage_id' in changes and ticket.stage_id.template_id:
            res['stage_id'] = (ticket.stage_id.template_id, {
                'auto_delete_message': True,
                'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_note'),
                'notif_layout': 'mail.mail_notification_light'
            }
        )
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'stage_id' in init_values and self.stage_id.sequence < 1:
            return 'helpdesk.mt_ticket_new'
        elif 'stage_id' in init_values and self.stage_id.sequence >= 1:
            return 'helpdesk.mt_ticket_stage'
        return super(HelpdeskTicket, self)._track_subtype(init_values)

    @api.multi
    def _notify_get_groups(self, message, groups):
        """ Handle helpdesk users and managers recipients that can assign
        tickets directly from notification emails. Also give access button
        to portal and portal customers. If they are notified they should
        probably have access to the document. """
        groups = super(HelpdeskTicket, self)._notify_get_groups(message, groups)

        self.ensure_one()
        for group_name, group_method, group_data in groups:
            if group_name in ('customer'):
                continue
            group_data['has_button_access'] = True

        if self.user_id:
            return groups

        take_action = self._notify_get_action_link('assign')
        helpdesk_actions = [{'url': take_action, 'title': _('Assign to me')}]
        helpdesk_user_group_id = self.env.ref('helpdesk.group_helpdesk_user').id
        return [(
            'group_helpdesk_user', lambda pdata: pdata['type'] == 'user' and helpdesk_user_group_id in pdata['groups'], {
                'actions': helpdesk_actions,
            })] + groups

    @api.multi
    def _notify_get_reply_to(self, default=None, records=None, company=None, doc_names=None):
        """ Override to set alias of tickets to their team if any. """
        aliases = self.mapped('team_id')._notify_get_reply_to(default=default, records=None, company=company, doc_names=None)
        res = {ticket.id: aliases.get(ticket.team_id.id) for ticket in self}
        leftover = self.filtered(lambda rec: not rec.team_id)
        if leftover:
            res.update(super(HelpdeskTicket, leftover)._notify_get_reply_to(default=default, records=None, company=company, doc_names=doc_names))
        return res

    # ------------------------------------------------------------
    # Rating Mixin
    # ------------------------------------------------------------

    @api.multi
    def rating_apply(self, rate, token=None, feedback=None, subtype=None):
        return super(HelpdeskTicket, self).rating_apply(rate, token=token, feedback=feedback, subtype="helpdesk.mt_ticket_rated")

    def rating_get_parent(self):
        return 'team_id'
