# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', 'Helpdesk Ticket')

    @api.onchange('project_id')
    def onchange_project_id(self):
        result = super(AccountAnalyticLine, self).onchange_project_id()
        if self.helpdesk_ticket_id:
            self.task_id = self.helpdesk_ticket_id.task_id
        return result
