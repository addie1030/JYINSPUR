# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools


class PsCheckPostAccountMove(models.TransientModel):
    _name = "ps.check.post.account.move"
    _description = _("Move Confirmed")

    @api.multi
    @api.constrains('ps_analytic_boolean')
    def check_account_move(self):
        flag = False
        shbrdj = self.env.user.company_id.ps_same_user_approval
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the move to be confirmed.'))
        move_ids = []
        move_line_ids = []
        axauxiliary_line_ids = []
        movelines = self.env['account.move.line'].browse(context.get('active_ids'))

        for r in movelines:
            move_ids.append(r.move_id)
            move_line_ids.append(r.move_id.id)
            for n in r.move_id.line_ids:
                axauxiliary_line_ids.append(n)

        num = 0
        if(axauxiliary_line_ids):
            for r in axauxiliary_line_ids:
                name = r.account_id.name
                id = r.account_id.id
                res = self.env['account.account'].search([('id', '=', id)])
                if res:
                    for n in res:
                        if n.ps_consider_partner:
                            if not r.ps_sub_id:
                                num = num + 1
                                r.with_context(
                                    {'move_warn_color': '1', 'check_post_write': '1'}).write({'warn_color': True})
                        if n.ps_consider_product:
                            if not r.ps_sub_id:
                                num = num + 1
                                r.with_context(
                                    {'move_warn_color': '1', 'check_post_write': '1'}).write({'warn_color': True})
                        if n.ps_is_cash_flow:
                            if not r.ps_sub_id:
                                num = num + 1
                                r.with_context(
                                    {'move_warn_color': '1', 'check_post_write': '1'}).write({'warn_color': True})
            if num != 0:
                view_id = self.env.ref('ps_account.ps_check_account_move_view_auxiliary').id

                return {'type': 'ir.actions.act_window',
                        'res_model': 'ps.check.post.account.move',
                        'views': [[view_id, 'form']],
                        'target': 'new',
                        }
        if len(move_ids):
            for r in move_ids:
                if not shbrdj:  # 不允许审核本人单据
                    if r.create_uid.id == self.env.user.id:
                        raise UserError(_('The create user cannot be the same as the confirmed one.'))
                if r.state == 'checked':
                    raise UserError(_('The move【') + r.ref + _('】has been confirmed and cannot be confirmed repeatedly.'))
                elif r.state == 'posted':
                    raise UserError(_('The move【') + r.ref + _('】has been posted and cannot be confirmed.'))
                else:
                    r.with_context({'check_post_write': '1'}).write({'state': 'checked', 'ps_confirmed_user': self.env.user.id, 'ps_confirmed_datetime': fields.Date.today()})
                    self.env['account.move.line'].search([('move_id', 'in', move_line_ids)]).with_context({'check_post_write': '1'}).write({'move_state': 'checked'})
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def get_check_view_id(self):
        view_id = self.env.ref('ps_account.ps_check_account_move_view').id
        return view_id



class PsPostAccountMove(models.TransientModel):
    _name = "ps.post.account.move"
    _description = "Move Posted"

    @api.multi
    def post_account_move(self):
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the move to be posted.'))
        move_ids = []
        move_line_ids = []
        movelines = self.env['account.move.line'].browse(context.get('active_ids'))
        # print(movelines.mapped('name'))
        for r in movelines:
            move_ids.append(r.move_id)
            move_line_ids.append(r.move_id.id)
        if len(move_ids):
            for r in move_ids:
                if r.state == 'draft':
                    raise UserError(_('The move【') + r.ref + _('】has not been confirmed and cannot be posted.'))
                elif r.state == 'posted':
                    raise UserError(_('The move【') + r.ref + _('】has been posted and cannot be posted repeatedly.'))
                else:
                    r.with_context({'check_post_write': '1'}).write({'state': 'posted', 'ps_posted_user': self.env.user.id,
                             'ps_posted_datetime': fields.Date.today()})
                    self.env['account.move.line'].search([('move_id', 'in', move_line_ids)]).with_context({'check_post_write': '1'}).write(
                        {'move_state': 'posted'})
        return {'type': 'ir.actions.act_window_close'}

