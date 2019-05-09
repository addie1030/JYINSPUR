# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tools.mail import html2plaintext
import time
from datetime import datetime, timedelta
from odoo import api, models, fields
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.misc import format_date


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_next_date(self, followup_line, level):
        delay = followup_line.delay
        previous_followup = self.env['account_followup.followup.line'].search([('delay', '<', delay),
                                                                                ('followup_id', '=', followup_line.followup_id.id)],
                                                                                order="delay desc", limit=1)
        if previous_followup:
            delay -= previous_followup.delay
        return fields.datetime.now() + timedelta(days=delay)

    def _get_line_info(self, followup_line):
        return {
                'id': followup_line.id,
                'name': followup_line.name,
                'print_letter': followup_line.print_letter,
                'send_email': followup_line.send_email,
                'manual_action': followup_line.manual_action,
                'manual_action_note': followup_line.manual_action_note
            }

    @api.model
    def get_followup_informations(self, partner_id, options):
        partner = self.env['res.partner'].browse(partner_id)
        level = partner.get_followup_level()
        options['partner_id'] = partner_id
        if level:
            options['followup_level'] = level
        infos = super(AccountFollowupReport, self).get_followup_informations(partner_id, options)
        if level:
            followup_line = self.env['account_followup.followup.line'].browse(level[0])
            infos['followup_level'] = self._get_line_info(followup_line)
            # Compute the next_action date
            if not options.get('keep_summary'):
                next_date = self._get_next_date(followup_line, level)
                lang_code = partner.lang or self.env.user.lang or 'en_US'
                infos['next_action']['date_auto'] = format_date(self.env, next_date, lang_code=lang_code)
        return infos

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        if additional_context is None:
            additional_context = {}
        additional_context['followup_line'] = self.get_followup_line(options)
        return super(AccountFollowupReport, self).get_html(options, line_id=line_id, additional_context=additional_context)

    @api.model
    def get_followup_line(self, options):
        if options.get('followup_level'):
            followup_line = self.env['account_followup.followup.line'].browse(options['followup_level'][0])
            return followup_line
        return False

    def _get_default_summary(self, options):
        followup_line = self.get_followup_line(options)
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        lang = partner.lang or self.env.user.lang or 'en_US'
        if followup_line:
            partner = self.env['res.partner'].browse(options['partner_id'])
            lang = partner.lang or self.env.user.lang or 'en_US'
            summary = followup_line.with_context(lang=lang).description
            try:
                summary = summary % {'partner_name': partner.name,
                                     'date': time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                     'user_signature': html2plaintext(self.env.user.signature or ''),
                                     'company_name': self.env.user.company_id.name}
            except ValueError as exception:
                message = "An error has occurred while formatting your followup letter/email. (Lang: %s, Followup Level: #%s) \n\nFull error description: %s" \
                          % (partner.lang, followup_line.id, exception)
                raise ValueError(message)
            return summary
        return super(AccountFollowupReport, self)._get_default_summary(options)

    @api.model
    def do_manual_action(self, options):
        msg = _('Manual action done')
        partner = self.env['res.partner'].browse(options.get('partner_id'))
        if options.get('followup_level'):
            followup_line = self.env['account_followup.followup.line'].browse(options.get('followup_level'))
            if followup_line:
                msg += '<br>' + followup_line.manual_action_note
        partner.message_post(body=msg)

    def _execute_followup_partner(self, partner):
        if partner.followup_status == 'in_need_of_action':
            level = partner.get_followup_level()
            followup_line = self.env['account_followup.followup.line'].browse(level[0])
            if followup_line.send_email:
                partner.send_followup_email()
            if followup_line.manual_action:
                #log a next activity for today
                activity_data = {
                    'res_id': partner.id,
                    'res_model_id': self.env['ir.model']._get(partner._name).id,
                    'activity_type_id': followup_line.manual_action_type_id.id or self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': followup_line.manual_action_note,
                    'user_id': followup_line.manual_action_responsible_id.id or self.env.user.id,
                }
                self.env['mail.activity'].create(activity_data)
            next_date = self._get_next_date(followup_line, level)
            partner.update_next_action(options={'next_action_date': datetime.strftime(next_date, DEFAULT_SERVER_DATE_FORMAT), 'next_action_type': 'auto'})
            if followup_line.print_letter:
                return partner
        return None
