# -*- coding: utf-8 -*-
from odoo import models, fields, _


class QualityTestingAql(models.Model):
    _name = 'ps.quality.testing.aql'
    _description = 'Quality Testing Aql'
    _rec_name = 'key'

    name = fields.Char(string='Name', translate=True)
    key = fields.Char(string='AQL Key')
    value = fields.Float(string='AQL Value')
