# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class QualityCheckData(models.Model):
    _name = "ps.quality.check.data"
    _description = "ps quality check data"

    @api.model
    def _get_target_value_qualitative(self):
        res = self.env['ps.quality.testing.value.possible'].search([('id', '>', '0')])
        ids = []
        for rec in res:
            try:
                float(rec.value)
            except:
                ids.append((rec.id))
        return [('id', 'in', ids)]

    target_value = fields.Float(string='Target Value')
    target_value_qualitative = fields.Many2many('ps.quality.testing.value.possible', string='Target Value Qualitative')
    value_type = fields.Selection(string='Value Type', selection=[('quantitative', 'Quantitative'),
                                                                  ('qualitative', 'Qualitative'),
                                                                  ('other', 'Other'),
                                                                  ], )
    standard_value = fields.Float(string='Standard Value')
    lower_limit = fields.Float(string='Lower Limit')
    upper_limit = fields.Float(string='Upper Limit')
    value_measured = fields.Float(string='Value Measured')
    qty_qualitative = fields.Many2one('ps.quality.testing.value.possible', string='Value Measured Qualitative', domain=_get_target_value_qualitative)
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    check_id = fields.Many2one('quality.check', string='Check')

    @api.model
    def default_get(self, fields):
        default_values = super(QualityCheckData, self).default_get(fields)
        testing_item_id = self.env.context.get('testing_item_id')
        ps_inspection_plan_id = self.env.context.get('ps_inspection_plan_id')
        plan = self.env['quality.point'].search(
            [('testing_item_id', '=', testing_item_id), ('plan_id', '=', ps_inspection_plan_id)])
        values ={
            'target_value': plan.target_value_quantitative,
            'target_value_qualitative': list(plan.target_value_qualitative.ids),
            'value_type': plan.method_type,
            'lower_limit': plan.lower_limit,
            'upper_limit': plan.upper_limit
        }
        default_values.update(values)
        return default_values
