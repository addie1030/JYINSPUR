# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import datetime


class QualityInspectionPlan(models.Model):
    _name = 'ps.quality.inspection.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quality Inspection Plan'
    _rec_name = "code"

    code = fields.Char(string='Code', default=lambda self: _('New'), copy=False)
    name = fields.Char(string='Name')

    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    product_variant_id = fields.Many2one('product.product', 'Product Variant',
                                         domain="[('product_tmpl_id', '=', product_tmpl_id)]")

    product_readonly_state = fields.Selection([
        ('readonly', 'readonly'),
        ('un_readonly', 'un_readonly '),
    ], default='un_readonly')

    type = fields.Selection([
        ('all', 'All'),
        ('gb', 'GB'),
    ], string='Type')
    strictness = fields.Selection([
        ('normal', 'Normal'),
        ('tightened', 'Tightened'),
        ('reduced', 'Reduced'),
    ], string='Strictness')
    aql = fields.Many2one('ps.quality.testing.aql', string='AQL')
    sampling_plan_id = fields.Many2one('ps.quality.sampling.plan', string='Sampling Plan')

    validate_from = fields.Date(string='Validate From', copy=True)
    validate_to = fields.Date(string='Validate To', copy=True)
    description = fields.Char(string='Description')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='State', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    picking_type_id = fields.Many2one('stock.picking.type', "Operation Type")

    inspection_plan_testing_item_ids = fields.One2many('quality.point', 'plan_id')
    sequence_list = []

    @api.multi
    def unlink(self):
        for line in self:
            if line.state not in ('draft',):
                raise UserError(
                    _(
                        "You can't delete a non-draft status quality inspection plan, please set it to draft status first!"))
        return super(QualityInspectionPlan, self).unlink()

    @api.multi
    def draft(self):
        self.state = 'draft'

    @api.multi
    def confirmed(self):
        res = self.env['ps.quality.inspection.plan'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('product_variant_id', '=', self.product_variant_id.id),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('state', '=', 'confirmed'),
        ])
        if res:
            for rec in res:
                if rec.validate_to >= self.validate_from:
                    if rec.validate_from > self.validate_to:
                        continue
                    raise ValidationError(
                        _('This product_tmpl or product has duplicate time in confirmed state and picking_type_id'))

        self.state = 'confirmed'

    @api.multi
    def cancelled(self):
        self.state = 'cancelled'

    @api.multi
    def closed(self):
        self.state = 'closed'

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

        res = super(QualityInspectionPlan, self).write(vals)
        for line in self.inspection_plan_testing_item_ids:
            line.product_tmpl_id = self.product_tmpl_id
            line.product_id = self.product_variant_id
            line.lower_limit = line.own_lower_limit
            line.upper_limit = line.own_upper_limit
        return res

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('ps.quality.inspection.plan') or '/'
        res = super(QualityInspectionPlan, self).create(vals)
        for line in res.inspection_plan_testing_item_ids:
            line.product_tmpl_id = res.product_tmpl_id
            line.product_id = res.product_variant_id
            line.lower_limit = line.own_lower_limit
            line.upper_limit = line.own_upper_limit
        return res

    @api.onchange('inspection_plan_testing_item_ids')
    def onchange_item_ids(self):
        """
        compute sequence_list
        :return:
        """
        self.sequence_list.clear()
        res = self.inspection_plan_testing_item_ids
        for rec in res:
            self.sequence_list.append(rec.sequence)

    @api.constrains('validate_from', 'validate_to')
    def onchange_validate(self):
        start_time = datetime.datetime.strptime(str(self.validate_from), "%Y-%m-%d")
        end_time = datetime.datetime.strptime(str(self.validate_to), "%Y-%m-%d")
        if start_time > end_time:
            raise ValidationError(_("validate_to is greater than the validate_from !"))



