# -*- coding: utf-8 -*-

from odoo import models, fields, api

class soft(models.Model):
    _name = 'jyinspur.soft'

    name = fields.Char()
    ggxh = fields.Char()
    price = fields.Float()
    #price = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()
    jldw = fields.Many2one('uom.uom',string='单位')

    #@api.depends('value')
    #def _value_pc(self):
        #self.value2 = float(self.value) / 100