# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MailMailStatistics(models.Model):
    _inherit = 'mail.mail.statistics'

    marketing_trace_id = fields.Many2one(
        'marketing.trace', string='Marketing Trace',
        index=True, ondelete='cascade')

    def set_clicked(self, mail_mail_ids=None, mail_message_ids=None):
        statistics = super(MailMailStatistics, self).set_clicked(mail_mail_ids=mail_mail_ids, mail_message_ids=mail_message_ids)
        if statistics.marketing_trace_id:
            statistics.marketing_trace_id.process_event('mail_click')
        return statistics

    def set_opened(self, mail_mail_ids=None, mail_message_ids=None):
        statistics = super(MailMailStatistics, self).set_opened(mail_mail_ids=mail_mail_ids, mail_message_ids=mail_message_ids)
        if statistics.marketing_trace_id:
            statistics.marketing_trace_id.process_event('mail_open')
        return statistics

    def set_replied(self, mail_mail_ids=None, mail_message_ids=None):
        statistics = super(MailMailStatistics, self).set_replied(mail_mail_ids=mail_mail_ids, mail_message_ids=mail_message_ids)
        if statistics.marketing_trace_id:
            statistics.marketing_trace_id.process_event('mail_reply')
        return statistics

    def set_bounced(self, mail_mail_ids=None, mail_message_ids=None):
        statistics = super(MailMailStatistics, self).set_bounced(mail_mail_ids=mail_mail_ids, mail_message_ids=mail_message_ids)
        if statistics.marketing_trace_id:
            statistics.marketing_trace_id.process_event('mail_bounce')
        return statistics
