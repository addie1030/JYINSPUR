# -*- coding: utf-8 -*-
import datetime

import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
import time


class PsHrExpenseRequest(models.Model):
    _name = 'ps.hr.expense.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_employee(self):
        if not self.env.user.employee_ids:
            raise ValidationError(_('Current users have no associated employees.'))
        return self.env.user.employee_ids[0]

    name = fields.Char(string='Name', copy=False, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee Id', required=True,
                                  default=_get_default_employee,
                                  states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],
                                          'refused': [('readonly', True)], 'cancelled': [('readonly', True)],
                                          'closed': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', string='Department Id', compute='_set_department_id', store=True,
                                    states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],
                                            'refused': [('readonly', True)], 'cancelled': [('readonly', True)],
                                            'closed': [('readonly', True)]})
    reason = fields.Text(string='Reason')
    is_loan = fields.Boolean(string='Is Loan',
                             states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],
                                     'refused': [('readonly', True)], 'cancelled': [('readonly', True)],
                                     'closed': [('readonly', True)]})
    amount_loan = fields.Float(string='Amount Loan',
                               states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],
                                       'refused': [('readonly', True)], 'cancelled': [('readonly', True)],
                                       'closed': [('readonly', True)]})
    date_return = fields.Date(string='Date',
                              states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)],
                                      'refused': [('readonly', True)], 'cancelled': [('readonly', True)],
                                      'closed': [('readonly', True)]})
    amount_request = fields.Float(string='Amount Request', readonly=True, compute='get_amount')
    amount_approved = fields.Float(string='Amount Approved', readonly=True, compute='get_amount')
    amount_actual = fields.Float(string='Amount Actual', readonly=True)
    amount_reimburse = fields.Float(string='Amount Reimburse', readonly=True)
    need_repayment = fields.Boolean(string='Need Repayment', default=False)
    report_id = fields.Many2one('hr.expense.sheet', string='Report Id')
    payment_ids = fields.Many2many('account.payment', string='Payment Ids')
    state = fields.Selection(
        [('draft', 'draft'), ('confirmed', 'confirmed'), ('approved', 'approved'), ('refused', 'refused'),
         ('cancelled', 'cancelled'), ('closed', 'closed')],
        default='draft', string='State', track_visibility='onchange')
    line_ids = fields.One2many('ps.hr.expense.request.line', 'expense_request_id', string='Line Ids')
    amount_return_theoretical = fields.Float(string="Theoretical refund amount")
    amount_return_actual = fields.Float(string="Actual refund amount")
    sheet_id = fields.Many2one('hr.expense.sheet', string='Sheet Id')

    @api.constrains('is_loan', 'amount_loan', 'date_return')
    def _check_amount_loan(self):
        if self.is_loan and self.amount_loan <= 0:
            raise ValidationError(_('The "Amount Loan" must be greater than 0 ！'))
        if self.is_loan:
            if self.date_return < datetime.date.today():
                raise ValidationError(_('The "Date Return" cannot be earlier than the current time ！'))

    @api.multi
    def open_refund_form(self):
        for rec in self:
            amount_return_actual = self.env['ps.hr.expense.request'].browse(self.id).amount_return_actual
            amount_return_theoretical = rec.amount_return_theoretical - amount_return_actual
            for payment in rec.payment_ids:
                if payment.ps_is_repayment and payment.state == "draft":
                    raise ValidationError(_('There is an unconfirmed loan payment form and no refund is allowed.'))
        return {
            'type': 'ir.actions.act_window',
            'name': '退款申请',
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'expense_request_id': self.id,
                        'default_amount_return_theoretical': amount_return_theoretical,
                        'default_amount_return_actual': amount_return_theoretical},
            'target': 'new',
            'res_model': 'ps.returned.amount',
        }

    @api.multi
    def compute_amount_theoretical(self):
        for res in self:
            account_payments = self.env['account.payment'].search([('ps_expense_request_id', '=', res.id)])
            for account_payment in account_payments:
                if account_payment.amount > res.amount_reimburse:
                    need_repayment = True
                    amount_return_theoretical = account_payment.amount - res.amount_reimburse
                    res.write({
                        'need_repayment': need_repayment,
                        'amount_return_theoretical': amount_return_theoretical,
                    })

    @api.multi
    def unlink(self):
        for r in self:
            if r.state in ('confirmed', 'approved', 'closed'):
                raise ValidationError(_('This list is in ') + r.state + _(' and cannot be deleted.'))
            return super(PsHrExpenseRequest, self).unlink()

    @api.depends('employee_id')
    def _set_department_id(self):
        self.ensure_one()
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.depends('line_ids')
    def get_amount(self):
        for r in self:
            if r.line_ids:
                amount_request = 0.0
                amount_approved = 0.0
                for rec in r.line_ids:
                    amount_request += rec.amount_request
                    amount_approved += rec.amount_approved
                r.amount_request = amount_request
                r.amount_approved = amount_approved

    def _get_users_to_subscribe(self, employee=False):
        users = self.env['res.users']
        employee = employee or self.employee_id
        if employee.user_id:
            users |= employee.user_id
        if employee.parent_id:
            users |= employee.parent_id.user_id
        if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
            users |= employee.department_id.manager_id.user_id
        return users

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('ps.hr.expense.request') or _('New')
        return super(PsHrExpenseRequest, self).create(vals)

    @api.multi
    def action_approve(self):
        for line in self:
            #   1、设置状态
            if line.state == 'confirmed':
                line.write({'state': 'approved'})
                # 更新明细state,用于读写控制
                for r in line.line_ids:
                    r.state = 'approved'
            else:
                raise ValidationError(
                    _('Only "confirmed" state are allowed to be operate'))
            #   2019年1月14日迭代8：费用申请需求变更-old-begin；
            #   2、生成报销单、费用报告；
            # expense_sheet_line = []
            # if line.line_ids:
            #     for r in line.line_ids:
            #         expense_sheet_line.append(
            #             (0, 0, {'name': r.name.name, 'product_id': r.name.id, 'unit_amount': r.price_approved,
            #                     'quantity': r.qty_approved,
            #                     'employee_id': r.expense_request_id.employee_id.id}))
            # report = self.env['hr.expense.sheet'].create({
            #     'name': line.reason,
            #     'employee_id': line.employee_id.id,
            #     'expense_line_ids': expense_sheet_line,
            # })
            # #   3、费用申请与费用报告关联
            # self.env['ps.hr.expense.request'].browse(line.id).write({'sheet_id': report.id})
            #   2019年1月14日迭代8：费用申请需求变更-old-end；
            #   2019年1月14日迭代8：费用申请需求变更-new-begin；
            if line.line_ids:
                for r in line.line_ids:
                    self.env['hr.expense'].create(
                        {'name': r.name.name,
                          'product_id': r.name.id,
                          'unit_amount': r.price_approved,
                          'quantity': r.qty_approved,
                          'employee_id': r.expense_request_id.employee_id.id,
                          'request_id':line.id})

            #   2019年1月14日迭代8：费用申请需求变更-new-end；

            # 定义获取现金账户
            journal_id = self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id

            if journal_id == False:
                raise ValidationError(
                    _('Unmaintained accounting journal'))
            else:
                # 4、如勾选了is_loan字段，则生成借款付款单
                if line.is_loan == True:
                    self.with_context({'expense_request_payment': line.id})
                    new_payment = self.env['account.payment'].create({
                        'payment_use': self.env.ref('ps_account.payment_use_preset_expense_loan').id,
                        'payment_type': 'outbound',
                        'partner_type': 'supplier',
                        'partner_id': line.employee_id.sudo().address_home_id.id,
                        'amount': line.amount_loan,
                        'payment_method_id': 1,
                        'communication': _('Application Payment'),
                        'journal_id': journal_id,
                        'ps_is_loan': True,
                        'ps_expense_request_id': line.id
                    })
                    line.update({'payment_ids': new_payment})

    @api.multi
    def action_submit(self):
        for line in self:
            if line.state == 'draft':
                line.write({'state': 'confirmed'})
                # 更新明细state,用于读写控制
                for r in line.line_ids:
                    r.state = 'confirmed'
                    r.price_approved = r.price
                    r.qty_approved = r.qty
                note = _("The list of ") + self.employee_id.name + _("been submitted, please review them.")
                from datetime import datetime, timedelta
                now = datetime.now()
                if self.employee_id.parent_id.user_id:
                    self.activity_schedule(
                        'hr_expense.mail_act_expense_approval',
                        user_id=self.employee_id.parent_id.user_id.id,
                        date_deadline=(now + timedelta(days=3)).date(),
                        note=note
                    )
                else:
                    raise ValidationError(
                        _('Involving users without associated employees!'))
            else:
                raise ValidationError(
                    _('Only expense request at "draft" state can be confirm'))

    @api.multi
    def action_cancel(self):
        for line in self:
            if line.state == 'draft' or line.state == 'confirmed':
                line.write({'state': 'cancelled'})
                # 更新明细state,用于读写控制
                for r in line.line_ids:
                    r.state = 'cancelled'
            else:
                raise ValidationError(
                    _('Only expense request at "draft" state can be cancel'))

    @api.multi
    def action_draft(self):
        for line in self:
            if line.state == 'cancelled':
                line.write({'state': 'draft'})
            else:
                raise ValidationError(
                    _('Only expense request at "cancelled" state can be draft'))

    @api.multi
    def action_refuse(self):
        for line in self:
            if line.state == 'confirmed':
                line.write({'state': 'draft'})
                # 更新明细state,用于读写控制
                for r in line.line_ids:
                    r.state = 'draft'
            else:
                raise ValidationError(
                    _('Only expense request at "confirmed" state can be draft'))


