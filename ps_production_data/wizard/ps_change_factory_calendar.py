# -*- coding: utf-8 -*-

import logging
import time
from odoo import models, api, fields, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PsChangeCalendarWizard(models.TransientModel):
    _name = "ps.change.factory.calendar"
    _description = "Calendar Change Notification"

    @api.multi
    def ps_change_calendar_confirm(self):
        recs = self.env.context.get('recs')
        print(recs)
        for rec in recs:
            rec.write({'ps_is_factory_calendar': False})
        return {'type': 'ir.actions.act_window_close'}