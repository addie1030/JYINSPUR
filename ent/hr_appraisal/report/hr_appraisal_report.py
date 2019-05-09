# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

from odoo.addons.hr_appraisal.models.hr_appraisal import HrAppraisal


class HrAppraisalReport(models.Model):
    _name = "hr.appraisal.report"
    _description = "Appraisal Statistics"
    _auto = False

    create_date = fields.Date(string='Create Date', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    deadline = fields.Date(string="Deadline", readonly=True)
    final_interview = fields.Date(string="Interview", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    state = fields.Selection(HrAppraisal.APPRAISAL_STATES, 'Status', readonly=True)

    _order = 'create_date desc'

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hr_appraisal_report')
        self.env.cr.execute("""
            create or replace view hr_appraisal_report as (
                 select
                     min(a.id) as id,
                     date(a.create_date) as create_date,
                     a.employee_id,
                     e.department_id as department_id,
                     a.date_close as deadline,
                     a.date_final_interview as final_interview,
                     a.state
                     from hr_appraisal a
                        left join hr_employee e on (e.id=a.employee_id)
                 GROUP BY
                     a.id,
                     a.create_date,
                     a.state,
                     a.employee_id,
                     a.date_close,
                     a.date_final_interview,
                     e.department_id
                )
            """)
