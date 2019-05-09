# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class QualityControlPoint(models.Model):
    _inherit = "quality.point"

    plan_id = fields.Many2one('ps.quality.inspection.plan', string="Quality Inspection Plan", ondelete='cascade')

    picking_type_id = fields.Many2one('stock.picking.type', "Operation Type", required=False,
                                      default=lambda self: self.env.context.get('picking_type_id'))

    sequence = fields.Integer(string="Sequence", default=1)

    testing_item_id = fields.Many2one('ps.quality.testing.item', string='Testing Item')

    method_type = fields.Selection([
        ('quantitative', 'Quantitative'),
        ('qualitative', 'Qualitative'),
        ('other', 'Other'),
    ], string='Method Type')

    defect_level = fields.Selection([
        ('fatal', 'Fatal'),
        ('serious', 'Serious'),
        ('light', 'Light'),
    ], string='Defect_level')

    check_level = fields.Many2one("ps.quality.inspection.level", string="Inspection Level")

    @api.model
    def _get_sampling_plan_id_domain(self):
        domain = []
        domain.append(('id', '=', self.id))
        return domain

    sampling_plan_id = fields.Many2one('ps.quality.sampling.plan', string='Sampling Plan',
                                       default=lambda self: self.env.context.get('sampling_plan_id'),
                                       domain=_get_sampling_plan_id_domain
                                       )
    type = fields.Selection([
        ('all', 'All'),
        ('gb', 'GB'),
    ], string='Type', default=lambda self: self.env.context.get('type'))
    strictness = fields.Selection([
        ('normal', 'Normal'),
        ('tightened', 'Tightened'),
        ('reduced', 'Reduced'),
    ], string='Strictness', default=lambda self: self.env.context.get('strictness'))
    aql = fields.Many2one('ps.quality.testing.aql', string='AQL', default=lambda self: self.env.context.get('aql'))

    is_destructive_test = fields.Boolean(string='Destructive Test')
    is_key_inspection = fields.Boolean(string='Key Inspection')

    criteria_id = fields.Many2one('ps.quality.data_dict', string='Criteria',
                                  domain=[('application', 'in', ['quality_criterion', ])])
    basis_id = fields.Many2one('ps.quality.data_dict', string='Basis',
                               domain=[('application', 'in', ['basis', ])])
    testing_method_id = fields.Many2one('ps.quality.data_dict', string='Testing Method',
                                        domain=[('application', 'in', ['testing_method', ])])
    testing_equipment_id = fields.Many2one('ps.quality.data_dict', string='Testing Equipment',
                                           domain=[('application', 'in', ['testing_equipment', ])])
    state = fields.Selection([
        ('qualified', 'Qualified'),
        ('failed', 'Failed '),
    ], string='State', default='failed')

    comparison = fields.Selection([
        ('=', '='),
        ('between', 'between'),
    ], string='Comparison', default='=')

    check_count = fields.Integer('# Quality Checks', compute='_compute_check_count')

    @api.multi
    def _compute_check_count(self):
        for recode in self:
            check_order_id = self.env['ps.quality.check.order'].search([('ps_inspect_plan_id', '=', recode.plan_id.id)])
            recode.check_count = len(check_order_id)


    def action_see_quality_checks(self):
        self.ensure_one()
        action = self.env.ref('quality_control.quality_check_action_main').read()[0]
        action['domain'] = [('ps_inspect_plan_id', '=', self.plan_id.id)]
        return action




    @api.model
    def _get_target_value_qualitative(self):
        testing_mapping_res = self.env['ps.quality.testing.value.mapping'].search(
            [('item_id', '=', self.testing_item_id.id)])
        ids = []
        for testing_mapping_rec in testing_mapping_res:
            rec = self.env['ps.quality.testing.value.possible'].search([('id', '=', testing_mapping_rec.value_id.id)])
            try:
                float(rec.value)
            except:
                ids.append((rec.id))
        return [('id', 'in', ids)]

    target_value_qualitative = fields.Many2many('ps.quality.testing.value.possible', string='Target Value Qualitative',
                                                domain=_get_target_value_qualitative)
    target_value_quantitative = fields.Float(string='Target Value Quantitative', default=1)
    lower_limit = fields.Float(string='Lower Limit')
    upper_limit = fields.Float(string='Upper Limit')
    lower_deviation = fields.Float(string='Lower Deviation', default=1)
    upper_deviation = fields.Float(string='Upper Deviation', default=1)

    own_product_tmpl_id = fields.Integer()
    own_product_id = fields.Integer()

    own_lower_limit = fields.Float()
    own_upper_limit = fields.Float()

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        pass

    def _compute_limit(self, target_value_quantitative, deviation, flag):
        if self.method_type == 'quantitative' and self.comparison in ['=', 'between']:
            if target_value_quantitative < 0:
                pre_num = self.lower_limit + self.lower_deviation
                self.update({'target_value_quantitative': pre_num})
                return {
                    'warning': {'title': "Warning",
                                'message': _("target_value_quantitative can not less than 0")},
                }
            if flag:
                if deviation < 0:
                    pre_num = self.upper_limit - self.target_value_quantitative
                    self.update({'upper_deviation': pre_num})
                    return {
                        'warning': {'title': "Warning",
                                    'message': _("upper_deviation can not less than 0")},
                    }
                limit = target_value_quantitative + deviation
            else:
                if (deviation < 0) or (deviation > target_value_quantitative):
                    pre_num = self.target_value_quantitative - self.lower_limit
                    self.update({'lower_deviation': pre_num})
                    return {
                        'warning': {'title': "Warning",
                                    'message': _(
                                        "lower_deviation can not less than 0 and more than target_value_quantitative")},
                    }
                limit = target_value_quantitative - deviation
            return limit

    @api.onchange('lower_deviation')
    def _compute_lower_limit(self):
        result = self._compute_limit(self.target_value_quantitative, self.lower_deviation, flag=False)
        if isinstance(result, dict):
            return result
        self.lower_limit = result
        self.own_lower_limit = result

    @api.onchange('upper_deviation')
    def _compute_upper_limit(self):
        result = self._compute_limit(self.target_value_quantitative, self.upper_deviation, flag=True)
        if isinstance(result, dict):
            return result
        self.upper_limit = result
        self.own_upper_limit = result

    @api.onchange('testing_item_id')
    def _onchange_testing_item_id(self):
        if self.testing_item_id:
            self.method_type = self.testing_item_id.method_type
            self.defect_level = self.testing_item_id.defect_level
            self.is_destructive_test = self.testing_item_id.is_destructive_test
            self.is_key_inspection = self.testing_item_id.is_key_inspection
            self.criteria_id = self.testing_item_id.criteria_id
            self.basis_id = self.testing_item_id.basis_id
            self.testing_method_id = self.testing_item_id.testing_method_id
            self.testing_equipment_id = self.testing_item_id.testing_equipment_id
            self.sampling_plan_id = self.testing_item_id.sampling_plan_id
            self.check_level = self.testing_item_id.check_level
            self.aql = self.testing_item_id.aql
            self.strictness = self.testing_item_id.strictness
            self.type = self.testing_item_id.type

            domain = self._get_target_value_qualitative()
            return {
                'domain': {'target_value_qualitative': domain},
            }

    @api.onchange('method_type')
    def _onchange_method_type(self):
        # 获取检验项目对应的值
        values = self.env['ps.quality.testing.value.mapping'].search([
            ('item_id', '=', self.testing_item_id.id), ('is_target', '=', True)])
        value = None
        if values:
            value = values[0].value_id.value
        if self.testing_item_id.method_type == 'qualitative':
            value = 1
        # 定量分析时，设置值
        if self.method_type == 'quantitative':
            try:
                self.target_value_quantitative = value
                self.norm = value
            except:
                self.target_value_quantitative = 1
                self.norm = 1
            finally:
                self.lower_deviation = 0
                self.upper_deviation = 0

            self.target_value_qualitative = None

            self.test_type_id = self.env['quality.point.test_type'].search([('name', '=', 'Measure')]).id

            self.tolerance_min = self.lower_limit
            self.tolerance_max = self.upper_limit
        # 非定量分析时，设置值
        if self.method_type in ['qualitative', 'other']:
            self.target_value_quantitative = None
            self.target_value_qualitative = None
            self.lower_limit = None
            self.upper_limit = None
            self.lower_deviation = None
            self.upper_deviation = None

            self.test_type_id = self.env['quality.point.test_type'].search([('name', '=', 'Pass - Fail')]).id
            self.norm = None
            self.norm_unit = None
            self.tolerance_min = None
            self.tolerance_max = None

    @api.onchange('target_value_quantitative')
    def _onchange_target_value_quantitative(self):
        # for res in self:
        result = self._compute_limit(self.target_value_quantitative, self.lower_deviation, flag=False)
        if isinstance(result, dict):
            return result
        self.lower_limit = result
        self.own_lower_limit = result

        result = self._compute_limit(self.target_value_quantitative, self.upper_deviation, flag=True)
        if isinstance(result, dict):
            return result
        self.upper_limit = result
        self.own_upper_limit = result

        self.norm = self.target_value_quantitative

    @api.onchange('lower_limit')
    def _onchange_lower_limit(self):
        self.tolerance_min = self.lower_limit

    @api.onchange('upper_limit')
    def _onchange_upper_limit(self):
        self.tolerance_max = self.upper_limit

    @api.model
    def default_get(self, fields):
        """
        compute the sequence field
        :param fields:
        :return:
        """
        default_values = super(QualityControlPoint, self).default_get(fields)
        item_ids = self.env.context.get('item_ids')
        sequence_list = []
        if self.plan_id.sequence_list:
            sequence_list = self.plan_id.sequence_list
        else:
            if item_ids:
                for item_id in item_ids:
                    if isinstance(item_id[1], int):
                        sequence = self.env['quality.point'].search(
                            [('id', '=', item_id[1])]).sequence
                        sequence_list.append(sequence)
                    else:
                        sequence = item_id[2]['sequence']
                        sequence_list.append(sequence)
        if sequence_list:
            max_sequence = max(sequence_list)
            max_sequence_list = list(range(1, max_sequence + 1))
            sublist = list(set(max_sequence_list) - set(sequence_list))
            if sublist:
                number = min(sublist)
            else:
                number = max_sequence + 1

            default_values.update({
                'sequence': number,
            })
        return default_values

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'all':
            self.strictness = None
            self.aql = None
        self.sampling_plan_id = self.env['ps.quality.sampling.plan'].search(
            [('type', '=', self.type), ('strictness', '=', self.strictness), ('aql', '=', self.aql.id)]).id

    @api.onchange('strictness')
    def onchange_strictness(self):
        self.sampling_plan_id = self.env['ps.quality.sampling.plan'].search(
            [('type', '=', self.type), ('strictness', '=', self.strictness), ('aql', '=', self.aql.id)]).id

    @api.onchange('aql')
    def onchange_aql(self):
        self.sampling_plan_id = self.env['ps.quality.sampling.plan'].search(
            [('type', '=', self.type), ('strictness', '=', self.strictness), ('aql', '=', self.aql.id)]).id

    @api.multi
    def write(self, vals):
        if vals.get('type') == 'all':
            vals['strictness'] = None
            vals['aql'] = None
        return super(QualityControlPoint, self).write(vals)
