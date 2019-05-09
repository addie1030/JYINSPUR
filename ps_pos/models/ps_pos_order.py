# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, tools, _
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
from datetime import datetime

class PsPosOrder(models.Model):
    _inherit = 'pos.order'

    ps_total_offer = fields.Float(digits=dp.get_precision('ps_unit_price'), string='Offer Amount')

    @api.multi
    def get_amount_gift_points(self):
        if not self.partner_id:  # 是否选择了客户
            return
        if not self.partner_id.ps_member_no:  # 该客户是否维护了会员
            return
        result = self.env['ps.member.category.point.rule'].search(
            [('member_category_id', '=', self.partner_id.ps_member_category_id.id), ('date_start', '<=', self.date_order),
             ('date_end', '>=', self.date_order)], limit=1)
        if not result: #该会员类别是否维护了积分规则
            return
        amount_gift_points = safe_eval(result.formula_point, {'x': self.amount_paid})
        return amount_gift_points


    @api.model
    def _process_order(self, pos_order):
        res = super(PsPosOrder, self)._process_order(pos_order)
        if self.env.context.get('pos_origin') != 'juye':
            total_price = 0.00
            for r in res.lines:
                price = r.product_id.list_price * r.qty
                total_price = total_price + price
            res.ps_total_offer = total_price - res.amount_paid
            deposit_amount = 0.00
            bonus_amount = 0.00
            result = res.get_amount_gift_points()#pos消费后应获得的积分
            amount_gift_points = result if result else 0.00
            if res.partner_id.ps_member_no:
                if res.statement_ids[0].journal_id.ps_is_member_deposit:#当前支付方式为储值
                    deposit_amount, bonus_amount = self.env[
                        'ps.member.category.bonus.use.set'].get_bonus_amount_update_member_bonus_info(res.partner_id.id,
                                                                                                      res.date_order,
                                                                                                      res.amount_paid)
                    self.env['ps.member.cashflow.account'].create({
                        'business_date': res.date_order,
                        'origin': 'pos.order,' + str(res.id) ,
                        'company_id': self.env.user.company_id.id,
                        'user_id': self.env.user.id,
                        'partner_id': res.partner_id.id,
                        'type': 'depositconsume',
                        'consume_deposit_amount': deposit_amount,#消费储值金额
                        'consume_bonus_amount': bonus_amount, #消费赠送金额
                        'bonus_point': amount_gift_points #赠送积分
                    })
                else:
                    self.env['ps.member.cashflow.account'].create({
                        'business_date': res.date_order,
                        'origin': 'pos.order,' + str(res.id),
                        'company_id': self.env.user.company_id.id,
                        'user_id': self.env.user.id,
                        'partner_id': res.partner_id.id,
                        'type': 'cashconsume',
                        'consume_cash': res.amount_paid,  # 消费现金res.amount_paid
                        'bonus_point': amount_gift_points  # 赠送积分
                    })
                # 回写最后一次消费日期
                res.partner_id.ps_last_consumption_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return res

class PsPosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    @api.multi
    def check(self):
        if self.env.context.get("pos_origin") != 'juye':
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            rec = self.env['pos.order'].search([('pos_reference', '=', order.pos_reference)], order='id', limit=1)
            pmca = self.env['ps.member.cashflow.account'].search([('origin', '=', 'pos.order,' + str(rec.id))])
            if pmca.type == 'depositrefund':
                pmca.copy({
                    'business_date': pmca.business_date,
                    'origin': 'pos.order,' + str(rec.id),
                    'company_id': pmca.company_id.id,
                    'user_id': pmca.user_id.id,
                    'partner_id': pmca.partner_id.id,
                    'type': 'depositrefund',
                    'consume_deposit_amount': -pmca.consume_deposit_amount,  # 消费储值金额
                    'consume_bonus_amount': -pmca.consume_bonus_amount,  # 消费赠送金额
                    'bonus_point': -pmca.bonus_point  # 赠送积分
                })
            elif pmca.type == 'cashconsume':
                pmca.copy({
                    'business_date': pmca.business_date,
                    'origin': 'pos.order,' + str(rec.id),
                    'company_id': pmca.company_id.id,
                    'user_id': pmca.user_id.id,
                    'partner_id': pmca.partner_id.id,
                    'type': 'cashconsume',
                    'consume_cash': -pmca.consume_cash,  # 消费现金
                    'bonus_point': -pmca.bonus_point  # 赠送积分
                })
            elif pmca.type == 'depositconsume':
                pmca.copy({
                    'business_date': pmca.business_date,
                    'origin': 'pos.order,' + str(rec.id),
                    'company_id': pmca.company_id.id,
                    'user_id': pmca.user_id.id,
                    'partner_id': pmca.partner_id.id,
                    'type': 'depositconsume',
                    'consume_deposit_amount': -pmca.consume_deposit_amount,  # 消费储值金额
                    'consume_bonus_amount': -pmca.consume_bonus_amount,  # 消费赠送金额
                    'bonus_point': -pmca.bonus_point  # 赠送积分
                })
        super(PsPosMakePayment, self).check()