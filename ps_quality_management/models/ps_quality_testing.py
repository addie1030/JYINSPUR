# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class QualityTestingItem(models.Model):
    _name = 'ps.quality.testing.item'
    _description = 'Quality Testing'

    code = fields.Char(string='Code', default=lambda self: _('New'))
    name = fields.Char(string='Name')

    method_type = fields.Selection([
        ('quantitative', 'Quantitative'),
        ('qualitative', 'Qualitative'),
        ('other', 'Other'),
    ], string='Method_type')

    defect_level = fields.Selection([
        ('fatal', 'Fatal'),
        ('serious', 'Serious'),
        ('light', 'Light'),
    ], string='Defect_level')

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

    type = fields.Selection([
        ('all', 'All'),
        ('gb', 'GB'),
    ], string='Type')

    check_level = fields.Many2one("ps.quality.inspection.level", string="Inspection Level")
    strictness = fields.Selection([
        ('normal', 'Normal'),
        ('tightened', 'Tightened'),
        ('reduced', 'Reduced'),
    ], string='Strictness')
    aql = fields.Many2one('ps.quality.testing.aql', string='AQL')
    sampling_plan_id = fields.Many2one('ps.quality.sampling.plan', string='Sampling Plan')

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('ps.quality.testing.item') or '/'
        return super(QualityTestingItem, self).create(vals)

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'all':
            self.strictness = None
            self.aql = None
            self.check_level = None
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
        if vals.get('type')== 'all':
            vals['strictness'] = None
            vals['aql'] = None
            vals['check_level'] = None
        return super(QualityTestingItem, self).write(vals)


class QualityTestingValuePossible(models.Model):
    _name = 'ps.quality.testing.value.possible'
    _description = 'Quality Testing Value Possible'
    _rec_name = 'value'

    value = fields.Char(string='Value',size=6)
    description = fields.Char(string='Description')


class QualityTestingValueMapping(models.Model):
    _name = 'ps.quality.testing.value.mapping'
    _description = 'Quality Testing Value Mapping'

    _sql_constraints = [
        ('item_id_value_id_unique', 'UNIQUE(item_id,value_id)', 'An item_id cannot have twice the same value_id.')
    ]

    item_id = fields.Many2one('ps.quality.testing.item', string='Item', ondelete='cascade')
    value_id = fields.Many2one('ps.quality.testing.value.possible', string='Value', ondelete='cascade')
    is_target = fields.Boolean(string='Is Target Value')

    @api.constrains('value_id')
    def _check_value(self):
        """
        检查 值
        :return:
        """
        if self.item_id.method_type == 'quantitative':
            try:
                float(self.value_id.value)
            except:
                raise ValidationError(
                    _("This testing item method_type is quantitative, please choose number type value !"))

        if self.item_id.method_type in ['qualitative', 'other']:
            try:
                float(self.value_id.value)
            except:
                pass
            else:
                raise ValidationError(
                    _("This testing item method_type is not quantitative, please choose not number type value !"))
