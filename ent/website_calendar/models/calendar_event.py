# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid
from odoo import api, fields, models


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    def _default_access_token(self):
        return str(uuid.uuid4())

    access_token = fields.Char('Access Token', default=_default_access_token, readonly=True)
    appointment_type_id = fields.Many2one('calendar.appointment.type', 'Online Appointment', readonly=True)

    @api.model_cr_context
    def _init_column(self, column_name):
        """ Initialize the value of the given column for existing rows.
            Overridden here because we skip generating unique access tokens
            for potentially tons of existing event, should they be needed,
            they will be generated on the fly.
        """
        if column_name != 'access_token':
            super(CalendarEvent, self)._init_column(column_name)

    def _generate_access_token(self):
        for event in self:
            event.access_token = self._default_access_token()
