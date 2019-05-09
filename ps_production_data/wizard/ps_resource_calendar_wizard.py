# -*- coding: utf-8 -*-

import logging
import time
from odoo import models, api, fields, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PsResourceCalendarWizard(models.TransientModel):
    _name = "ps.resource.calendar.wizard"
    _description = "ps.resource.calendar.wizard"

    calendar_id = fields.Many2one('resource.calendar', string='Calendar', ondelete="cascade")  # 工作日历ID
    is_generate_calendar = fields.Boolean(string='Generate Calendar') #生成日历
    is_extend_calendar = fields.Boolean(string='Extend Calendar') #延长日历
    start_date = fields.Date(string='Start Date', default=fields.Date.today) #开始日期
    end_date = fields.Date(string='End Date') #结束日期
    extend_date = fields.Date(string='Extend Date') #延长日期

    @api.model
    def default_get(self, fields):
        res = super(PsResourceCalendarWizard, self).default_get(fields)
        active_ids = self.env.context.get('calendar_id')
        date_now = date.today()
        calendar = self.env['resource.calendar'].browse(active_ids)
        if len(calendar.calendar_line_ids) > 0:
            end_date = max([r.gregorian_date for r in calendar.calendar_line_ids])
        else:
            end_date = date_now + relativedelta(years=2)
        res.update({
            'calendar_id': active_ids,
            'end_date': end_date,
            'extend_date': end_date + relativedelta(days=1),
        })
        return res

    def get_week_day(self, date):
        week_day_dict = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday',
        }
        day = date.weekday()
        weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        rec = self.env['resource.calendar.attendance'].search([('calendar_id', '=', self.calendar_id.id),
                                                               ('dayofweek', '=', str(day))])
        dh = sum(r.hour_to - r.hour_from for r in rec) if rec else 0 # work hours per day
        if week_day_dict[day] in weekday:
            return True, dh
        else:
            return False, dh

    def check_whether_leave(self, date):
        leaves = self.env['resource.calendar.leaves'].search([('calendar_id', '=', self.calendar_id.id)])
        for leave in leaves:
            leave_begin = leave.date_from.date()
            leave_end = leave.date_to.date()
            if leave_begin <= date and leave_end >= date:
                return True

    @api.multi
    def ps_resource_calendar_confirm(self):
        self.ensure_one()
        calendar = self.env['resource.calendar'].browse(self.calendar_id.id)
        calendar_lines = []
        index = 0 # working day sequence
        th = 0 # cumulative work hours
        ds = self.start_date
        de = self.end_date + relativedelta(days=1)
        if self.is_generate_calendar:
            if self.start_date > self.end_date:
                raise UserError(_('Start date should not be later than end date.'))
            while ds <= self.end_date:
                if not self.check_whether_leave(ds):
                    gd, dh = self.get_week_day(ds)
                    da = 'work' if gd else 'rest'
                    index = index + 1 if da == 'work' else index
                    th += dh
                    calendar_lines.append({
                        'calendar_id': self.calendar_id.id,
                        'gregorian_date': ds,
                        'date_attribute': da,
                        'gregorian_week': str(ds.weekday()),
                        'day_hours': dh,
                        'working_day': str(index),
                        'total_hours': th,
                    })
                elif self.check_whether_leave(ds):
                    index = index
                    th += 0
                    calendar_lines.append({
                        'calendar_id': self.calendar_id.id,
                        'gregorian_date': ds,
                        'date_attribute': 'rest',
                        'gregorian_week': str(ds.weekday()),
                        'day_hours': 0,
                        'working_day': str(index),
                        'total_hours': th,
                    })
                ds = ds + relativedelta(days=1)
            if calendar.calendar_line_ids:
                calendar.calendar_line_ids.unlink()
            calendar.calendar_line_ids = calendar_lines
        elif self.is_extend_calendar:
            if not len(calendar.calendar_line_ids) > 0:
                raise UserError(_('Please generate calender before extend it.'))
            elif self.end_date > self.extend_date:
                raise UserError(_('Extend date should be later than end date.'))
            index_ex = max([int(r.working_day) for r in calendar.calendar_line_ids])
            th_ex = max([r.total_hours for r in calendar.calendar_line_ids])
            while de <= self.extend_date:
                if not self.check_whether_leave(de):
                    gd, dh = self.get_week_day(de)
                    da = 'work' if gd else 'rest'
                    index_ex = index_ex + 1 if da == 'work' else index_ex
                    th_ex += dh
                    calendar_lines.append({
                        'calendar_id': self.calendar_id.id,
                        'gregorian_date': de,
                        'date_attribute': da,
                        'gregorian_week': str(de.weekday()),
                        'day_hours': dh,
                        'working_day': str(index_ex),
                        'total_hours': th_ex,
                    })
                elif self.check_whether_leave(de):
                    index_ex = index_ex
                    th_ex += 0
                    calendar_lines.append({
                        'calendar_id': self.calendar_id.id,
                        'gregorian_date': de,
                        'date_attribute': 'rest',
                        'gregorian_week': str(de.weekday()),
                        'day_hours': 0,
                        'working_day': str(index_ex),
                        'total_hours': th_ex,
                    })
                de = de + relativedelta(days=1)
            calendar.calendar_line_ids = calendar_lines
        else:
            raise UserError(_('Both checkboxes are not selected, please click "Cancel" if you want to leave.'))
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('is_generate_calendar')
    def ensure_unique_type_selected(self):
        if self.is_generate_calendar:
            self.is_extend_calendar = False

    @api.onchange('is_extend_calendar')
    def ensure_unique_type_selected_1(self):
        if self.is_extend_calendar:
            self.is_generate_calendar = False





