# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _


class VoipPhonecall(models.Model):
    _name = "voip.phonecall"
    _description = 'VOIP Phonecall'

    _order = "sequence, id"

    name = fields.Char('Call Name', required=True)
    date_deadline = fields.Date('Due Date', default=lambda self: fields.Date.today())
    call_date = fields.Datetime('Call Date')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.uid)
    partner_id = fields.Many2one('res.partner', 'Contact')
    activity_id = fields.Many2one('mail.activity', 'Linked Activity')
    mail_message_id = fields.Many2one('mail.message', 'Linked Chatter Message')
    note = fields.Html('Note')
    duration = fields.Float('Duration', help="Duration in minutes.")
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    in_queue = fields.Boolean('In Call Queue', default=True)
    sequence = fields.Integer('Sequence', index=True,
        help="Gives the sequence order when displaying a list of Phonecalls.")
    start_time = fields.Integer("Start time")
    state = fields.Selection([
        ('pending', 'Not Held'),
        ('cancel', 'Cancelled'),
        ('open', 'To Do'),
        ('done', 'Held'),
    ], string='Status', default='open',
        help='The status is set to To Do, when a call is created.\n'
             'When the call is over, the status is set to Held.\n'
             'If the call is not applicable anymore, the status can be set to Cancelled.')
    type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing')
    ], string='Type', default='outgoing')

    @api.multi
    def init_call(self):
        self.ensure_one()
        self.call_date = fields.Datetime.now()
        self.start_time = int(time.time())

    @api.multi
    def hangup_call(self):
        self.ensure_one()
        stop_time = int(time.time())
        duration_seconds = float(stop_time - self.start_time)
        duration = round(duration_seconds / 60, 2)
        seconds = duration_seconds - int(duration) * 60
        note = False
        if (self.activity_id):
            note = self.activity_id.note
            duration_log = '<br/><p>Call duration: ' + str(int(duration)) + 'min ' + str(int(seconds)) + 'sec</p>'
            if self.activity_id.note:
                self.activity_id.note += duration_log
            else:
                self.activity_id.note = duration_log
            self.activity_id.action_done()
        self.write({
            'state': 'done',
            'duration': duration,
            'note': note,
        })
        return

    @api.multi
    def rejected_call(self):
        self.ensure_one()
        self.state = "pending"

    @api.multi
    def remove_from_queue(self):
        self.ensure_one()
        self.in_queue = False
        if(self.activity_id and self.state in ['pending', 'open']):
            self.state = 'cancel'
            self.activity_id.unlink()

    @api.multi
    def log_note(self, note):
        self.ensure_one()
        self.note = note
        if (self.activity_id):
            self.activity_id.note = note

    @api.one
    def get_info(self):
        info = {'id': self.id,
                'name': self.name,
                'state': self.state,
                'date_deadline': self.date_deadline,
                'call_date': self.call_date,
                'duration': self.duration,
                'phone': self.phone,
                'mobile': self.mobile,
                'note': self.note,
                }
        if self.partner_id:
            ir_model = self.env['ir.model'].search([('model', '=', 'res.partner')])
            info.update(
                partner_id=self.partner_id.id,
                activity_res_id=self.partner_id.id,
                activity_res_model='res.partner',
                activity_model_name=ir_model.display_name,
                partner_name=self.partner_id.name,
                partner_image_small=self.partner_id.image_small,
                partner_email=self.partner_id.email
            )
        if self.activity_id:
            ir_model = self.env['ir.model'].search([('model', '=', self.activity_id.res_model)])
            info.update(
                activity_id=self.activity_id.id,
                activity_res_id=self.activity_id.res_id,
                activity_res_model=self.activity_id.res_model,
                activity_model_name=ir_model.display_name,
                activity_summary=self.activity_id.summary,
                activity_note=self.activity_id.note,
            )
        elif self.mail_message_id:
            ir_model = self.env['ir.model'].search([('model', '=', self.mail_message_id.model)])
            info.update(
                activity_res_id=self.mail_message_id.res_id,
                activity_res_model=self.mail_message_id.model,
                activity_model_name=ir_model.display_name,
            )
        return info

    @api.model
    def get_next_activities_list(self):
        return self.search([
            '|',
            ('activity_id', '!=', False),
            ('mail_message_id', '!=', False),
            ('in_queue', '=', True),
            ('user_id', '=', self.env.user.id),
            ('date_deadline', '<=', fields.Date.today())
        ], order='sequence,date_deadline,id').get_info()

    @api.model
    def get_recent_list(self, search_expr=None, offset=0, limit=None):
        domain = [
            ('user_id', '=', self.env.user.id),
            ('call_date', '!=', False),
            ('in_queue', '=', True),
        ]
        if search_expr:
            domain += [['name', 'ilike', search_expr]]
        return self.search(domain, offset=offset, limit=limit, order='call_date desc').get_info()

    @api.model
    def create_from_contact(self, partner_id):
        partner = self.env['res.partner'].browse(partner_id)
        phonecall = self.create({
            'name': partner.name,
            'phone': partner.sanitized_phone,
            'mobile': partner.sanitized_mobile,
            'partner_id': partner_id,
        })
        phonecall.init_call()
        return phonecall.get_info()[0]

    @api.model
    def create_from_recent(self, phonecall_id):
        recent_phonecall = self.browse(phonecall_id)
        phonecall = self.create({
            'name': recent_phonecall.name,
            'phone': recent_phonecall.phone,
            'mobile': recent_phonecall.mobile,
            'partner_id': recent_phonecall.partner_id.id,
        })
        phonecall.init_call()
        return phonecall.get_info()[0]

    @api.model
    def create_from_number(self, number):
        name = _('Call to ') + number
        phonecall = self.create({
            'name': name,
            'phone': number,
        })
        phonecall.init_call()
        return phonecall.get_info()[0]

    @api.model
    def create_from_incoming_call(self, number, partner_id=False):
        name = _('Call from ') + number
        phonecall = self.create({
            'name': name,
            'phone': number,
            'type': 'incoming',
            'partner_id': partner_id,
        })
        phonecall.init_call()
        return phonecall.get_info()[0]

    @api.model
    def create_from_activity(self, activity):
        record = self.env[activity.res_model].browse(activity.res_id)
        partner_id = False
        if record._name == 'res.partner':
            partner_id = record.id
        elif 'partner_id' in record:
            partner_id = record.partner_id.id
        return self.create({
            'name': activity.res_name,
            'user_id': activity.user_id.id,
            'partner_id': partner_id,
            'activity_id': activity.id,
            'date_deadline': activity.date_deadline,
            'state': 'open',
            'phone': activity.phone,
            'mobile': activity.mobile,
            'note': activity.note,
        })

    @api.model
    def create_from_phone_widget(self, model, res_id, number):
        name = _('Call to ') + number
        partner_id = False
        if model == 'res.partner':
            partner_id = res_id
        else:
            record = self.env[model].browse(res_id)
            fields = self.env[model]._fields.items()
            partner_field_name = [k for k, v in fields if v.type == 'many2one' and v.comodel_name == 'res.partner'][0]
            if len(partner_field_name):
                partner_id = record[partner_field_name].id
        phonecall = self.create({
            'name': name,
            'phone': number,
            'partner_id': partner_id,
        })
        phonecall.init_call()
        return phonecall.get_info()[0]

    @api.model
    def get_from_activity_id(self, activity_id):
        phonecall = self.search([('activity_id', '=', activity_id)])
        phonecall.date_deadline = fields.Date.today()
        phonecall.init_call()
        return phonecall.get_info()[0]
