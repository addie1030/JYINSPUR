# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_overdue = fields.Boolean('Is overdue', compute="_compute_is_overdue",
        help="Indicates more support time has been delivered thant the ordered quantity")

    @api.depends('task_id.sale_line_id')
    def _compute_is_overdue(self):
        for ticket in self.filtered('task_id.sale_line_id'):
            sale_line_id = ticket.task_id.sale_line_id
            ticket.is_overdue = sale_line_id.qty_delivered >= sale_line_id.product_uom_qty
