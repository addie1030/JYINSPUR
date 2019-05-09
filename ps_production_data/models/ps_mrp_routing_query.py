# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PsMrpRoutingQuery(models.Model):
    _name = "ps.mrp.routing.query"
    _description = 'Query of MRP Routing'
    _auto = False

    code = fields.Char(string='Routing Reference')  # 工艺编号
    name = fields.Char(string='Routing')  # 工艺名称
    version = fields.Integer(string='Version')  # 工艺版本号
    ps_process_sequence = fields.Integer(string="Process Sequence")  # 工序顺序号
    operation_name = fields.Char(string='Process')  # 工序
    workcenter_name = fields.Char(string='Work Center')  # 工作中心
    time_cycle = fields.Float(string='Process Duration')  # 加工时间
    ps_salary_type = fields.Selection([
        ('time', 'Reckon by Time'),  # 计时
        ('piece', 'Reckon by Piece')],  # 计件
        string="Salary Type")  # 工资类型
    ps_price_unit = fields.Float(string="Salary Unit Price")  # 工资单价
    company_id = fields.Many2one('res.company', string='Company')  # 公司
    routing_id = fields.Many2one('mrp.routing', 'Routing')  # 工艺

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        is_mrp_plm_installed = self.env['ir.module.module'].search(
            [('name', '=', 'mrp_plm'), ('state', '=', 'installed')])
        if is_mrp_plm_installed:
            query = """
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        MR.code AS code,
                        MR.name AS name,
                        MR.version AS version,
                        MRW.ps_process_sequence AS ps_process_sequence, 
                        MRW.name AS operation_name,
                        MW.name AS workcenter_name,
                        MRW.time_cycle AS time_cycle,
                        MRW.ps_salary_type AS ps_salary_type,
                        MRW.ps_price_unit AS ps_price_unit,
                        MR.company_id AS company_id,
                        MRW.routing_id AS routing_id
                    FROM mrp_routing_workcenter MRW 
                    LEFT JOIN mrp_routing MR ON MRW.routing_id = MR.id
                    LEFT JOIN mrp_workcenter MW ON MRW.workcenter_id = MW.id
                    ORDER BY ps_process_sequence
            )"""% self._table
            self.env.cr.execute(query)
        else:
            query = """
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        MR.code AS code,
                        MR.name AS name,
                        CAST(null AS int) AS version,
                        MRW.ps_process_sequence AS ps_process_sequence, 
                        MRW.name AS operation_name,
                        MW.name AS workcenter_name,
                        MRW.time_cycle AS time_cycle,
                        MRW.ps_salary_type AS ps_salary_type,
                        MRW.ps_price_unit AS ps_price_unit,
                        MR.company_id AS company_id,
                        MRW.routing_id AS routing_id
                    FROM mrp_routing_workcenter MRW 
                    LEFT JOIN mrp_routing MR ON MRW.routing_id = MR.id
                    LEFT JOIN mrp_workcenter MW ON MRW.workcenter_id = MW.id
                    ORDER BY ps_process_sequence
            )""" % self._table
            self.env.cr.execute(query)

    @api.multi
    def action_query_relevant_product_info(self):
        self.ensure_one()
        action = self.env.ref('ps_production_data.action_ps_production_return_mrp_routing_query').read()[0]
        records = self.env['ps.mrp.query.return'].search([('routing_id', '=', self.routing_id.id)])
        if len(records) > 0:
            action['domain'] = [('routing_id', '=', self.routing_id.id)]
        else:
            raise UserError(_('No records matched.'))
        return action

