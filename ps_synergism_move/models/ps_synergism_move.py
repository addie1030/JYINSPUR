# -*- coding: utf-8 -*-
import sys
import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
# reload(sys)
# sys.setdefaultencoding('utf8')

import logging
_logger = logging.getLogger(__name__)

class PsAccountMoveTrade(models.Model):
    # 内部交易记录
    _name = 'ps.account.move.trade'
    _rec_name = 'display_name'


    src_move_id = fields.Many2one('account.move', string='Src Move Id')
    des_company_id = fields.Many2one('res.partner', string='Des Company Id')
    type_id = fields.Many2one('ps.account.trade.type', string='Type Id')
    trade_no = fields.Char(string='Trade No')
    src_company_id = fields.Many2one('res.partner', string='Src Company Id')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State')
    origin = fields.Selection([('send', 'Send'), ('receive', 'Receive')], string='Origin')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    # @api.multi
    # def unlink(self):
        # raise ValidationError(_("Cannot delete the internal transaction record, please go to the certificate page to cancel the internal transaction record."))


    @api.depends('src_company_id', 'trade_no')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.src_company_id.name + record.trade_no


class PsAccountMove(models.Model):
    # 凭证
    _inherit = "account.move"

    ps_way = fields.Selection([('send', 'Send'), ('receive', 'Receive')], string='Ps Way')
    ps_trade_no = fields.Char(string='Ps Trade No')
    ps_type_id = fields.Many2one('ps.account.trade.type', string='Ps Type Id')
    ps_partner_id = fields.Many2one('res.partner', string='Ps Partner Id', domain=[('is_company', '=', True)])
    ps_boolean_inside = fields.Boolean(string='Ps Boolean Id', default=False)
    ps_mark = fields.Boolean(string='Ps Mark', default=False, copy=False)
    ps_trade_id = fields.Many2one(comodel_name='ps.account.move.trade', copy=False, string='Ps Trade Id',
                                  domain=lambda self: [('state', '=', 'draft'), ('origin', '=', 'send'),
                                                       ('des_company_id', '=', self.env.user.company_id.partner_id.id)])


    def mark_account_move_insider_dealing(self):
        # 判断发送方科目是否与对照表中的科目一致
        pamt = self.env['ps.account.move.trade']
        if self.ps_way == 'receive':
            rec = pamt.search([('origin', '=', 'receive'), ('trade_no', '=', self.ps_trade_no)])
            if rec:
                raise ValidationError(_('Voucher ') + self.ps_trade_no + _(' is already exists in the internal transaction record and cannot be created repeatedly.'))
        elif self.ps_way == 'send':
            rec = pamt.search([('origin', '=', 'send'), ('trade_no', '=', self.ps_trade_no)])
            if rec:
                raise ValidationError(_('Voucher ') + self.ps_trade_no + _(' is already exists in the internal transaction record and cannot be created repeatedly.'))

        trade_relate = self.env['ps.account.trade.relate']  # 科目对照表
        trade_no = []  # 中间表业务号
        trade_des_account = []
        trade_src_accout = []
        for i in pamt.sudo().search([]):
            trade_no.append(i.trade_no)
        for i in trade_relate.sudo().search([]):
            trade_src_accout.append(i.src_account_id.code)
            trade_des_account.append(i.des_account_id.code)
        if self.ps_trade_no not in trade_no:
            count = 0
            for line in self.line_ids:
                count += 1
                if self.ps_way == 'send':
                    trade_account = trade_src_accout
                else:
                    trade_account = trade_des_account

                if line.account_id.code not in trade_account:
                    raise ValidationError(_("In voucher") + str(count) + _("line") + line.account_id.name + _("inconsistence of subject settings between subjects and internal transaction control tables."))
                # 标记内部交易时，判断借贷方科目是否一致
                for i in trade_relate.sudo().search([]):
                    if i.src_account_id.code == line.account_id.code:
                        if line.credit != 0:
                            if i.src_direction != 'credit':
                                raise ValidationError(_("In voucher") + str(count) + _("The correspondence between the lender of the subject and the lender in the subject control table is inconsistent and cannot be labeled as an internal transaction."))
                        else:
                            if i.src_direction != 'debit':
                                raise ValidationError(_("In voucher") + str(count) + _("The correspondence between the lender of the subject and the lender in the subject control table is inconsistent and cannot be labeled as an internal transaction."))
        ps_move_id = self.env.context.get('ps_move_id')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('ps_synergism_move.ps_mark_move_trade_view').id,
            'target': 'new',
            'res_model': 'ps.mark.move.trade.wizard',
            'context': {'ps_move_id': ps_move_id}
        }


    @api.model
    def create(self, values):
        # 编号自动生成
        if 'code' not in values or values['code'] == _('New'):
            values['ps_trade_no'] = self.env['ir.sequence'].next_by_code('ps.trade.no')
        if 'ps_trade_id' in values.keys() and values['ps_way'] == 'receive':
            trade = self.env['ps.account.move.trade'].browse(values['ps_trade_id'])
            values['ps_partner_id'] = trade.src_company_id.id
            values['ps_trade_no'] = trade.trade_no
            values['ps_type_id'] = trade.type_id.id
        return super(PsAccountMove, self).create(values)


    @api.onchange('ps_trade_id')
    def _onchange_ps_trade_id(self):
        if self.ps_way == 'receive' and self.ps_trade_id:
            self.ps_trade_no = self.ps_trade_id.trade_no
            self.ps_type_id = self.ps_trade_id.type_id
            self.ps_partner_id = self.ps_trade_id.src_company_id.id
            # 通过关联业务获取中间表
            trades = self.env['ps.account.move.trade'].sudo().search([('trade_no', '=', self.ps_trade_no)])
            # 获取科目对照表
            relates = self.env['ps.account.trade.relate'].sudo().search([])
            # 找到与关联公司类型相同的内部交易业务类型 并且为发送方的中间表
            trade_move = trades.filtered(lambda r: r.type_id.id == self.ps_type_id.id and r.origin == 'send')

            lines = []
            for x in trade_move:
                # 找到关联业务凭证
                move_lines = self.env['account.move.line'].sudo().search([('move_id', '=', x.src_move_id.id)])
                # 遍历关联业务凭证，并且构建凭证行数据
                for line in move_lines:
                    # 通过关联公司凭证行的科目编号 来获取需要构建的当前凭证行科目编号，如果存在多个数据则为空
                    if len(relates.filtered(lambda r: r.src_account_id.code == line.account_id.code)) > 1:
                        account_id = False
                    else:
                        account_id_code = relates.filtered(lambda r: r.src_account_id.code == line.account_id.code)[
                            0].des_account_id.code
                        account_id = self.env['account.account'].search([('code', '=', account_id_code)]).id
                    # 判断中间表数据的方向，如果存在多条数据，则取默认的第一条数据来填充数据
                    if relates.filtered(lambda r: r.src_account_id.code == line.account_id.code)[
                        0].des_direction == 'debit':
                        line_debit = line.debit if line.debit > 0 else line.credit
                        line_credit = 0
                    else:
                        line_credit = line.debit if line.debit > 0 else line.credit
                        line_debit = 0
                    # 填充数据
                    lines.append([0, False, {
                        'name': line.name,
                        'company_id': self.env.user.company_id.id,
                        'partner_id': self.ps_partner_id.id,
                        'date': line.date,
                        'account_id': account_id,
                        'debit': line_debit,
                        'credit': line_credit,
                        'quantity': line.quantity,
                        'date_maturity': line.date_maturity,
                    }])
            if lines:
                self.line_ids = lines

    def cancel_insider_dealing_account_move(self):
        ps_trade_no = self.env.context.get('ps_trade_no')
        origin = ''
        pamt = self.env['ps.account.move.trade']
        recs_send = pamt.search(
            [('trade_no', '=', self.env.context.get('ps_trade_no')), ('origin', '=', 'send')])  # 发送方写入的记录
        recs_receive = pamt.search(
            [('trade_no', '=', self.env.context.get('ps_trade_no')), ('origin', '=', 'receive')])  # 接收方写入的记录
        if self.ps_way == 'receive':
            if recs_receive:
                if recs_receive[0].src_company_id.id == self.env.user.company_id.partner_id.id:  # 当前操作的用户为接收方
                    origin = 'receive'
                    return {
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': self.env.ref('ps_synergism_move.ps_cancle_move_trade_view').id,
                        'target': 'new',
                        'res_model': 'ps.cancle.move.trade.wizard',
                        'context': {'ps_trade_no': ps_trade_no, 'origin': origin}
                    }
                elif recs_receive[0].src_company_id.id != self.env.user.company_id.partner_id.id:  # 当前操作的用户不是接收方
                    raise ValidationError(_("Business number: ") + ps_trade_no + _(
                        " receiver has generated credentials and needs to cancel internal transactions. "))
        if self.ps_way == 'send':
            if recs_send:
                if recs_send[0].src_company_id.id == self.env.user.company_id.partner_id.id:  # 当前操作的用户为发送方
                    if recs_send and recs_receive:
                        raise ValidationError(_(
                            "This document has been confirmed and cannot be cancelled."))
                    origin = 'send'
                    return {
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'view_id': self.env.ref('ps_synergism_move.ps_cancle_move_trade_view').id,
                        'target': 'new',
                        'res_model': 'ps.cancle.move.trade.wizard',
                        'context': {'ps_trade_no': ps_trade_no, 'origin': origin}
                    }
                elif recs_send[0].src_company_id.id != self.env.user.company_id.partner_id.id:  # 当前操作用户不是发送方
                    raise ValidationError(_(
                        "The current login user is not the sender. Please contact the sender to cancel the internal transaction."))


