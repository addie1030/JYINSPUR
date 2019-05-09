# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    category = fields.Selection(selection_add=[('phonecall', 'Phonecall')])


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    voip_phonecall_id = fields.Many2one('voip.phonecall', 'Linked Voip Phonecall')

    @api.model
    def create(self, values):
        activity = super(MailActivity, self).create(values)
        if activity.activity_type_id.category == 'phonecall':
            numbers = activity._compute_phonenumbers()
            if numbers['phone'] or numbers['mobile']:
                activity.phone = numbers['phone']
                activity.mobile = numbers['mobile']
                phonecall = self.env['voip.phonecall'].create_from_activity(activity)
                activity.voip_phonecall_id = phonecall.id
                notification = {'type': 'refresh_voip'}
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                    notification
                )
        return activity

    @api.multi
    def _compute_phonenumbers(self):
        self.ensure_one()
        model = self.env[self.res_model]
        record = model.browse(self.res_id)
        numbers = {
            'phone': False,
            'mobile': False,
        }
        if 'phone' in record:
            numbers['phone'] = record.phone
        if 'mobile' in record:
            numbers['mobile'] = record.mobile
        if not numbers['phone'] and not numbers['mobile']:
            fields = model._fields.items()
            partner_field_name = [k for k, v in fields if v.type == 'many2one' and v.comodel_name == 'res.partner']
            if partner_field_name:
                numbers['phone'] = record[partner_field_name[0]].phone
                numbers['mobile'] = record[partner_field_name[0]].mobile
        return numbers

    @api.multi
    def action_feedback(self, feedback=False):
        mail_message_id = False
        phone_activities = self.filtered(lambda a: a.voip_phonecall_id)
        if phone_activities:
            remaining = self - phone_activities
            for activity in phone_activities:
                user_id = activity.user_id.partner_id.id
                note = activity.note
                voip_phonecall_id = activity.voip_phonecall_id
                mail_message_id = super(MailActivity, activity).action_feedback(feedback)

                vals = {
                    'state': 'done',
                    'mail_message_id': mail_message_id,
                    'note': feedback if feedback else note,
                }
                if not voip_phonecall_id.call_date:
                    vals.update(call_date=fields.Datetime.now())
                voip_phonecall_id.write(vals)
                self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', user_id),
                    {'type': 'refresh_voip'}
                )
        else:
            remaining = self
        if remaining:
            mail_message_id = super(MailActivity, remaining).action_feedback(feedback)

        return mail_message_id
