# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class QualityInspectionLevel(models.Model):
    _name = 'ps.quality.inspection.level'
    _description = 'Quality Inspection Level'

    name = fields.Char(string='Name', compute='_spell_name')
    code = fields.Selection([('S-1', "S-1"),
                             ('S-2', "S-2"),
                             ('S-3', "S-3"),
                             ('S-4', "S-4"),
                             ('Ⅰ', "Ⅰ"),
                             ('Ⅱ', "Ⅱ"),
                             ('Ⅲ', "Ⅲ")], string='Code')
    category = fields.Selection([('special', 'Special'),
                                 ('normal', ' Normal ')], string='Category')

    @api.depends('code', 'category')
    def _spell_name(self):
        # Automatically spell out name from code and category
        for record in self:
            if record.code and record.category:
                record.name = record.category + ' ' + record.code
            if not record.code:
                record.name = record.category
            if not record.category:
                record.name = record.code