class PsUnCheckAccountMove(models.TransientModel):
    _name = "ps.uncheck.account.move"
    _description = "Cancel Confirmed"

    @api.multi
    def uncheck_account_move(self):
        # obj = self.env['ps.account.move.check']
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the move to be unconfirmed.'))
        move_ids = []
        move_line_ids = []
        movelines = self.env['account.move.line'].browse(context.get('active_ids'))

        for r in movelines:
            move_ids.append(r.move_id)
            move_line_ids.append(r.move_id.id)
        if len(move_ids):
            for r in move_ids:
                if r.state == 'posted':
                    raise UserError(_('The move【') + r.ref + _('】has been posted，please cancel the posted first.'))
                elif r.state == 'draft':
                    raise UserError(_('The move【') + r.ref + _('】has not been confirmed.'))
                else:
                    r.with_context({'check_post_write': '1'}).write({'state': 'draft', 'ps_confirmed_user': 0, 'ps_confirmed_datetime': False})
                    self.env['account.move.line'].search([('move_id', 'in', move_line_ids)]).with_context({'check_post_write': '1'}).write(
                        {'move_state': 'draft'})
        return {'type': 'ir.actions.act_window_close'}

class PsUnPostAccountMove(models.TransientModel):
    _name = "ps.unpost.account.move"
    _description = "Cancel Posted"

    @api.multi
    def unpost_account_move(self):

        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the move to be unposted.'))
        move_ids = []
        move_line_ids = []
        movelines = self.env['account.move.line'].browse(context.get('active_ids'))
        # print(movelines.mapped('name'))

        for r in movelines:
            move_ids.append(r.move_id)
            move_line_ids.append(r.move_id.id)
        if len(move_ids):
            for r in move_ids:
                period_ids = self.env['ps.account.period'].get_period(r.date)
                if not period_ids:
                    raise UserError(_('Not getting the current accounting month, please add.'))
                if period_ids[0].financial_state == '2':
                    raise UserError(str(r.date) + _(' The current date is in the month and cannot be cancelled.'))
                if r.state == 'checked':
                    raise UserError(_('The move【') + r.ref + _('】has not been posted.'))
                else:
                    r.with_context({'check_post_write': '1'}).write({'state': 'checked', 'ps_posted_user': 0,
                             'ps_posted_datetime': False})
                    self.env['account.move.line'].search([('move_id', 'in', move_line_ids)]).with_context({'check_post_write': '1'}).write(
                        {'move_state': 'checked'})
        return {'type': 'ir.actions.act_window_close'}


