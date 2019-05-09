# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    helpdesk_target_closed = fields.Float(string='Target Tickets to Close')
    helpdesk_target_rating = fields.Float(string='Target Customer Rating')
    helpdesk_target_success = fields.Float(string='Target Success Rate')

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights.
            Access rights are disabled by default, but allowed
            on some specific fields defined in self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(ResUsers, self).__init__(pool, cr)
        helpdesk_fields = [
            'helpdesk_target_closed',
            'helpdesk_target_rating',
            'helpdesk_target_success',
        ]
        # duplicate list to avoid modifying the original reference
        type(self).SELF_WRITEABLE_FIELDS = list(self.SELF_WRITEABLE_FIELDS)
        type(self).SELF_WRITEABLE_FIELDS.extend(helpdesk_fields)
        # duplicate list to avoid modifying the original reference
        type(self).SELF_READABLE_FIELDS = list(self.SELF_READABLE_FIELDS)
        type(self).SELF_READABLE_FIELDS.extend(helpdesk_fields)
        return init_res
