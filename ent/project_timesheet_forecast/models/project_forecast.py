# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime

from odoo import api, fields, models
from odoo.osv import expression


class Forecast(models.Model):

    _inherit = "project.forecast"

    effective_hours = fields.Float("Effective hours", compute='_compute_effective_hours', compute_sudo=True, store=True)
    percentage_hours = fields.Float("Progress", compute='_compute_percentage_hours', compute_sudo=True, store=True)

    # this field should be in project_forecast directly, since it does not depends on timesheet, and its computation method can be
    # merge with _compute_time. (to avoid calling twice get_work_days_data)
    # TODO JEM: should be moved to project_forecast and mixed with compute_time (see master-forecast-poc2-jem)
    working_days_count = fields.Integer("Number of working days", compute='_compute_working_days_count', store=True)

    @api.depends('employee_id', 'employee_id.resource_calendar_id', 'start_date', 'end_date')
    def _compute_working_days_count(self):
        for forecast in self:
            start_dt = datetime.datetime.combine(forecast.start_date, datetime.time.min)
            stop_dt = datetime.datetime.combine(forecast.end_date, datetime.time.max)
            forecast.working_days_count = forecast.employee_id.get_work_days_data(start_dt, stop_dt)['days']

    @api.depends('resource_hours', 'effective_hours')
    def _compute_percentage_hours(self):
        for forecast in self:
            if forecast.resource_hours:
                forecast.percentage_hours = forecast.effective_hours / forecast.resource_hours
            else:
                forecast.percentage_hours = 0

    @api.depends('task_id', 'user_id', 'start_date', 'end_date', 'project_id.analytic_account_id', 'task_id.timesheet_ids')
    def _compute_effective_hours(self):
        Timesheet = self.env['account.analytic.line']
        for forecast in self:
            if not forecast.task_id and not forecast.project_id:
                forecast.effective_hours = 0
            else:
                domain = [
                    ('user_id', '=', forecast.user_id.id),
                    ('date', '>=', forecast.start_date),
                    ('date', '<=', forecast.end_date)
                ]
                if forecast.task_id:
                    timesheets = Timesheet.search(expression.AND([[('task_id', '=', forecast.task_id.id)], domain]))
                elif forecast.project_id:
                    timesheets = Timesheet.search(expression.AND([[('account_id', '=', forecast.project_id.analytic_account_id.id)], domain]))
                else:
                    timesheets = Timesheet.browse()

                forecast.effective_hours = sum(timesheet.unit_amount for timesheet in timesheets)