class PsHrExpenseRequestLine(models.Model):
    _name = 'ps.hr.expense.request.line'

    expense_request_id = fields.Many2one('ps.hr.expense.request', string='Expense Request')
    name = fields.Many2one('product.product', string='Name', domain=[('can_be_expensed', '=', True)])
    description = fields.Text(string='Text')
    place = fields.Char(string='Place')
    price = fields.Float(string='Price')
    qty = fields.Float(string='Qty')
    price_approved = fields.Float(string='Price Approved')
    qty_approved = fields.Float(string='Qty Approved')
    amount_request = fields.Float(string='Amount Request', readonly=True, compute='get_amount_request', store=True)
    amount_approved = fields.Float(string='Amount Approved', readonly=True, compute='get_amount_approved', store=True)
    state = fields.Selection(
        [('draft', 'draft'), ('confirmed', 'confirmed'), ('approved', 'approved'), ('refused', 'refused'),
         ('cancelled', 'cancelled'), ('closed', 'closed')], default='draft', string='State')

    @api.onchange('name')
    def onchange_name(self):
        for rec in self:
            rec.price = self.env['product.product'].browse(rec.name.id).list_price

    @api.constrains('name', 'description')
    def _check_name_description(self):
        for line in self:
            if not line.description or not line.name:
                raise ValidationError(_('The Name or Descrition cannot be None ！'))

    @api.constrains('price', 'qty')
    def _check_price_qty(self):
        for line in self:
            if line.price <= 0 or line.qty <= 0:
                raise ValidationError(_('The Price or Qty must be greater than 0 ！'))

    @api.depends('price', 'qty')
    def get_amount_request(self):
        for record in self:
            amount_request = record.price * record.qty
            record.amount_request = amount_request

    @api.depends('price_approved', 'qty_approved')
    def get_amount_approved(self):
        for record in self:
            amount_approved = record.price_approved * record.qty_approved
            record.amount_approved = amount_approved


