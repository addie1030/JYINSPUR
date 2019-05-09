# -*- coding: utf-8 -*-
import json
from odoo import fields, models, api, tools, _


class CreditUsage(models.Model):
    _name = 'ps.credit.usage'
    _description = 'ps.credit.usage'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    date_end = fields.Date(string='Date End', compute='_get_profile_data')
    partner_id = fields.Many2one('res.partner', string='Customer')
    check_scheme_id = fields.Many2one('ps.credit.check.scheme', string='Check Scheme', compute='_get_profile_data')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_get_profile_data')
    level = fields.Char(string='Level', compute='_get_profile_data')
    credit_ratio = fields.Float(string='Credit Ratio', compute='_get_profile_data')
    credit_limit = fields.Float(string='Credit Limit', compute='_get_profile_data')
    order_limit = fields.Float(string='Order limit', compute='_get_profile_data')
    overdue_ratio = fields.Float(string='Overdue Ratio', compute='_get_profile_data')
    overdue_limit = fields.Float(string='Overdue Limit', compute='_get_profile_data')
    overdue_days = fields.Integer(string='Overdue Days', compute='_get_profile_data')
    credit_ratio_limit = fields.Float(string='Credit Ratio Limit',
                                      compute='_compute_credit_data')
    prepaid = fields.Float(string='Prepaid', compute='_compute_credit_data')
    balance = fields.Float(string='Balance', compute='_compute_credit_data')
    actual_overdue_ratio = fields.Float(string='Actual Overdue Ratio',
                                        compute='_compute_credit_data')
    actual_overdue_limit = fields.Float(string='Actual Overdue Limit',
                                        compute='_compute_credit_data')
    actual_overdue_days = fields.Float(string='Actual Overdue Days',
                                       compute='_compute_credit_data')
    used_limit = fields.Float(string='Used Limit',
                              compute='_compute_credit_data')
    temporary_order_limit = fields.Float(string='Temporary Order Limit')
    temporary_credit = fields.Float(string='Temporary Credit')
    temporary_overdue = fields.Float(string='Temporary Overdue')
    temporary_overdue_limit = fields.Float(string='Temporary Overdue Limit')
    temporary_overdue_days = fields.Integer(string='Temporary Overdue Days')

    def _get_profile_data(self):
        current_date = fields.Date.today()
        for record in self:
            profile_obj = self.env['ps.credit.profile'].search(
                [('partner_id', '=', record.partner_id.id), ('date_start', '<=', current_date),
                 ('date_end', '>=', current_date), ('state', '=', 'confirmed')], limit=1)
            if profile_obj:
                record.date_end = profile_obj.date_end
                record.check_scheme_id = profile_obj.check_scheme_id.id
                record.currency_id = profile_obj.currency_id.id
                record.level = profile_obj.level_id.name
                record.credit_ratio = profile_obj.ratio
                record.credit_limit = profile_obj.credit_limit
                record.order_limit = profile_obj.order_limit
                record.overdue_ratio = profile_obj.overdue_ratio
                record.overdue_limit = profile_obj.overdue_limit
                record.overdue_days = profile_obj.overdue_days
            else:
                profile_obj = self.env['ps.credit.profile'].search(
                    [('partner_id', '=', record.partner_id.id), ('date_start', '<=', current_date),
                     ('date_end', '>=', current_date), ('state', '=', 'closed')], limit=1)
                if profile_obj:
                    record.date_end = profile_obj.date_end
                    record.check_scheme_id = profile_obj.check_scheme_id.id
                    record.currency_id = profile_obj.currency_id.id
                    record.level = ''
                    record.credit_ratio = 0
                    record.credit_limit = 0
                    record.order_limit = 0
                    record.overdue_ratio = 0
                    record.overdue_limit = 0
                    record.overdue_days = 0

    def _compute_posted_prepaid(self, partner_id):
        amount = 0.0
        for i in self.env['account.invoice'].search([('partner_id', '=', partner_id.id)]):
            d = json.loads(i.payments_widget)
            if d:
                for i in d['content']:
                    amount += i['amount']
        return amount

    def _compute_prepaid(self, account_id, partner_id):
        """
        应收科目中未核销的贷方之和:
        """
        return sum([i.credit for i in self.env['account.move.line'].search([
            ('date_maturity', '<=', fields.Date.today()),
            ('account_id', '=', account_id.id), ('partner_id', '=', partner_id.id), ('reconciled', '=', False)
        ])])

    def _compute_actual_overdue_limit(self, account_id, partner_id):
        """
        应收科目中未核销的借方之和
        """
        debit = sum([i.debit for i in self.env['account.move.line'].search([
            ('date_maturity', '<', fields.Date.today()),
            ('account_id', '=', account_id.id), ('partner_id', '=', partner_id.id), ('reconciled', '=', False)
        ])])
        if not debit:
            return 0.0
        return debit - self._compute_posted_prepaid(partner_id)

    def _compute_actual_overdue_ratio(self, partner_id, account_id, actual_overdue_limit):
        """
        　实际逾期金额(扣除过账预收款) / 应收款(扣除过账预收款)
        分几种情况：
        1.应收账款为零 实际逾期为零  0
        2.应收账款为零 实际逾期不为零   1
        3.应收不为零
        """
        debit = sum([i.debit for i in self.env['account.move.line'].search([
            ('partner_id', '=', partner_id.id), ('account_id', '=', account_id.id), ('reconciled', '=', False)
        ])]) - self._compute_posted_prepaid(partner_id)
        if debit == 0 and actual_overdue_limit == 0:
            return 0
        elif debit == 0 and actual_overdue_limit != 0:
            return 1
        return abs(actual_overdue_limit / debit)

    def _compute_actual_overdue_days(self, account_id, partner_id):
        """
        应收单上，到期未核销应收单的最大逾期天数（系统日期-到期日）
        """
        far_overdue = self.env['account.invoice'].search(
            [('company_id', '=', self.env.user.company_id.id), ('partner_id', '=', partner_id.id),
             ('account_id', '=', account_id.id), ('reconciled', '=', False), ('date_due', '>', fields.Date.today())
             ], limit=1, order='date_due DESC').date_due
        if not far_overdue:
            return 0
        else:
            return (far_overdue - fields.Date.today()).days

    def _compute_sale_order_amount(self, partner_id):
        sale_order = self.env['sale.order.line'].search(
            [('order_id.partner_id', '=', partner_id.id),
             ('invoice_status', '!=', 'invoiced'), ('state', '=', 'sale')])
        return sum([i.price_unit * (i.product_uom_qty - i.qty_invoiced) for i in sale_order])

    def _compute_outgoing_amount(self, partner_id):
        """计算出库金额"""
        outgoing_ids = self.env['stock.picking.type'].search([('code', '=', 'outgoing')])
        invoice_ids = self.env['account.invoice'].search(
            [('ps_picking_id', '!=', None), ('partner_id', '=', partner_id.id)])
        picking_ids = []
        for invoice_id in invoice_ids:
            for picking_id in invoice_id.ids:
                picking_ids.append(picking_id)
        move_ids = self.env['stock.move'].search(
            [('sale_line_id', '=', None), ('picking_type_id', 'in', [i.id for i in outgoing_ids]),
             ('state', '=', 'done'), ('picking_id', 'not in', picking_ids),
             ('picking_id.partner_id', '=', partner_id.id)])
        outgoing_amount = 0
        for move_id in move_ids:
            if move_id.quantity_done > 0:
                qty_done = move_id.quantity_done
            else:
                qty_done = move_id.product_uom_qty
            outgoing_amount += (qty_done - move_id.ps_invoice_qty) * move_id.ps_stock_price
        return outgoing_amount

    def _compute_credit_data(self):
        for record in self:
            customer_ids = self.env['ps.credit.usage'].search([('company_id', '=', record.company_id.id)])
            account_id = record.company_id.partner_id.property_account_receivable_id
            for line in customer_ids:
                line.prepaid = self._compute_prepaid(account_id, line.partner_id)
                line.credit_ratio_limit = line.prepaid * (1 + line.credit_ratio)
                costumer = self.env['res.partner'].search([('id', '=', line.partner_id.id)])
                total_due = costumer.total_due
                line.used_limit = self._compute_sale_order_amount(
                    line.partner_id) + total_due + self._compute_outgoing_amount(line.partner_id) + line.prepaid
                line.actual_overdue_days = self._compute_actual_overdue_days(account_id, line.partner_id)
                line.actual_overdue_limit = self._compute_actual_overdue_limit(account_id, line.partner_id)
                line.actual_overdue_ratio = self._compute_actual_overdue_ratio(line.partner_id, account_id,
                                                                               line.actual_overdue_limit,
                                                                               )
                line.balance = line.credit_limit - line.used_limit
