# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class Project(models.Model):

    _inherit = "project.project"

    @api.multi
    def action_view_project_forecast(self):
        """ Override to display remaining hours in task name get """
        return super(Project, self.with_context(project_task_display_forecast=True)).action_view_project_forecast()


class Task(models.Model):

    _inherit = 'project.task'

    @api.multi
    def name_get(self):
        if 'project_task_display_forecast' in self._context:
            result = []
            for task in self:
                result.append((task.id, _('%s (%s remaining hours)') % (task.name, task.remaining_hours)))
            return result
        return super(Task, self).name_get()
