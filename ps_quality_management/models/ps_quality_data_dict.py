# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PsQualityDataDict(models.Model):
    _name = 'ps.quality.data_dict'
    _description = 'ps.quality.data_dict'

    name = fields.Char(string='Name', required=True)
    description = fields.Char(string='Description', translate="True")
    application = fields.Selection([
        ('quality_criterion', 'Quality Criterion'),
        ('testing_method', 'Testing Method'),
        ('testing_equipment', 'Testing Equipment'),
        ('basis', 'Basis'),
        ('defect_type', 'Defect Type'),
        ('defect_cause', 'Defect Cause'),
        ('defect_consequence', 'Defect Consequence'),
    ], required=True, application="Application")

    @api.model
    def create(self, vals):
        if not vals['application']:
            vals['application'] = self._context.get('application')
        return super(PsQualityDataDict, self).create(vals)
