# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PsMrpInvestYieldCollectionWizard(models.Model):
    _name = 'ps.mrp.in.product.cost.calculation.wizard'
    _description = 'Ps Mrp In Product Cost Calculation Wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间

    # @api.multi
    # def _get_values(self):
    #     for rec in self:
    #         date_start = rec.period_id.date_start
    #         date_end = rec.period_id.date_end
    #         mrp_products = self.env['mrp.production'].search(
    #             [('state', 'not in', ('confirmed', 'cancel')), ('date_planned_start', '>=', date_start),
    #              ('date_planned_start', '<=', date_end)])  # 生产订单
    #         yield_collects = []
    #         for mrp_product in mrp_products:
    #             cost_account_id = False
    #             workcenter_ids = []
    #             for operation in mrp_product.routing_id.operation_ids:
    #                 workcenter_ids.append(operation.workcenter_id.id)  # 工作中心id
    #             cost_accounts = self.env['ps.mrp.cost.accounting'].search(
    #                 [('workcenter_id', 'in', tuple(workcenter_ids))])
    #             for cost_account in cost_accounts:
    #                 if len(cost_account.workcenter_id) >= len(workcenter_ids):
    #                     cost_account_id = cost_account.id  # 成本中心id
    #             yield_collects.append({
    #                 'product_id': mrp_product.product_id.id,
    #                 'mrp_production_id': mrp_product.id,
    #                 'cost_account_id': cost_account_id,
    #                 'product_qty': mrp_product.product_qty,
    #             })
    #     return yield_collects
    #
    # @api.multi
    # def _set_values(self):
    #     yield_collects = self._get_values()
    #     yield_collections = self.env['ps.mrp.invest.yield.collection']
    #     for yield_collect in yield_collects:
    #         # 如果是第一次归集过，那么创建新的数据，否则更新之前数据
    #         collect = yield_collections.search([('mrp_production_id', '=', yield_collect['mrp_production_id'])])
    #         if not collect:
    #             yield_collections.create({
    #                 'product_id': yield_collect['product_id'],
    #                 'mrp_production_id': yield_collect['mrp_production_id'],
    #                 'cost_account_id': yield_collect['cost_account_id'],
    #                 'product_qty': yield_collect['product_qty'],
    #             })
    #         else:
    #             collect.update({
    #                 'product_id': yield_collect['product_id'],
    #                 'mrp_production_id': yield_collect['mrp_production_id'],
    #                 'cost_account_id': yield_collect['cost_account_id'],
    #                 'product_qty': yield_collect['product_qty'],
    #             })
    #
    @api.multi
    def calculate(self):
        print('calculate')
        # self._set_values()
        self.unlink()
