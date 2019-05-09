# -*- coding: utf-8 -*-

from datetime import date, timedelta, time, datetime
from dateutil.relativedelta import relativedelta, MO, SU
from lxml import etree
import pytz
import logging

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_round
from odoo.osv import expression
from odoo.tools import pycompat

from odoo.addons.resource.models.resource import HOURS_PER_DAY

_logger = logging.getLogger(__name__)


class ProjectForecast(models.Model):
    _name = 'project.forecast'
    _description = 'Project Forecast'

    def _default_employee_id(self):
        user_id = self.env.context.get('default_user_id', self.env.uid)
        employee_ids = self.env['hr.employee'].search([('user_id', '=', user_id)])
        return employee_ids and employee_ids[0] or False

    def _default_start_date(self):
        forecast_span = self.env.user.company_id.forecast_span
        start_date = date.today()
        # grid context: default start date should be the one of the first grid column
        if self._context.get('grid_anchor'):
            start_date = fields.Date.from_string(self._context['grid_anchor'])

        if forecast_span == 'week':
            start_date += relativedelta(weekday=MO(-1))  # beginning of current week
        elif forecast_span == 'month':
            start_date += relativedelta(day=1)  # beginning of current month
        return fields.Date.to_string(start_date)

    def _default_end_date(self):
        forecast_span = self.env.user.company_id.forecast_span

        start_date = self._default_start_date()
        if 'default_start_date' in self._context:
            start_date = self._context.get('default_start_date')
        start_date = fields.Date.from_string(start_date)

        delta = relativedelta()
        if forecast_span == 'week':
            delta = relativedelta(weekday=SU)  # end of current week
        elif forecast_span == 'month':
            delta = relativedelta(months=1, day=1, days=-1)  # end of current month
        return fields.Date.to_string(start_date + delta)

    def _read_group_employee_ids(self, employee, domain, order):
        group = self.env.ref('project.group_project_user', False) or self.env.ref('base.group_user')
        return self.env['hr.employee'].search([('user_id', 'in', group.users.ids)])

    name = fields.Char(compute='_compute_name')
    active = fields.Boolean(default=True)
    employee_id = fields.Many2one('hr.employee', "Employee", default=_default_employee_id, required=True, group_expand='_read_group_employee_ids')
    user_id = fields.Many2one('res.users', string="User", related='employee_id.user_id', store=True, readonly=True)
    project_id = fields.Many2one('project.project', string="Project", required=True)
    task_id = fields.Many2one(
        'project.task', string="Task", domain="[('project_id', '=', project_id)]",
        group_expand='_read_forecast_tasks')
    company_id = fields.Many2one('res.company', string="Company", related='project_id.company_id', store=True, readonly=True)

    # used in custom filter
    stage_id = fields.Many2one(related='task_id.stage_id', string="Task stage", readonly=False)
    tag_ids = fields.Many2many(related='task_id.tag_ids', string="Task tags", readonly=False)

    time = fields.Float(string="Allocated time / Time span", help="Percentage of working time", compute='_compute_time', store=True, digits=(16, 2))

    start_date = fields.Date(default=_default_start_date, required=True)
    end_date = fields.Date(default=_default_end_date, required=True)
    # consolidation color and exclude
    color = fields.Integer(string="Color", compute='_compute_color')
    exclude = fields.Boolean(string="Exclude", compute='_compute_exclude', store=True)

    # resource
    resource_hours = fields.Float(string="Planned hours", default=0)
    resource_time = fields.Float("Allocated Time", compute='_compute_resource_time', inverse='_inverse_resource_time', compute_sudo=True, store=True, help="Expressed in the Unit of Measure of the project company")
    forecast_uom = fields.Selection(related='company_id.forecast_uom', readonly=True)

    _sql_constraints = [
        ('check_start_date_lower_end_date', 'CHECK(end_date >= start_date)', 'Forecast end date should be greater or equal to its start date'),
    ]

    @api.one
    @api.depends('project_id', 'task_id', 'employee_id')
    def _compute_name(self):
        group = self.env.context.get("group_by", "")

        name = []
        if "employee_id" not in group:
            name.append(self.employee_id.name)
        if ("project_id" not in group):
            name.append(self.project_id.name)
        if ("task_id" not in group and self.task_id):
            name.append(self.task_id.name)

        if name:
            self.name = " - ".join(name)
        else:
            self.name = _("undefined")

    @api.one
    @api.depends('project_id.color')
    def _compute_color(self):
        self.color = self.project_id.color or 0

    @api.one
    @api.depends('project_id.name')
    def _compute_exclude(self):
        self.exclude = (self.project_id.name == "Leaves")

    @api.one
    @api.depends('resource_hours', 'start_date', 'end_date', 'employee_id')
    def _compute_time(self):
        if not self.employee_id:
            return

        # We want to compute the number of hours that an **employee** works between 00:00:00 and 23:59:59
        # according to him -- his **timezone**
        start = datetime.combine(self.start_date, time.min)
        stop = datetime.combine(self.end_date, time.max)
        employee_tz = self.employee_id.user_id.tz and pytz.timezone(self.employee_id.user_id.tz)
        if employee_tz:
            start = employee_tz.localize(start).astimezone(pytz.utc)
            stop = employee_tz.localize(stop).astimezone(pytz.utc)
        tz_warning = _('The employee (%s) doesn\'t have a timezone, this might cause errors in the time computation. It is configurable on the user linked to the employee') % self.employee_id.name
        if not employee_tz:
            _logger.warning(tz_warning)
        hours = self.employee_id.get_work_days_data(start, stop, compute_leaves=False)['hours']
        if hours > 0:
            self.time = self.resource_hours * 100.0 / hours
        else:
            self.time = 0  # allow to create a forecast for a day you are not supposed to work

    @api.multi
    @api.depends('resource_hours', 'company_id.forecast_uom', 'project_id.resource_calendar_id')
    def _compute_resource_time(self):
        for forecast in self:
            factor = 1.0
            if forecast.company_id.forecast_uom == 'day':
                calendar = forecast.project_id.resource_calendar_id or forecast.company_id.resource_calendar_id
                factor = calendar.hours_per_day if calendar else HOURS_PER_DAY
            forecast.resource_time = float_round(forecast.resource_hours / factor, precision_digits=2)

    @api.multi
    def _inverse_resource_time(self):
        for forecast in self:
            factor = 1.0
            if forecast.company_id.forecast_uom == 'day':
                calendar = forecast.project_id.resource_calendar_id or forecast.company_id.resource_calendar_id
                factor = calendar.hours_per_day if calendar else HOURS_PER_DAY
            forecast.resource_hours = float_round(forecast.resource_time * factor, precision_digits=2)

    @api.one
    @api.constrains('resource_hours')
    def _check_time_positive(self):
        if self.resource_hours and self.resource_hours < 0:
            raise ValidationError(_("Forecasted time must be positive"))

    @api.one
    @api.constrains('task_id', 'project_id')
    def _check_task_in_project(self):
        if self.task_id and (self.task_id not in self.project_id.tasks):
            raise ValidationError(_("Your task is not in the selected project."))

    @api.constrains('start_date', 'end_date', 'project_id', 'task_id', 'employee_id', 'active')
    def _check_overlap(self):
        self.env.cr.execute("""
            SELECT F1.id, F1.start_date, F1.end_date, F1.project_id, F1.task_id
            FROM project_forecast F1
            INNER JOIN project_forecast F2
                ON F1.employee_id = F2.employee_id AND F1.project_id = F2.project_id
            WHERE F1.id != F2.id
                AND (F1.task_id = F2.task_id OR (F1.task_id IS NULL AND F2.task_id IS NULL))
                AND (
                    F1.start_date BETWEEN F2.start_date AND F2.end_date
                    OR
                    F1.end_date BETWEEN F2.start_date AND F2.end_date
                    OR
                    F2.start_date BETWEEN F1.start_date AND F1.end_date
                )
                AND F1.active = 't'
                AND F1.id IN %s
        """, (tuple(self.ids),))
        data = self.env.cr.dictfetchall()

        project_ids = [item['project_id'] for item in data if item.get('project_id')]
        task_ids = [item['task_id'] for item in data if item.get('task_id')]
        if data:
            project_names = self.env['project.project'].browse(project_ids).mapped('name')
            task_names = self.env['project.task'].browse(task_ids).mapped('name')
            message = _('Forecast should not overlap existing forecasts. To solve this, check the project(s): %s.') % (' ,'.join(project_names),)
            if task_names:
                message = _('%s Task(s): %s' % (message, ' ,'.join(task_names),))
            raise ValidationError(message)

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id:
            self.project_id = self.task_id.project_id

    @api.onchange('project_id')
    def _onchange_project_id(self):
        domain = [] if not self.project_id else [('project_id', '=', self.project_id.id)]
        return {
            'domain': {'task_id': domain},
        }

    @api.onchange('start_date')
    def _onchange_start_date(self):
        self.end_date = self.with_context(default_start_date=self.start_date)._default_end_date()

    # ----------------------------------------------------
    # ORM overrides
    # ----------------------------------------------------

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Set the widget `float_time` on `resource_time` field on view, depending on company configuration (so it can not be a groups on inherited view) """
        result = super(ProjectForecast, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type in ['tree', 'form', 'grid'] and self.env.user.company_id.forecast_uom == 'hour':
            doc = etree.XML(result['arch'])
            for node in doc.xpath("//field[@name='resource_time']"):
                node.set('widget', 'float_time')
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

    # ----------------------------------------------------
    # Actions
    # ----------------------------------------------------

    @api.model
    def action_view_forecast(self, action_xmlid=None):
        """ This method extends the context of action defined in xml files to
            customize it according to the forecast span of the current company.

            :param action_xmlid: complete xml id of the action to return
            :returns action (dict): an action with a extended context, evaluable
                by the webclient
        """
        if not action_xmlid:
            action_xmlid = 'project_forecast.project_forecast_action_from_project'

        action = self.env.ref(action_xmlid).read()[0]
        context = {}
        if action.get('context'):
            eval_context = self.env['ir.actions.actions']._get_eval_context()
            if 'active_id' in self._context:
                eval_context.update({'active_id': self._context.get('active_id')})
            context = safe_eval(action['context'], eval_context)
        # add the default employee (for creation)
        if self.env.user.employee_ids:
            context['default_employee_id'] = self.env.user.employee_ids[0].id
        # hide range button for grid view
        company = self.company_id or self.env.user.company_id
        if company.forecast_span == 'day':
            context['forecast_hide_range_month'] = True
            context['forecast_hide_range_year'] = True
        elif company.forecast_span == 'week':
            context['forecast_hide_range_week'] = True
            context['forecast_hide_range_year'] = True
        elif company.forecast_span == 'month':
            context['forecast_hide_range_week'] = True
            context['forecast_hide_range_month'] = True
        action['context'] = context
        # include UoM in action name, because in grid view we only see number and we don't know if it is hours or days
        action['display_name'] = _('Forecast (in %s)') % ({key: value for key, value in self._fields['forecast_uom']._description_selection(self.env)}[company.forecast_uom],)
        return action

    # ----------------------------------------------------
    # Grid View Stuffs
    # ----------------------------------------------------

    def _grid_pagination(self, field, span, step, anchor):
        """ For forecast, we want the next and previous anchor date to be the border of the period, in order
            to se the default start_date value to match the beginning of the forecast span (of the company)
        """
        pagination = super(ProjectForecast, self)._grid_pagination(field, span, step, anchor)
        if field.type == 'date':
            for pagination_key in ['next', 'prev']:
                val = field.from_string(pagination[pagination_key]['default_%s' % field.name])
                pagination[pagination_key]['default_%s' % field.name] = field.to_string(self._grid_start_of(span, step, val))
        return pagination

    @api.multi
    def adjust_grid(self, row_domain, column_field, column_value, cell_field, change):
        if column_field != 'start_date' or cell_field != 'resource_time':
            raise exceptions.UserError(
                _("Grid adjustment for project forecasts only supports the "
                  "'start_date' columns field and the 'resource_time' cell "
                  "field, got respectively %(column_field)r and "
                  "%(cell_field)r") % {
                    'column_field': column_field,
                    'cell_field': cell_field,
                }
            )

        from_, to_ = pycompat.imap(fields.Date.from_string, column_value.split('/'))
        start = fields.Date.to_string(from_)
        # range is half-open get the actual end date
        end = fields.Date.to_string(to_ - relativedelta(days=1))

        # see if there is an exact match
        cell = self.search(expression.AND([row_domain, [
            '&',
            ['start_date', '=', start],
            ['end_date', '=', end]
        ]]), limit=1)
        # if so, adjust in-place
        if cell:
            cell[cell_field] += change
            return False

        # otherwise copy an existing cell from the row, ignore eventual
        # non-monthly forecast
        self.search(row_domain, limit=1).ensure_one().copy({
            'start_date': start,
            'end_date': end,
            cell_field: change,
        })
        return False

    # ----------------------------------------------------
    # Business Methods
    # ----------------------------------------------------

    @api.model
    def _read_forecast_tasks(self, tasks, domain, order):
        tasks_domain = [('id', 'in', tasks.ids)]
        if 'default_project_id' in self.env.context:
            tasks_domain = expression.OR([
                tasks_domain,
                [('project_id', '=', self.env.context['default_project_id'])]
            ])
        return tasks.sudo().search(tasks_domain, order=order)
