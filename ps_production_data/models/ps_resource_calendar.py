# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from datetime import datetime, time, timedelta
from dateutil.rrule import rrule, DAILY
from functools import partial
from itertools import chain
from pytz import timezone, utc

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools.float_utils import float_round

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    ps_is_factory_calendar = fields.Boolean(string='The Factory Calendar',
                                            help='Selected if this calendar is the calendar for the factory') #工厂日历(如被选中，则此日历为工厂日历)
    calendar_line_ids = fields.One2many('ps.resource.calendar.line', 'calendar_id', string='Calendar Line') #日历明细

    @api.multi
    def generate_calendar(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generate Calendar'),
            'view_mode': 'form',
            'view_type': 'form',
            'context': {'calendar_id': self.id},
            'res_model': 'ps.resource.calendar.wizard',
            'target': 'new',
        }

    @api.multi
    def write(self, vals):
        res = super(ResourceCalendar, self).write(vals)
        for line in self.calendar_line_ids:
            rec = self.env['ps.resource.calendar.line'].search([('id', '<=', line.id), ('calendar_id', '=', self.id)])
            total_hours = sum(l.day_hours for l in rec)
            line.total_hours = total_hours
        return res

    @api.constrains('ps_is_factory_calendar')
    def _check_unique_factory_calendar(self):
        for r in self:
            if r.ps_is_factory_calendar:
                recs = self.search([('id', '!=', r.id)])
                if recs:
                    for rec in recs:
                        rec.write({'ps_is_factory_calendar': False})


class PsResourceCalendarLine(models.Model):
    _name = "ps.resource.calendar.line"
    _description = 'PS Resource Calendar Lines'

    calendar_id = fields.Many2one('resource.calendar', string='Calendar', ondelete="cascade") #工作日历ID
    gregorian_date = fields.Date(string='Gregorian Date') #公历日期
    factory_workday = fields.Integer(string='Factory Workday') #工厂工作日
    date_attribute = fields.Selection([('work', 'Week Days'), ('rest', 'Closing Days')], string='Date Attribute') #日期属性(工作日、休息日)
    gregorian_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='0') #公历星期
    day_hours = fields.Float(string='Working Hours Per Day', digits=dp.get_precision('Work Hours')) #日总工时
    working_day = fields.Char(string='Working Day', help='Start from 0, and plus 1 if the day was week day') #工作日
    total_hours = fields.Float(string='Cumulative Working Hours', digits=dp.get_precision('Work Hours')) #总工时