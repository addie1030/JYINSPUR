# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


_logger = logging.getLogger(__name__)


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    _order = 'ps_process_sequence'

    ps_process_sequence = fields.Integer(string="Process sequence")  # 工序顺序号

    ps_salary_type = fields.Selection([
        ('time', 'reckon by time'),  # 计时
        ('piece', 'reckon by the piece')],  # 计件
        string="Salary type",  # 工资类型
        require=True, default='piece')
    ps_price_unit = fields.Float(string="Salary unit price")  # 工资单价
    time_cycle = fields.Float(store=True)


    @api.onchange('workcenter_id')
    def _onchange_workcenter_id(self):
        """
        选择工作中心，带出工资类型和工资单价
        """
        for line in self:
            line.ps_salary_type = line.workcenter_id.ps_salary_type
            line.ps_price_unit = line.workcenter_id.costs_hour

