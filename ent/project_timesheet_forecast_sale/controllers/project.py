# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval
import babel
from dateutil.relativedelta import relativedelta

from odoo import http, fields, _
from odoo.http import request

from odoo.addons.sale_timesheet.controllers.main import SaleTimesheetController


DEFAULT_MONTH_RANGE = 3


class TimesheetForecastController(SaleTimesheetController):

    def _table_get_line_values(self, projects):
        result = super(TimesheetForecastController, self)._table_get_line_values(projects)

        if any(projects.mapped('allow_forecast')):
            # add headers
            result['header'] += [{
                'label': _('Remaining \n (Forecasts incl.)'),
                'tooltip': _('What is still to deliver based on sold hours, hours already done and forecasted hours. Equals to sold hours - done hours - forecasted hours.'),
            }]

            # add last column to compute the second remaining with forecast
            for row in result['rows']:
                # Sold - Done (current month excl.) - MAX (Done and Forecasted for this month) - Forecasted (current month excl.)
                row += [row[-2] - (row[5] - row[4]) - max(row[4], row[6]) - (row[10] - row[6])]
        return result

    def _table_header(self, projects):
        header = super(TimesheetForecastController, self)._table_header(projects)

        def _to_short_month_name(date):
            month_index = fields.Date.from_string(date).month
            return babel.dates.get_month_names('abbreviated', locale=request.env.context.get('lang', 'en_US'))[month_index]

        if any(projects.mapped('allow_forecast')):
            initial_date = fields.Date.from_string(fields.Date.today())
            fc_months = sorted([fields.Date.to_string(initial_date + relativedelta(months=i, day=1)) for i in range(0, DEFAULT_MONTH_RANGE)])  # M3, M4, M5

            new_header = header[0:-2]
            for header_name in [_to_short_month_name(date) for date in fc_months] + [_('After'), _('Forecasted')]:
                new_header.append({
                    'label': header_name,
                    'tooltip': '',
                })
            header = new_header + header[-2:]

        return header

    def _table_row_default(self, projects):
        default_row = super(TimesheetForecastController, self)._table_row_default(projects)
        if any(projects.mapped('allow_forecast')):
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # before, M1, M2, M3, Done, M3, M4, M5, After, Forecasted, Sold, Remaining
        return default_row  # before, M1, M2, M3, Done, Sold, Remaining

    def _table_rows_sql_query(self, projects):
        query, query_params = super(TimesheetForecastController, self)._table_rows_sql_query(projects)

        initial_date = fields.Date.from_string(fields.Date.today())
        fc_months = sorted([fields.Date.to_string(initial_date + relativedelta(months=i, day=1)) for i in range(0, DEFAULT_MONTH_RANGE)])  # M3, M4, M5

        if any(projects.mapped('allow_forecast')):
            query += """
                UNION
                SELECT
                    'forecast' AS type,
                    date_trunc('month', date)::date AS month_date,
                    F.employee_id AS employee_id,
                    S.order_id AS sale_order_id,
                    F.order_line_id AS sale_line_id,
                    SUM(F.resource_hours) / SUM(F.working_days_count) * count(*) AS number_hours
                FROM generate_series(
                    (SELECT min(start_date) FROM project_forecast WHERE active=true)::date,
                    (SELECT max(end_date) FROM project_forecast WHERE active=true)::date,
                    '1 day'::interval
                ) date
                    LEFT JOIN project_forecast F ON date >= F.start_date AND date <= end_date
                    LEFT JOIN hr_employee E ON F.employee_id = E.id
                    LEFT JOIN resource_resource R ON E.resource_id = R.id
                    LEFT JOIN sale_order_line S ON F.order_line_id = S.id
                WHERE
                    EXTRACT(ISODOW FROM date) IN (
                        SELECT A.dayofweek::integer+1 FROM resource_calendar_attendance A WHERE A.calendar_id = R.calendar_id
                    )
                    AND F.active=true
                    AND F.project_id IN %s
                    AND date_trunc('month', date)::date >= %s
                    AND F.resource_hours > 0
                    AND F.employee_id IS NOT NULL
                GROUP BY F.project_id, F.task_id, date_trunc('month', date)::date, F.employee_id, S.order_id, F.order_line_id
            """
            query_params += (tuple(projects.ids), fc_months[0])
        return query, query_params

    def _table_rows_get_employee_lines(self, projects, data_from_db):
        rows_employee = super(TimesheetForecastController, self)._table_rows_get_employee_lines(projects, data_from_db)
        if not any(projects.mapped('allow_forecast')):
            return rows_employee

        initial_date = fields.Date.today()
        fc_months = sorted([initial_date + relativedelta(months=i, day=1) for i in range(0, DEFAULT_MONTH_RANGE)])  # M3, M4, M5
        default_row_vals = self._table_row_default(projects)

        # extract employee names
        employee_ids = set()
        for data in data_from_db:
            employee_ids.add(data['employee_id'])
        map_empl_names = {empl.id: empl.name for empl in request.env['hr.employee'].sudo().browse(employee_ids)}

        # extract rows data for employee, sol and so rows
        for data in data_from_db:
            sale_line_id = data['sale_line_id']
            sale_order_id = data['sale_order_id']
            # employee row
            row_key = (data['sale_order_id'], sale_line_id, data['employee_id'])
            if row_key not in rows_employee:
                meta_vals = {
                    'label': map_empl_names.get(row_key[2]),
                    'sale_line_id': sale_line_id,
                    'sale_order_id': sale_order_id,
                    'res_id': row_key[2],
                    'res_model': 'hr.employee',
                    'type': 'hr_employee'
                }
                rows_employee[row_key] = [meta_vals] + default_row_vals[:]  # INFO, before, M1, M2, M3, Done, M3, M4, M5, After, Forecasted

            index = False
            if data['type'] == 'forecast':
                if data['month_date'] in fc_months:
                    index = fc_months.index(data['month_date']) + 6
                elif data['month_date'] > fc_months[-1]:
                    index = 9
                rows_employee[row_key][index] += data['number_hours']
                rows_employee[row_key][10] += data['number_hours']
        return rows_employee

    def _table_get_empty_so_lines(self, projects):
        """ get the Sale Order Lines having no forecast but having generated a task or a project """
        empty_line_ids, empty_order_ids = super(TimesheetForecastController, self)._table_get_empty_so_lines(projects)
        sale_line_ids = request.env['project.task'].sudo().search_read([('project_id', 'in', projects.ids), ('sale_line_id', '!=', False)], ['sale_line_id'])
        sale_line_ids = [line_id['sale_line_id'][0] for line_id in sale_line_ids]
        order_ids = request.env['sale.order.line'].sudo().search_read([('id', 'in', sale_line_ids)], ['order_id'])
        order_ids = [order_id['id'] for order_id in order_ids]
        so_line_data = request.env['sale.order.line'].sudo().search_read([('order_id', 'in', order_ids), '|', ('task_id', '!=', False), ('project_id', '!=', False), ('analytic_line_ids', '=', False)], ['id', 'order_id'])
        so_line_ids = [so_line['id'] for so_line in so_line_data]
        order_ids = [so_line['order_id'][0] for so_line in so_line_data]
        return empty_line_ids | set(so_line_ids), empty_order_ids | set(order_ids)

    # --------------------------------------------------
    # Actions: Stat buttons, ...
    # --------------------------------------------------

    def _plan_get_stat_button(self, projects):
        stat_buttons = super(TimesheetForecastController, self)._plan_get_stat_button(projects)
        if any(projects.mapped('allow_forecast')):
            stat_buttons.append({
                'name': _('Forecasts'),
                'res_model': 'project.forecast',
                'domain': [('project_id', 'in', projects.ids)],
                'icon': 'fa fa-tasks',
            })
        return stat_buttons

    @http.route('/timesheet/plan/action', type='json', auth="user")
    def plan_stat_button(self, domain=[], res_model='account.analytic.line', res_id=False):
        action = super(TimesheetForecastController, self).plan_stat_button(domain=domain, res_model=res_model, res_id=res_id)
        if res_model == 'project.forecast':
            forecasts = request.env['project.forecast'].search(literal_eval(domain))
            projects = forecasts.mapped('project_id')
            if len(projects) == 1:
                action = request.env['project.forecast'].with_context(active_id=projects.id).action_view_forecast('project_forecast.project_forecast_action_from_project')
                action['context']['default_project_id'] = projects.id
            else:
                action = request.env['project.forecast'].action_view_forecast('project_forecast.project_forecast_action_by_project')
            action.update({
                'name': _('Forecasts'),
                'domain': domain,
            })
            action.setdefault('context', {})['search_default_future'] = 0
        return action
