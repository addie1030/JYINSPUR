# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError, ValidationError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    @api.depends('ps_qty_ng')
    def _compute_ps_check_result(self):
        for self in self:
            # if self.type == 'all':
            #     self.ps_check_result = 'hold'
            # else:

            if self.ps_qty_ng > 0:
                self.ps_check_result = 'failed'
            else:
                self.ps_check_result = 'qualified'

    testing_item_id = fields.Many2one('ps.quality.testing.item', string='Testing Item')
    type = fields.Selection([
        ('all', 'All'),
        ('gb', 'GB'),
    ], string='Type')

    check_level = fields.Many2one("ps.quality.inspection.level", string="Inspection Level")
    ps_check_result = fields.Selection(
        [('qualified', 'Qualified'), ('failed', 'Failed'), ('hold', 'Hold')],
        string="Check Result", compute=_compute_ps_check_result)
    ps_check_quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="Quantity Check")
    ps_qty_ok = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="Quantity Qualified", )
    ps_qty_ng = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="Quantity Failed",
                             compute="_compute_ps_qty", store=True)
    ps_failed_qty = fields.Float(string="Failed Qty")

    @api.onchange('ps_failed_qty')
    def onchange_ps_failed_qty(self):

        check_ids = self.env.context.get('check_ids', None)
        if check_ids:
            cmd = self.ps_quality_id.resolve_2many_commands('check_ids', check_ids)

        if self.type == 'all' and self.ps_failed_qty > self.ps_check_quantity:
            # 当类型为全检时，录入的数量不能超过检查数量
            raise UserError(_("The quality failed qty can not bigger than the check quantity  when type is all"))

        if self.type == 'gb' and self.ps_failed_qty > self.sample_size:
            # 当类型为国标抽样时，录入的数量不能超过样本数量
            raise UserError(_("The quality failed qty can not bigger than the sample quantity  when type is gb"))

    sample_size = fields.Integer(string='Sample Size', compute="_compute_type_result")
    quantity_accept = fields.Integer(string='Quantity Accept', compute="_compute_type_result")
    quantity_reject = fields.Integer(string='Quantity Reject', compute="_compute_type_result")
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', 'in', ['consu', 'product'])]", required=False)
    team_id = fields.Many2one(required=False)


    def _get_sampling_code(self, quantity, check_level, aql, strictness):
        if quantity < 5000000:
            sampling_code = self.env['ps.quality.sampling.code'].search(
                [('inspection_level', '=', check_level), ('size_begin', '<=', quantity),
                 ('size_end', '>=', quantity)], limit=1).code
        else:
            sampling_code = self.env['ps.quality.sampling.code'].search(
                [('inspection_level', '=', check_level)
                 ('size_end', '<=', quantity)], limit=1).code

        plan_id = self.env['ps.quality.sampling.plan.line'].search(
            [('plan_id.aql', '=', aql),
             ('sample_size_code', '=', sampling_code),
             ('plan_id.strictness', '=', strictness)])
        if plan_id:
            return plan_id.sample_size, plan_id.quantity_accept, plan_id.quantity_reject
        else:
            return 0, 0, 0

    @api.depends('ps_inspection_plan_id', 'type', 'check_level')
    def _compute_type_result(self):
        """
        根据抽样方案的类型进行计算是否合格

        全检：可以部分合格与部分不合格
        国标抽样：只能整单合格与不合格
                根据被检查数量和检查水平去查找样本量字码的code
                然后根据code 和AQL查找允收数和拒收数

        :return:
        """
        for line in self:
            if line.type == 'all':
                continue

            sample_size, quantity_accept, quantity_reject = self.env['quality.check']._get_sampling_code(
                line.ps_check_quantity,
                line.check_level.id,
                line.testing_item_id.aql.id,
                line.testing_item_id.strictness)

            line.sample_size = sample_size
            line.quantity_accept = quantity_accept
            line.quantity_reject = quantity_reject

            # if line.ps_check_quantity < 5000000:
            #     sampling_code = self.env['ps.quality.sampling.code'].search(
            #         [('inspection_level', '=', line.check_level.id), ('size_begin', '<=', line.ps_check_quantity),
            #          ('size_end', '>=', line.ps_check_quantity)], limit=1).code
            # else:
            #     sampling_code = self.env['ps.quality.sampling.code'].search(
            #         [('inspection_level', '=', line.check_level.id)
            #          ('size_end', '<=', line.ps_check_quantity)], limit=1).code
            #
            # plan_id = self.env['ps.quality.sampling.plan.line'].search(
            #     [('plan_id.aql', '=', line.testing_item_id.aql.id),
            #      ('sample_size_code', '=', sampling_code),
            #      ('plan_id.strictness', '=', line.testing_item_id.strictness)])
            # if plan_id:
            #     line.sample_size = plan_id.sample_size
            #     line.quantity_accept = plan_id.quantity_accept
            #     line.quantity_reject = plan_id.quantity_reject

    @api.depends('ps_data_ids', 'ps_failed_qty', 'is_check_data')
    def _compute_ps_qty(self):
        for self in self:
            if self.is_check_data:
                for rec in self.ps_data_ids:
                    if rec.value_type == 'quantitative':
                        if (rec.value_measured < rec.lower_limit or rec.value_measured > rec.upper_limit):
                            self.ps_qty_ng += rec.qty
                            self.ps_failed_qty += rec.qty
                    else:
                        if not rec.qty_qualitative in rec.target_value_qualitative:
                            self.ps_qty_ng += rec.qty
                            self.ps_failed_qty += rec.qty
            else:
                self.ps_qty_ng = self.ps_failed_qty
                # self.ps_failed_qty = self.ps_failed_qty

    ps_inspection_plan_id = fields.Many2one("ps.quality.inspection.plan", string="Inspection Plan")

    ps_partner_id = fields.Many2one('res.partner', string="Partner")
    ps_warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    ps_location_id = fields.Many2one('stock.location', string="Location")
    ps_quality_id = fields.Many2one('ps.quality.check.order', string="Quality Check Order")
    ps_data_ids = fields.One2many('ps.quality.check.data', 'check_id', string="Check Data")

    ps_name = fields.Char(string="Name", related="ps_quality_id.name")
    ps_type_id = fields.Many2one('stock.picking.type', string="Type", related="ps_quality_id.type_id")
    ps_description = fields.Char(string="Description", related="ps_quality_id.description")
    ps_document = fields.Reference(selection=[('stock.picking', 'Stock Picking')], string="Document",
                                   related="ps_quality_id.document")
    ps_sampling_plan_id = fields.Many2one("ps.quality.sampling.scheme", string="Sampling Plan")
    is_check_data = fields.Boolean(string="check data")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('validated', 'Validated'),
        ('cancel', 'Cancel'),
    ], string="States", default='draft', related="ps_quality_id.state")

    @api.onchange('is_check_data')
    def onchange_is_check_data(self):
        if self.is_check_data and self.ps_inspection_plan_id:
            plan_lines = []
            plan = self.env['quality.point'].search(
                [('testing_item_id', '=', self.testing_item_id.id), ('plan_id', '=', self.ps_inspection_plan_id.id)])
            # for plan in self.ps_inspection_plan_id.inspection_plan_testing_item_ids:
            values = (0, 0, {
                'target_value': plan.target_value_quantitative,
                'target_value_qualitative': plan.target_value_qualitative,
                'value_type': plan.method_type,
                'lower_limit': plan.lower_limit,
                'upper_limit': plan.upper_limit,
                'testing_item_id': plan.testing_item_id.id,
            })
            plan_lines.append(values)
            self.ps_data_ids = plan_lines
        else:
            self.ps_data_ids = False

    @api.onchange('ps_data_ids')
    def onchange_ps_data_ids(self):
        self.ps_qty_ng = 0
        for rec in self.ps_data_ids:
            if rec.value_type == 'quantitative':
                if (rec.value_measured < rec.lower_limit or rec.value_measured > rec.upper_limit):
                    self.ps_qty_ng += rec.qty
            else:
                if not rec.qty_qualitative in rec.target_value_qualitative:
                    self.ps_qty_ng += rec.qty

        total = sum(rec.qty for rec in self.ps_data_ids)
        if total > self.ps_check_quantity:
            raise UserError(_("Total quality check detail quantity can not bigger than quality check quantity"))
        if self.type == 'gb' and total > self.sample_size:
            raise UserError(_("Total quality check detail quantity can not bigger than quality check quantity"))
