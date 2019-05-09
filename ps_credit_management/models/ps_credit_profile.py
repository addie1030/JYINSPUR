# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CreditProfile(models.Model):
    _name = 'ps.credit.profile'
    _description = 'ps credit profile'
    _rec_name = "partner_id"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    partner_id = fields.Many2one('res.partner', string='Customer')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    level_id = fields.Many2one('ps.credit.level', string='Level')
    state = fields.Selection([('draft', "Draft"),
                              ('confirmed', "Confirmed"),
                              ('closed', "Closed")], string='Status', default='draft', track_visibility='onchange')
    check_scheme_id = fields.Many2one('ps.credit.check.scheme', string='Check Scheme',
                                      default=lambda self: self.env['ps.credit.check.scheme'].search(
                                          [('is_default', '=', True), ('state', '=', 'approved')]))
    credit_limit = fields.Float(string='Credit Limit')
    ratio = fields.Float(string='Ratio')
    order_limit = fields.Float(string='Order Limit')
    overdue_days = fields.Integer(default=0, string='Overdue Days')
    overdue_limit = fields.Float(string='Overdue Limit')
    overdue_ratio = fields.Float(string='Overdue Ratio')
    date_start = fields.Date(string='Date Start', default=fields.Date.today)
    date_end = fields.Date(string='Date End', compute='_compute_date_end', store=True)
    cycle_days = fields.Integer(string='Cycle Days')

    @api.constrains('credit_limit')
    def constrains_credit_limit(self):
        if self.credit_limit < 0:
            raise ValidationError(_('The credit limit can not less than zero.'))

    @api.constrains('ratio')
    def constrains_ratio(self):
        if self.ratio < 0:
            raise ValidationError(_('The ratio can not less than zero.'))

    @api.constrains('order_limit')
    def constrains_order_limit(self):
        if self.order_limit < 0:
            raise ValidationError(_('The order limit can not less than zero.'))

    @api.constrains('overdue_days')
    def constrains_overdue_days(self):
        if self.overdue_days < 0:
            raise ValidationError(_('The overdue days can not less than zero.'))

    @api.constrains('overdue_limit')
    def constrains_overdue_limit(self):
        if self.overdue_limit < 0:
            raise ValidationError(_('The overdue limit can not less than zero.'))

    @api.constrains('overdue_ratio')
    def constrains_overdue_ratio(self):
        if self.overdue_ratio < 0:
            raise ValidationError(_('The overdue ratio can not less than zero.'))

    @api.constrains('cycle_days')
    def constrains_cycle_days(self):
        if self.cycle_days < 0:
            raise ValidationError(_('The cycle days can not less than zero.'))

    @api.multi
    def action_approve(self):
        # Insert profile-data into ps_credit_usage
        if not self.env['ps.credit.usage'].search([('partner_id', '=', self.partner_id.id)]):
            self.env['ps.credit.usage'].create({
                'company_id': self.company_id.id,
                'partner_id': self.partner_id.id,
            })
        # Determine if the customer file has a duplicate time
        records = self.env['ps.credit.profile'].search(
            [('company_id', '=', self.company_id.id), ('partner_id', '=', self.partner_id.id),
             ('state', '=', 'confirmed')])
        if records:
            for record in records:
                if record.date_end >= self.date_start:
                    if record.date_start > self.date_end:
                        continue
                    raise UserError(_('The partner information has duplicate time.'))
        return self.write({'state': 'confirmed'})

    def action_close(self):
        return self.write({'state': 'closed'})

    @api.depends('date_start', 'cycle_days')
    def _compute_date_end(self):
        # Compute date_end
        for line in self:
            line.date_end = line.date_start + timedelta(days=line.cycle_days)

    @api.onchange('date_start')
    def assert_date_start(self):
        # Determines if the date was set incorrectly
        if self.date_start < fields.Date.today():
            raise UserError(_("The effective date cannot be before the current period."))

    def unlink(self):
        # Non-draft status cannot be deleted
        for profile in self:
            if profile.state != 'draft':
                raise UserError(_("Don't delete this record."))
        return super(CreditProfile, self).unlink()


class CreditLevel(models.Model):
    _name = 'ps.credit.level'
    _description = 'ps credit level'

    name = fields.Char(string="Name")
    description = fields.Char(string="Description", translate=True)
