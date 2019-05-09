# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    project_id = fields.Many2one("project.project", string="Project", ondelete="restrict")

    @api.model
    def create(self, vals):
        if vals.get('use_helpdesk_timesheet') and not vals.get('project_id'):
            vals['project_id'] = self.env['project.project'].create({
                'name': vals['name'],
                'type_ids': [
                    (0, 0, {'name': _('In Progress')}),
                    (0, 0, {'name': _('Closed'), 'is_closed': True})
                ]
            }).id
        return super(HelpdeskTeam, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'use_helpdesk_timesheet' in vals and not vals['use_helpdesk_timesheet']:
            vals['project_id'] = False
        result = super(HelpdeskTeam, self).write(vals)
        for team in self.filtered(lambda team: team.use_helpdesk_timesheet and not team.project_id):
            team.project_id = self.env['project.project'].create({
                'name': team.name,
                'type_ids': [
                    (0, 0, {'name': _('In Progress')}),
                    (0, 0, {'name': _('Closed'), 'is_closed': True})
                ]
            })
        return result


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def default_get(self, fields_list):
        result = super(HelpdeskTicket, self).default_get(fields_list)
        if result.get('team_id') and not result.get('project_id'):
            result['project_id'] = self.env['helpdesk.team'].browse(result['team_id']).project_id.id
        return result

    project_id = fields.Many2one("project.project", string="Project")
    task_id = fields.Many2one("project.task", string="Task", domain="[('project_id', '=', project_id)]", track_visibility="onchange", help="The task must have the same customer as this ticket.")
    timesheet_ids = fields.One2many('account.analytic.line', 'helpdesk_ticket_id', 'Timesheets')
    is_closed = fields.Boolean(related="task_id.stage_id.is_closed", string="Is Closed", readonly=True)
    is_task_active = fields.Boolean(related="task_id.active", string='Is Task Active', readonly=True)
    use_helpdesk_timesheet = fields.Boolean('Timesheet activated on Team', related='team_id.use_helpdesk_timesheet', readonly=True)

    @api.onchange('partner_id', 'project_id')
    def _onchange_partner_project(self):
        if self.project_id:
            domain = [('project_id', '=', self.project_id.id)]
            if self.partner_id:
                    domain.extend(['|',
                                   ('partner_id', 'child_of', self.partner_id.commercial_partner_id.id),
                                   ('partner_id', '=', False),
                                   ])
            # Take the latest task and set it.
            self.task_id = self.env['project.task'].search(domain, limit=1)
            return {'domain': {'task_id': domain}}

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.timesheet_ids:
            if self.task_id:
                msg = _("All timesheet hours will be assigned to the selected task on save. Discard to avoid the change.")
            else:
                msg = _("Timesheet hours will not be assigned to a customer task. Set a task to charge a customer.")
            return {'warning':
                {
                    'title': _("Warning"),
                    'message': msg
                }
            }

    @api.multi
    def write(self, values):
        result = super(HelpdeskTicket, self).write(values)
        if 'task_id' in values:
            self.sudo().mapped('timesheet_ids').write({'task_id': values['task_id']})  # sudo since helpdesk user can change task
        return result

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Set the correct label for `unit_amount`, depending on company UoM """
        result = super(HelpdeskTicket, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        result['arch'] = self.env['account.analytic.line']._apply_timesheet_label(result['arch'])
        return result

    @api.multi
    def action_view_ticket_task(self):
        self.ensure_one()
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'res_id': self.task_id.id,
        }
