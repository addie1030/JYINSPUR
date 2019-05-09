# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError


class QualitySamplingPlan(models.Model):
    _name = "ps.quality.sampling.plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quality Sampling Plan'

    code = fields.Char(string='Code', default=lambda self: _('New'), copy=False)
    name = fields.Char(string='Name', copy=False)

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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='State', copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')

    line_ids = fields.One2many('ps.quality.sampling.plan.line', 'plan_id', copy=True)
    sequence_list = []

    @api.multi
    def draft(self):
        self.state = 'draft'

    @api.multi
    def confirmed(self):
        self.state = 'confirmed'

    @api.multi
    def cancelled(self):
        self.state = 'cancelled'

    @api.multi
    def closed(self):
        self.state = 'closed'

    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('ps.quality.sampling.plan') or '/'
        return super(QualitySamplingPlan, self).create(vals)

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        """
        compute sequence_list
        :return:
        """
        self.sequence_list.clear()
        res = self.line_ids
        for rec in res:
            self.sequence_list.append(rec.sequence)

    @api.constrains('name')
    def _check_name(self):
        """
        检查名称的唯一性
        :return:
        """
        for record in self:
            rec = self.env['ps.quality.sampling.plan'].search([('name', '=', record.name)])
            if len(rec) > 1:
                raise ValidationError(
                    _("Name must be unique !"))

    def copy_data(self, default=None):
        """
        重写复制方法
        :param default:
        :return:
        """
        name = _("%s (copy)") % (self.name)
        default = dict(default or {}, name=name)
        return super(QualitySamplingPlan, self).copy_data(default)

    @api.multi
    @api.depends('name', 'strictness', 'aql')
    def name_get(self):
        result = []
        for record in self:
            if record.name and record.aql:
                name = record.strictness + ' - ' + record.name + ' - ' + str(record.aql.value)
            else:
                name = record.name
            result.append((record.id, name))
        return result


class QualitySamplingPlanLine(models.Model):
    _name = "ps.quality.sampling.plan.line"
    _description = 'Quality Sampling Plan Line'

    plan_id = fields.Many2one('ps.quality.sampling.plan')

    sequence = fields.Integer(string="Sequence", default=1)

    # batch_size = fields.Integer(string="Batch Size", )
    sample_size_code = fields.Char(string='Sample Size Code')
    sample_size = fields.Integer(string='Sample Size')
    quantity_accept = fields.Integer(string='Quantity Accept')
    quantity_reject = fields.Integer(string='Quantity Reject')

    @api.model
    def default_get(self, fields):
        """
        compute the sequence field
        :param fields:
        :return:
        """
        default_values = super(QualitySamplingPlanLine, self).default_get(fields)
        line_ids = self.env.context.get('line_ids')
        sequence_list = []
        if self.plan_id.sequence_list:
            sequence_list = self.plan_id.sequence_list
        else:
            if line_ids:
                for line_id in line_ids:
                    if isinstance(line_id[1], int):
                        sequence = self.env['ps.quality.sampling.plan.line'].search(
                            [('id', '=', line_id[1])]).sequence
                        sequence_list.append(sequence)
                    else:
                        sequence = line_id[2]['sequence']
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
