# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError, ValidationError
import datetime


class CreditScheme(models.Model):
    _name = 'ps.credit.check.scheme'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='name', required=True)
    description = fields.Char(string='description', required=True)
    is_default = fields.Boolean(string='is_default', default=False, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='state', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3,
        default='draft')
    validate_by = fields.Many2one('res.users', string='validate by', copy=False)
    validate_date = fields.Date(string='validate date', copy=False)

    check_rule_ids = fields.One2many('ps.credit.check.rule', 'scheme_id')

    def copy_data(self, default=None):
        """
        重写复制方法
        :param default:
        :return:
        """
        name = _("%s (copy)") % (self.name)
        check_rule_ids_copy = []
        for check_rule_id in self.check_rule_ids:
            val = (0, 0, {
                'document': check_rule_id.document,
                'control_strength': check_rule_id.control_strength,
                'check_credit_limit': check_rule_id.check_credit_limit,
                'check_credit_ratio': check_rule_id.check_credit_ratio,
                'check_overdue_days': check_rule_id.check_overdue_days,
                'check_overdue_amount': check_rule_id.check_overdue_amount,
                'check_overdue_ratio': check_rule_id.check_overdue_ratio,
                'excessive_condition': check_rule_id.excessive_condition,
            })
            check_rule_ids_copy.append(val)

        default = dict(default or {}, name=name, check_rule_ids=check_rule_ids_copy)
        return super(CreditScheme, self).copy_data(default)

    @api.constrains('name', 'is_default')
    def _check_name_and_is_default(self):
        """
        检查名称和是否默认的唯一性
        :return:
        """
        for record in self:
            rec = self.env['ps.credit.check.scheme'].search([('name', '=', record.name)])
            if len(rec) > 1:
                raise ValidationError(
                    _("Name must be unique !"))

        record = self.env['ps.credit.check.scheme'].search([('is_default', '=', True)])
        if len(record) > 1:
            raise ValidationError(
                _("is_default must be unique !"))

    @api.multi
    def unlink(self):
        for line in self:
            if line.state not in ('draft',):
                raise UserError(
                    _("You can't delete a non-draft status credit check scheme, please set it to draft status first!"))
        return super(CreditScheme, self).unlink()

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
    def approved(self):
        self.validate_date = datetime.date.today()
        self.validate_by = self.env.user.id
        self.state = 'approved'

    @api.multi
    def closed(self):
        rec = None
        for record in self:
            record.is_default = False
            rec = self.env['ps.credit.profile'].search(
                [('check_scheme_id', '=', record.id)])
        if rec:
            raise UserError(_("This check scheme has been applied to the profile and cannot be closed"))
        else:
            self.state = 'closed'


class CreditRule(models.Model):
    _name = 'ps.credit.check.rule'

    document = fields.Selection([
        ('sales_order', 'Sales Order'),
        ('stock_picking', 'Stock Picking'),
        ('stock_out', 'Stock Out')
    ], string='document', required=True)

    control_strength = fields.Selection([
        ('stop', 'Stop'),
        ('warning', 'Warning'),
        ('password', 'Password'),
        ('freeze', 'Freeze'),
    ], default='warning', string='control strength', required=True)

    check_credit_limit = fields.Boolean(string='check credit limit', default=True)
    check_credit_ratio = fields.Boolean(string='check credit ratio', default=False)
    check_overdue_days = fields.Boolean(string='check overdue days', default=False)
    check_overdue_amount = fields.Boolean(string='check overdue amount', default=False)
    check_overdue_ratio = fields.Boolean(string='check overdue ratio', default=False)
    excessive_condition = fields.Selection([
        ('single', 'Single Term'),
        ('multi', 'Multi Term'),
    ], string='excessive condition', default='single')

    scheme_id = fields.Many2one('ps.credit.check.scheme')

    @api.constrains('document')
    def _check_document(self):
        """
        检查单据唯一性
        :return:
        """
        for record in self:
            rec = self.env['ps.credit.check.rule'].search(
                [('scheme_id', '=', record.scheme_id.id), ('document', '=', record.document)])
            if len(rec) > 1:
                raise ValidationError(
                    _("document must be unique !"))
