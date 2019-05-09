# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class TimesheetForecastReport(models.Model):

    _name = "project.timesheet.forecast.report.analysis"
    _description = "Timesheet & Forecast Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Date('Date', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    number_hours = fields.Float('Number of hours', readonly=True)
    type = fields.Selection([('forecast', 'Forecast'), ('timesheet', 'Timesheet')], 'Type', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE VIEW %s as (
                (
                    SELECT
                        date::date AS date,
                        F.employee_id AS employee_id,
                        F.task_id AS task_id,
                        F.project_id AS project_id,
                        F.resource_hours / F.working_days_count AS number_hours,
                        'forecast' AS type,
                        F.id AS id
                    FROM generate_series(
                        (SELECT min(start_date) FROM project_forecast WHERE active=true)::date,
                        (SELECT max(end_date) FROM project_forecast WHERE active=true)::date,
                        '1 day'::interval
                    ) date
                        LEFT JOIN project_forecast F ON date >= F.start_date AND date <= end_date
                        LEFT JOIN hr_employee E ON F.employee_id = E.id
                        LEFT JOIN resource_resource R ON E.resource_id = R.id
                    WHERE
                        EXTRACT(ISODOW FROM date) IN (
                            SELECT A.dayofweek::integer+1 FROM resource_calendar_attendance A WHERE A.calendar_id = R.calendar_id
                        )
                        AND F.active=true
                ) UNION (
                    SELECT
                        A.date AS data,
                        E.id AS employee_id,
                        A.task_id AS task_id,
                        A.project_id AS project_id,
                        A.unit_amount AS number_hours,
                        'timesheet' AS type,
                        -A.id AS id
                    FROM account_analytic_line A, hr_employee E
                    WHERE A.project_id IS NOT NULL
                        AND A.employee_id = E.id
                )
            )
        """ % (self._table,))
