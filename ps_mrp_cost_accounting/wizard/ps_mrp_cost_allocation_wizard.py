# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PsMrpCompleteWarehouseQtyWizard(models.Model):
    _name = 'ps.mrp.cost.allocation.wizard'
    _description = 'Ps Mrp Cost Allocation Wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period')  # 会计期间


    def _get_work_center(self, operation_ids):
        work_centers = []
        for op in operation_ids:
            work_center = op.workcenter_id
            work_centers.append(work_center.id)
        return work_centers

    def _get_cost_center(self, work_centers):
        cost_centers = self.env['ps.mrp.cost.accounting'].search([('workcenter_id', 'in', tuple(work_centers))])
        if cost_centers:
            for cc in cost_centers:
                if len(work_centers) == len(cc.workcenter_id):
                    cost_center = cc.id
                else:
                    raise ValidationError(_('Data abnormity.'))
            return cost_center
        else:
            raise ValidationError(_('No suitable cost center data.'))

    def _get_initial_quantity(self, is_current, order_number):
        # 获得期初数
        if is_current == 1:
            # 当期新增单据，没有期初数
            return 0
        else:
            # 取出期初数
            initial_quantity = self.env['ps.mrp.inventory'].search([('name','=',order_number)])
            if initial_quantity:
                return initial_quantity.product_inventory_qty
            else:
                raise ValidationError(_('No suitable data.'))

    def _get_current_input_quantity(self, is_current, mrp_pro):
        # 获得本期投入
        if is_current == 1:
            # 当期新增单据，有本期投入
            return mrp_pro.product_qty
        else:
            return 0

    def _get_cumulative_quantity(self, order_number):
        # 获得期末在产品
        # 工单计划数量-已完工数量
        pass

    def _get_complete_quantity_in(self):
        # 获得本期完工数
        # 本期库存移动数
        pass

    def _get_complete_cumulative_quantity(self, order_number):
        # 获得累计完工数
        complete_cumulative_quantity = self.env['stock.move.line'].search(['&',('reference','=',order_number),('location_id.usage','=','production')])
        return complete_cumulative_quantity.qty_done

    def _is_current_month(self, mrp_pro):
        # 判断是否为当期新增单据
        if mrp_pro.date_start.strftime("%Y-%m-%d") >= str(self.period_id.date_start):
            # 当期新增工单
            return 1
        else:
            # 历史期间工单
            return 0

    def _get_amount(self, number, mrp_pro):
        # 计算金额
        product_qty = mrp_pro.bom_id.product_qty
        bom_line_ids = mrp_pro.bom_id.bom_line_ids
        amount = 0.0
        for line in bom_line_ids:
            line_product_standard_price = line.product_id.standard_price
            line_product_qty = line.product_qty
            ratio = self._get_ratio(product_qty, line_product_qty)
            line_amount = line_product_standard_price * number * ratio
            amount += line_amount
        return amount


    def _get_ratio(self, product_qty, line_product_qty):
        # 根据BOM计算产品材料比
        return line_product_qty / product_qty

    @api.multi
    def _set_values(self):
        period_id = self.period_id.period # 会计期间
        date_start = self.period_id.date_start
        date_end = self.period_id.date_end
        mrp_production_progress = self.env['mrp.production'].search([('state','in',['progress']),('date_start','<=',date_end)])
        mrp_production_done = self.env['mrp.production'].search([('state','in',['done']),('date_finished','<=',date_end),('date_finished','>=',date_start)])
        mrp_production = mrp_production_progress + mrp_production_done
        # mrp_production = self.env['mrp.production'].search(['|','&','&',('date_start','<=',date_end),('date_finished','>=',date_start),('date_finished','=',None),('state','in',['progress','done'])])
        for mrp_pro in mrp_production:
            product_id = mrp_pro.product_id # 产品
            operation_ids = mrp_pro.routing_id.operation_ids
            work_centers = self._get_work_center(operation_ids)
            cost_center = self._get_cost_center(work_centers) # 成本中心
            order_number = mrp_pro.name # 工单编号
            plan_quantity = mrp_pro.product_qty # 计划产量
            if mrp_pro.state in ['progress', 'done']:
                is_current = self._is_current_month(mrp_pro)

                initial_quantity = self._get_initial_quantity(is_current, order_number) # 期初在产品数
                initial_amount = self._get_amount(initial_quantity, mrp_pro)

                current_input_quantity = self._get_current_input_quantity(is_current, mrp_pro) # 本期投入数
                current_input_amount = self._get_amount(current_input_quantity, mrp_pro)

                complete_cumulative_quantity = self._get_complete_cumulative_quantity(order_number) # 累计完工数
                complete_cumulative_amount = self._get_amount(complete_cumulative_quantity, mrp_pro)
                complete_cumulative_cost = complete_cumulative_amount / complete_cumulative_quantity

                cumulative_quantity = mrp_pro.product_qty - complete_cumulative_quantity  # 期末在产品
                cumulative_amount = self._get_amount(cumulative_quantity, mrp_pro)

                if is_current == 1:
                    complete_quantity_in = plan_quantity - cumulative_quantity # 本期完工
                else:
                    complete_quantity_in = initial_quantity - cumulative_quantity  # 本期完工
                complete_amount_in = self._get_amount(complete_quantity_in, mrp_pro)
                if complete_quantity_in > 0:
                    complete_cost_in = complete_amount_in / complete_quantity_in
                else:
                    complete_cost_in = None
            else:
                pass
            cost_allocation = self.env['ps.mrp.cost.allocation'].search([('order_number','=',order_number)])
            if cost_allocation:
                cost_allocation.update({
                    'period_id': period_id,
                    'product_id': product_id.id,
                    'cost_center': cost_center,
                    'order_number': order_number,
                    'plan_quantity': plan_quantity,
                    'initial_quantity': initial_quantity,
                    'initial_amount': initial_amount,
                    'current_input_quantity': current_input_quantity,
                    'current_input_amount': current_input_amount,
                    'cumulative_quantity': cumulative_quantity,
                    'cumulative_amount': cumulative_amount,
                    'complete_quantity_in': complete_quantity_in,
                    'complete_cost_in': complete_cost_in,
                    'complete_amount_in': complete_amount_in,
                    'complete_cumulative_quantity': complete_cumulative_quantity,
                    'complete_cumulative_cost': complete_cumulative_cost,
                    'complete_cumulative_amount': complete_cumulative_amount,
                })
            else:
                cost_allocation.create({
                    'period_id':period_id,
                    'product_id':product_id.id,
                    'cost_center':cost_center,
                    'order_number':order_number,
                    'plan_quantity':plan_quantity,
                    'initial_quantity':initial_quantity,
                    'initial_amount':initial_amount,
                    'current_input_quantity':current_input_quantity,
                    'current_input_amount':current_input_amount,
                    'cumulative_quantity':cumulative_quantity,
                    'cumulative_amount':cumulative_amount,
                    'complete_quantity_in':complete_quantity_in,
                    'complete_cost_in':complete_cost_in,
                    'complete_amount_in':complete_amount_in,
                    'complete_cumulative_quantity':complete_cumulative_quantity,
                    'complete_cumulative_cost':complete_cumulative_cost,
                    'complete_cumulative_amount':complete_cumulative_amount,
                })

    @api.multi
    def complete(self):
        self._set_values()
        self.unlink()

