# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualitySamplingName(models.Model):
    _name = "ps.quality.sampling.name"
    _description = "Quality Sampling Name"

    name = fields.Char(string="Name")
    code_ids = fields.One2many('ps.quality.sampling.code', 'sampling_id', string="Sampling Code")
    is_set = fields.Boolean(string="Set")

    def unlink(self):
        for self in self:
            if self.is_set:
                raise UserError(_("this recode is setup data,so you can not delete!"))


class QualitySamplingCode(models.Model):
    _name = "ps.quality.sampling.code"
    _description = "Quality Sampling Code"

    sampling_id = fields.Many2one('ps.quality.sampling.name', string="Sampling Code")
    size_scope = fields.Char(string="Size Scope", compute="_compute_size_scope", store=True)
    size_begin = fields.Integer(string="Size Begin")
    size_end = fields.Integer(string="Size End")
    inspection_level = fields.Many2one("ps.quality.inspection.level", string="Inspection Level")
    inspection_level_name = fields.Char(string="Inspection Level Name", related="inspection_level.name", store=True)
    inspection_level_category = fields.Selection([('special', 'Special'),
                                                  ('normal', 'Normal')], string='Category',
                                                 related="inspection_level.category", store=True)

    code = fields.Char(string="Code", size=1)

    @api.depends("size_begin", "size_end")
    def _compute_size_scope(self):
        for record in self:
            if record.size_begin > 0 and record.size_end != 0:
                record.size_scope = "%s-%s" % (record.size_begin, record.size_end)
            elif record.size_end == 0:
                record.size_scope = ">=%s" % (record.size_begin)

    @api.onchange("code")
    def onchange_code(self):
        if self.code:
            if not 'A' <= self.code <= 'Z':
                self.code = None
                raise UserError(_("please input the values between A and Z "))