class PsAccountPayment(models.Model):
    _inherit = "account.payment"

    expense_request_id = fields.Many2one('ps.hr.expense.request', string='Expense Request Id')
    loan = fields.Boolean(string='Loan')


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    @api.multi
    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_user'):
            raise UserError(_("Only HR Officers can approve expenses"))
        self.write({'state': 'approve', 'responsible_id': self.env.user.id})
        #   2019年1月14日迭代8：费用申请需求变更-old-begin；
        # 更新费用申请中的 amount_reimburse
        # if self.expense_line_ids:
        #     amount_reimburse = 0.0
        #     for rec in self.expense_line_ids:
        #         amount_reimburse += rec.total_amount
        # expense_request = self.env['ps.hr.expense.request'].search([('sheet_id', '=', self.id)])
        # expense_request.write({'amount_reimburse': amount_reimburse})
        #   2019年1月14日迭代8：费用申请需求变更-old-end；
        #   2019年1月14日迭代8：费用申请需求变更-new-begin；
        #   考虑一次提交多张单据明细的场景
        if self.expense_line_ids:
            for rec in self.expense_line_ids:
                expense_request = self.env['ps.hr.expense.request'].search([('id', '=', rec.request_id.id)])
                amount_reimburse = expense_request.amount_reimburse
                amount_reimburse += rec.total_amount
                expense_request.write({'amount_reimburse': amount_reimburse})
                # 是否已经形成费用付款单
                account_payments = self.env['account.payment'].search([('ps_expense_request_id.id', '=', expense_request.id)])
                for account_payment in account_payments:
                    if account_payment.state == 'posted':
                        expense_request.compute_amount_theoretical()


class HrExpense(models.Model):
    _inherit = "hr.expense"

    request_id = fields.Many2one('ps.hr.expense.request', string='Expense Request Id')


class HrExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = "hr.expense.sheet.register.payment.wizard"

    def _get_payment_vals(self):

        result = super(HrExpenseSheetRegisterPaymentWizard, self)._get_payment_vals()
        result.update({'payment_use': self.env.ref('ps_account.payment_use_preset_expense_payment').id})
        return result