class PsSubOpening(models.Model):
    _name = 'ps.sub.opening'
    _description = 'ps.sub.opening'


    subopening_ids = fields.One2many('ps.account.move.line.sub', 'opening_sub_id')

    @api.onchange('subopening_ids')
    def _set_account_id(self):
        if self.subopening_ids:
            for r in self.subopening_ids:
                r.account_id = self.env.context.get('auxiliary_account_id')


    def ps_set_account_move_line(self):
        account = self.env['account.account'].search([('id', '=', self.env.context.get('auxiliary_account_id'))])
        amount_debit = 0.0
        amount_redit = 0.0
        if self.subopening_ids:
            account.write({'ps_sub_id': self.id})
            for r in self.subopening_ids:
                if r.balance_direction == '1':
                    amount_debit = amount_debit + r.amount
                elif r.balance_direction == '2':
                    amount_redit = amount_redit + r.amount

        if amount_debit != 0 and amount_redit != 0:
            if amount_debit > amount_redit:
                account.write({'opening_debit': amount_debit - amount_redit})
            elif amount_debit < amount_redit:
                account.write({'opening_credit': amount_redit - amount_debit})

        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PsSubOpening, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        account = self.env['account.account'].search([('id', '=', self.env.context.get('auxiliary_account_id'))])
        if account.currency_id:
            consider_currency = True
        else:
            consider_currency = False
        if account.ps_consider_partner:
            consider_partner = True
        else:
            consider_partner = False
        if account.ps_consider_product:
            ps_consider_product = True
            consider_quantity = True
        else:
            ps_consider_product = False
            consider_quantity = False
        if account.ps_is_cash_flow:
            ps_is_cash_flow = True
        else:
            ps_is_cash_flow = False

        if view_type == 'form':
            treev = res['fields']['subopening_ids']['views']['tree']
            doc = etree.XML(treev['arch'])
            if consider_partner:#往来单位
                if doc.xpath("//tree/field[@name='ps_consider_partner']"):
                    node = doc.xpath("//tree/field[@name='ps_consider_partner']")[0]
                    node.set('invisible', '0')
                    treev['fields']['ps_consider_partner']['required'] = True
                    setup_modifiers(node, treev['fields']['ps_consider_partner'])
            if consider_currency:
                if doc.xpath("//tree/field[@name='ps_consider_currency']"):
                    node = doc.xpath("//tree/field[@name='ps_consider_currency']")[0]
                    node.set('invisible', '0')
                    setup_modifiers(node, treev['fields']['ps_consider_currency'])
                if doc.xpath("//tree/field[@name='ps_currency_rate']"):
                    node = doc.xpath("//tree/field[@name='ps_currency_rate']")[0]
                    node.set('invisible', '0')
                    setup_modifiers(node, treev['fields']['ps_currency_rate'])
            if ps_consider_product:
                if doc.xpath("//tree/field[@name='ps_consider_product']"):
                    node = doc.xpath("//tree/field[@name='ps_consider_product']")[0]
                    node.set('invisible', '0')
                    treev['fields']['ps_consider_product']['required'] = True
                    setup_modifiers(node, treev['fields']['ps_consider_product'])
            if consider_quantity:
                if doc.xpath("//tree/field[@name='product_uom_id']"):
                    node = doc.xpath("//tree/field[@name='product_uom_id']")[0]
                    node.set('invisible', '0')
                    setup_modifiers(node, treev['fields']['product_uom_id'])
                if doc.xpath("//tree/field[@name='ps_consider_quantity']"):
                    node = doc.xpath("//tree/field[@name='ps_consider_quantity']")[0]
                    node.set('invisible', '0')
                    setup_modifiers(node, treev['fields']['ps_consider_quantity'])
                if doc.xpath("//tree/field[@name='unit_price']"):
                    node = doc.xpath("//tree/field[@name='unit_price']")[0]
                    node.set('invisible', '0')
                    setup_modifiers(node, treev['fields']['unit_price'])
                if consider_currency:  # 核算数量，核算外币
                    if doc.xpath("//tree/field[@name='amount']"):
                        node = doc.xpath("//tree/field[@name='amount']")[0]
                        node.set('invisible', '0')
                        node.set('string', _('local currency amount'))
                        node.set('readonly', '1')  # 自动算本币金额
                        setup_modifiers(node, treev['fields']['amount'])
                    if doc.xpath("//tree/field[@name='amount_input']"):
                        node = doc.xpath("//tree/field[@name='amount_input']")[0]
                        node.set('invisible', '0')
                        node.set('readonly', '1')  # 自动算外币金额
                        node.set('string', _('currency amount'))
                        setup_modifiers(node, treev['fields']['amount_input'])
                else:  # 核算数量，不核算外币
                    if doc.xpath("//tree/field[@name='amount']"):
                        node = doc.xpath("//tree/field[@name='amount']")[0]
                        node.set('invisible', '0')
                        node.set('string', _('amount'))
                        node.set('readonly', '1')  # 自动算金额
                        setup_modifiers(node, treev['fields']['amount'])
                    # if doc.xpath("//tree/field[@name='amount_input']"):
                    #     node = doc.xpath("//tree/field[@name='amount_input']")[0]
                    #     node.set('invisible', '1')
                    #     node.set('readonly', '0')
                    #     node.set('string', _('Amount of money'))
                    #     setup_modifiers(node, treev['fields']['amount_input'])
            else:
                if consider_currency:  # 不核算数量，但是核算外币
                    if doc.xpath("//tree/field[@name='amount']"):
                        node = doc.xpath("//tree/field[@name='amount']")[0]
                        node.set('invisible', '0')
                        node.set('string', _('local currency amount'))
                        node.set('readonly', '1')
                        setup_modifiers(node, treev['fields']['amount'])
                    if doc.xpath("//tree/field[@name='amount_input']"):
                        node = doc.xpath("//tree/field[@name='amount_input']")[0]
                        node.set('invisible', '0')
                        node.set('readonly', '0')  # 手工输入外币金额，自动算出本币金额
                        node.set('string', _('currency amount'))
                        setup_modifiers(node, treev['fields']['amount_input'])
                else:  # 不核算数量，也不核算外币
                    # if doc.xpath("//tree/field[@name='amount']"):
                    #     print('^^^不核算数量，也不核算外币^^^')
                    #     node = doc.xpath("//tree/field[@name='amount']")[0]
                    #     node.set('invisible', '0')  # 隐藏
                    #     node.set('string', _('amount'))
                    #     node.set('readonly', '0')
                    #     setup_modifiers(node, treev['fields']['amount'])
                    if doc.xpath("//tree/field[@name='amount_input']"):
                        node = doc.xpath("//tree/field[@name='amount_input']")[0]
                        node.set('invisible', '0')
                        node.set('readonly', '0')  # 手工输入金额
                        node.set('string', _('amount'))
                        setup_modifiers(node, treev['fields']['amount_input'])
            if ps_is_cash_flow:
                if doc.xpath("//tree/field[@name='cash_flow_item_id']"):
                    node = doc.xpath("//tree/field[@name='cash_flow_item_id']")[0]
                    node.set('invisible', '0')
                    treev['fields']['cash_flow_item_id']['required'] = True
                    setup_modifiers(node, treev['fields']['cash_flow_item_id'])
            treev['arch'] = etree.tostring(doc, encoding='unicode')
        return res
