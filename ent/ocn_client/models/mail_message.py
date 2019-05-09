# -*- coding: utf-8 -*-
import re
from html2text import html2text

from odoo import models, api
from odoo.addons.iap import jsonrpc


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.multi
    def _notify_recipients(self, rdata, record, msg_vals, **kwargs):
        """ We want to send a Cloud notification for every mentions of a partner
        and every direct message. We have to take into account the risk of
        duplicated notifications in case of a mention in a channel of `chat` type.
        """
        super(MailMessage, self)._notify_recipients(rdata, record, msg_vals, **kwargs)

        notif_pids = [r['id'] for r in rdata['partners']]
        chat_cids = [r['id'] for r in rdata['channels'] if r['type'] == 'chat']

        if not notif_pids and not chat_cids:
            return

        self_sudo = self.sudo()
        msg_type = msg_vals.get('message_type') or self_sudo.message_type

        if msg_type == 'comment':
            # Create Cloud messages for needactions, but ignore the needaction if it is a result
            # of a mention in a chat. In this case the previously created Cloud message is enough.

            if chat_cids:
                channel_partner_ids = self.env['mail.channel'].sudo().search([
                    ('id', 'in', chat_cids),
                ]).mapped("channel_partner_ids").ids
            else:
                channel_partner_ids = []
            pids = (set(notif_pids) | set(channel_partner_ids)) - set(self_sudo.author_id.ids)
            if pids:
                receiver_ids = self.env['res.partner'].sudo().search([('id', 'in', list(pids))])
                identities = receiver_ids.filtered(lambda receiver: receiver.ocn_token).mapped('ocn_token')
                if identities:
                    endpoint = self.env['res.config.settings']._get_endpoint()
                    params = {
                        'ocn_tokens': identities,
                        'data': self._ocn_prepare_payload(self)
                    }
                    jsonrpc(endpoint + '/iap/ocn/send', params=params)

    @api.model
    def _ocn_prepare_payload(self, message):
        """Returns dictionary containing message information for mobile device.
        This info will be delivered to mobile device via Google Firebase Cloud
        Messaging (FCM). And it is having limit of 4000 bytes (4kb)
        """
        payload = {
            "author_name": message.author_id.name,
            "model": message.model,
            "res_id": message.res_id,
            "db_id": self.env['res.config.settings']._get_ocn_uuid()
        }
        if message.model == 'mail.channel':
            channel = message.channel_ids.filtered(lambda r: r.id == message.res_id)
            if channel.channel_type == 'chat':
                payload['subject'] = message.author_id.name
                payload['type'] = 'chat'
            else:
                payload['subject'] = "#%s" % (message.record_name)
        else:
            payload['subject'] = message.record_name or message.subject
        payload_length = len(str(payload).encode("utf-8"))
        if payload_length < 4000:
            body = re.sub(r'<a(.*?)>', r'<a>', message.body)  # To-Do : Replace this fix
            payload['body'] = html2text(body)[:4000 - payload_length]
        return payload
