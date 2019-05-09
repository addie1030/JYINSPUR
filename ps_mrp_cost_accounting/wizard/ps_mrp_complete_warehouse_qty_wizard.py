# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PsMrpCompleteWarehouseQtyWizard(models.Model):
    _name = 'ps.mrp.complete.warehouse.qty.wizard'
    _description = 'Ps Mrp Complete Warehouse Quantity Wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间

    @api.multi
    def _get_values(self):
        for rec in self:
            date_start = rec.period_id.date_start
            date_end = rec.period_id.date_end
            location_ids = self.env['stock.location'].search([('usage', '=', 'production')])
            location_id = []
            for location in location_ids:
                location_id.append(location.id)
            stock_move_lines = self.env['stock.move.line'].search(
                [('date', '>=', date_start), ('date', '<=', date_end), ('state', '=', 'done'),
                 ('location_id', 'in', location_id)])
        return stock_move_lines

    @api.multi
    def _set_values(self):
        stock_move_lines = self._get_values()
        completed_warehouse_qty = self.env['ps.mrp.completed.warehouse.qty']
        mrp_production = self.env['mrp.production']
        cost_accounting = self.env['ps.mrp.cost.accounting']  # 成本中心
        for stock_move_line in stock_move_lines:
            cost_account_id = False
            workcenter_ids = []  # 工作中心id
            production = mrp_production.search([('name', '=', stock_move_line.reference)])
            for operation in production.routing_id.operation_ids:
                workcenter_ids.append(operation.workcenter_id.id)
            cost_account_ids = cost_accounting.search([('workcenter_id', 'in', tuple(workcenter_ids))])
            for cost_account in cost_account_ids:
                if len(cost_account.workcenter_id) >= len(workcenter_ids):
                    cost_account_id = cost_account.id
            completed_qty = completed_warehouse_qty.search([('name', '=', stock_move_line.reference)])
            # 如果之前未归集，则创建一条新的数据；如果已经归集过，则更新已有数据
            if not completed_qty:
                if production:
                    # 创建一条新的数据
                    completed_warehouse_qty.create({
                        'stock_move_line_id': stock_move_line.id,
                        'name': stock_move_line.reference,  # 单据编号
                        'date': fields.Date.today(),  # 业务日期
                        'product_id': stock_move_line.product_id.id,  # 产品id
                        'cost_account_id': cost_account_id,  # 成本中心
                        'qty_done': stock_move_line.qty_done,  # 完成数量
                        'stock_state': stock_move_line.state,  # 库存状态
                        'stock_location_id': stock_move_line.location_dest_id.id,  # 仓库
                    })
            else:
                if production:
                    completed_qty.update({
                        'date': fields.Date.today(),  # 业务日期
                        'product_id': stock_move_line.product_id.id,  # 产品id
                        'cost_account_id': cost_account_id,  # 成本中心
                        'qty_done': stock_move_line.qty_done,  # 完成数量
                        'stock_state': stock_move_line.state,  # 库存状态
                        'stock_location_id': stock_move_line.location_dest_id.id,  # 仓库
                    })

    @api.multi
    def complete(self):
        self._set_values()
        self.unlink()

