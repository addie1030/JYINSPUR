# -*- coding: utf-8 -*-

import time
import math
from odoo import _


from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, exceptions, _
from .import ps_account_account_base
# from ps_account.models.ps_account_account_base import single_get_first, getPinyin

#建立码表
class PsCashflowItem(models.Model):
    _name = 'ps.cashflow.item'
    _description = 'ps.cashflow.item'

    name = fields.Char(string=_("Item Name"), translate=True)
    parent_id = fields.Many2one('ps.cashflow.item', string=_('Parent code'))
    company_id = fields.Many2one('res.company', string=_("Company"))

#建立科目属性表
class PsAccountAccountAttribute(models.Model):
    _name = 'ps.account.account.attribute'

    name = fields.Char(string='Attribute Name', translate=True)
    balance_direction = fields.Selection([('0', 'None'), ('1', 'Debit'), ('2', 'Credit')],  string='Balance Direction',
                                         default='0')
    first_character = fields.Char(string='First Character')

    @api.constrains('first_character')
    def _check_first_character(self):
        self.ensure_one()
        if not self.first_character.isdigit():
            raise exceptions.ValidationError(_('Please enter a number between 1-9 for the first character.'))
        elif int(self.first_character) > 9 or int(self.first_character) < 1:
            raise exceptions.ValidationError(_('Please enter a number between 1-9 for the first character.'))

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('name', _("%s (Copy)") % (self.name or ''))
        return super(PsAccountAccountAttribute, self).copy(default)

    @api.multi
    def open_new_win(self):
        rec = self.copy()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('ps_account.ps_account_account_attribute_view_form_id').id,
            'target': 'current',
            'res_model': 'ps.account.account.attribute',
            'res_id': rec.id,
            #'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': True}
        }


#修改科目表
class PsAccountAccount(models.Model):
    _inherit = 'account.account'

    parent_id = fields.Many2one('account.account', string='Parent Account')#fields.Integer()#Many2one('account.account', string='上级科目')#存放的是ps.account.account.copy表的copy_id
    ps_shortcode = fields.Char(string='Mnemonic Code')
    ps_balance_direction = fields.Selection([('0', 'None'), ('1', 'Debit'), ('2', 'Credit')],  string='Balance Direction',
                                         required=True, default='0')
    account_attribute_id = fields.Many2one('ps.account.account.attribute', string='Accounting Elements')
    
    ps_consider_partner = fields.Boolean(string='Consider Partner', default=False)
    ps_consider_product = fields.Boolean(string='Consider Product', default=False)
    ps_account_level = fields.Integer(default=1, string='Account Level')#科目所处的级数
    ps_is_leaf = fields.Boolean(string='Is Final Stage', default=True)

    ps_sub_id = fields.Many2one('ps.sub.opening', string='Auxiliary Accounting')
    ps_auxiliary_state = fields.Selection([('0', 'No'), ('1', 'Yes')], string='Auxiliary Accounting',
                                          compute='_set_ps_auxiliary_state', default='0', store=True)
    ps_is_cash_flow = fields.Boolean(string='Cash Flow', default=False)
    ps_is_account_analytic = fields.Boolean(string='Account Analytic', default=False)
    ps_analytic_tag_id = fields.Many2one('account.analytic.tag', string='Account Tags Classify')

    @api.onchange('name')
    def _set_shortcode_value(self):
        for r in self:
            if r.name:
                r.ps_shortcode = ps_account_account_base.getPinyin(r.name)

    def _compute_opening_debit_credit(self):
        for record in self:
            opening_debit = opening_credit = 0.0
            if record.company_id.account_opening_move_id:
                for line in self.env['account.move.line'].search([('account_id', '=', record.id),
                                                                 ('move_id','=', record.company_id.account_opening_move_id.id)]):
                    #could be executed at most twice: once for credit, once for debit
                    if line.debit:
                        opening_debit = opening_debit + line.debit
                    elif line.credit:
                        opening_credit = opening_credit + line.credit
            record.opening_debit = opening_debit
            record.opening_credit = opening_credit

    def _set_opening_debit_credit(self, amount, field):
        company = self.env.user.company_id
        company.create_op_move_if_non_existant()
        amount = round(float(amount), 2)

        opening_move = self.company_id.account_opening_move_id
        if not opening_move:
            raise UserError(_("No opening move defined !"))
        if opening_move:
            opening_move_line = self.env['account.move.line'].search([('account_id', '=', self.id),
                                                                      ('move_id', '=', opening_move.id)])
            if opening_move_line:
                opening_move_line.with_context({'check_move_validity': False, 'auxiliary_style': '1'}).unlink()
                if not 'import_file' in self.env.context:
                    self.company_id._auto_balance_opening_move()

            move_create = {}

            #如果有辅助核算
            # print(self.env.context.get('main_auxiliary_id'))
            # auxiliary_ids = self.env['ps.account.auxiliary'].search([('opening_auxiliary_id', '=', self.env.context.get('main_auxiliary_id'))])
            if self.ps_sub_id:
                for r in self.ps_sub_id.subopening_ids:
                    r.with_context({'auxiliary_style': '1'}).write({'state': 'used'})
                    move_create.clear()
                    # if r.balance_direction == '1':
                    #     amount = r.amount
                    # elif r.balance_direction == '2':
                    #     amount = -r.amount
                    move_create = {
                                   'name':  _('Opening balance'),
                                    field: r.amount,
                                   'move_id': opening_move.id,
                                   'account_id': self.id,
                                   'ps_sub_id': r.id,
                                   'partner_id': r.ps_consider_partner.id,
                                   'product_id': r.ps_consider_product.id,
                                   'product_uom_id': r.product_uom_id.id,
                                   'ps_currency_rate': r.ps_currency_rate,
                                   'ps_unit_price': r.unit_price,
                                   'ps_amount': amount,
                                   'cash_flow_item_id': r. cash_flow_item_id.id,
                                   'main_auxiliary_id': r.opening_sub_id.id
                                   }
                    self.env['account.move.line'].with_context({'check_move_validity': False}).create(move_create)
            else:
                move_create = {'name':  _('Opening balance'),
                                field: amount,
                                'move_id': opening_move.id,
                                'account_id': self.id}
                self.env['account.move.line'].with_context({'check_move_validity': False}).create(move_create)

            if not 'import_file' in self.env.context:
                self.company_id._auto_balance_opening_move()

    @api.depends('currency_id', 'ps_consider_partner',
                 'ps_consider_product', 'ps_is_cash_flow', 'ps_is_account_analytic')
    def _set_ps_auxiliary_state(self):
        for r in self:
            if r.currency_id or \
                    r.ps_consider_partner or \
                    r.ps_consider_product or \
                    r.ps_is_cash_flow or r.ps_is_account_analytic:
                r.ps_auxiliary_state = '1'
            else:
                r.ps_auxiliary_state = '0'

    #选择上级后，生成对应下级
    @api.onchange('parent_id')
    def _create_child_account(self):
        self.ensure_one()
        # sel = dict(fields.selection.reify(self, self._columns['account_cash_bank']))
        # print(sel)
        newcode = ''
        newname = ''
        newlev = 0
        rule = self._get_account_rule()  # 获取编码规则
        # print(rule)
        par_id = self.parent_id.id #self.env['ps.account.account.copy'].search([('id', '=', self.parent_show_id.id)]).copy_id  # 上级ID
        if not par_id:
            par_id = 0

        # par_id = self.parent_id
        par_rec = self.search([('id', '=', par_id)])
        t_id = (par_id,)
        par_lev = par_rec.ps_account_level  # 上级所处科目级数
        code = par_rec.code #上级科目code
        curr_name = par_rec.name#上级科目名称

        self._cr.execute("""\
                         SELECT      max(code)
                         FROM        account_account
                         WHERE       parent_id = %s
                         """, t_id)
        maxcode = self._cr.fetchone()[0]
        if par_lev < len(rule):#所选上级科目级数小于编码规则长度
            if par_lev == 1:
                if maxcode:
                    if len(str(int(maxcode[-int(rule[1]):]) + 1)) < int(rule[1]):
                        newcode = maxcode[:-int(rule[1])] + str(int(maxcode[-int(rule[1]):]) + 1).zfill(int(rule[1]))
                    else:
                        raise exceptions.ValidationError(_('The level-2 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                else:#没有下级
                    newcode = code + str(1).zfill(int(rule[1]))
                newlev = par_lev + 1
                newname = curr_name + _('【Level-2 transcript】')
            if par_lev == 2:
                if maxcode:
                    if len(str(int(maxcode[-int(rule[2]):]) + 1)) < int(rule[2]):
                        newcode = maxcode[:-int(rule[2])] + str(int(maxcode[-int(rule[2]):]) + 1).zfill(int(rule[2]))
                    else:
                        raise exceptions.ValidationError(_('The level-3 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                else:#没有下级
                    newcode = code + str(1).zfill(int(rule[2]))
                newlev = par_lev + 1
                newname = curr_name + _('【Level-3 transcript】')
            if par_lev == 3:
                if maxcode:
                    if len(str(int(maxcode[-int(rule[3]):]) + 1)) < int(rule[3]):
                        newcode = maxcode[:-int(rule[3])] + str(int(maxcode[-int(rule[3]):]) + 1).zfill(int(rule[3]))
                    else:
                        raise exceptions.ValidationError(_('The level-4 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                else:#没有下级
                    newcode = code + str(1).zfill(int(rule[3]))
                newlev = par_lev + 1
                newname = curr_name + _('【Level-4 transcript】')
            if par_lev == 4:
                if maxcode:
                    if len(str(int(maxcode[-int(rule[4]):]) + 1)) < int(rule[4]):
                        newcode = maxcode[:-int(rule[4])] + str(int(maxcode[-int(rule[4]):]) + 1).zfill(int(rule[4]))
                    else:
                        raise exceptions.ValidationError(_('The level-5 subject【')+maxcode+('】has reached the maximum and cannot create child subject.'))
                else:#没有下级
                    newcode = code + str(1).zfill(int(rule[4]))
                newlev = par_lev + 1
                newname = curr_name + _('【Level-5 transcript】')
        else:
            raise exceptions.ValidationError(_('The selected subject has reached the maximum and cannot create child subject.'))
        self.name = newname
        self.code = newcode
        self.ps_account_level = newlev
        self.account_attribute_id = par_rec.account_attribute_id.id
        self.user_type_id = par_rec.user_type_id.id
        self.ps_balance_direction = par_rec.ps_balance_direction
        if par_rec.user_type_id.type in ('receivable', 'payable'):
            self.reconcile = True
        else:
            self.reconcile = False
        # self.parent_id = par_id

    #对科目进行校验
    @api.constrains('code', 'account_attribute_id')
    def _check_code_rule(self):
        self.ensure_one()
        rule = self._get_account_rule()  # 获取编码规则
        szf = self.account_attribute_id.first_character  # 科目属性首字符
        # print('约束，上级科目：' + str(self.parent_show_id.id) )
        if not self.parent_id:  # 如果没有上级，则code长度等于第一级规则长度，且首字符要与科目属性首字符相等
            # 安装科目模板时，科目属性为空时，此时不判断编码规则
            if self.account_attribute_id:
                if len(self.code) != int(rule[0]):
                    raise exceptions.ValidationError(
                        _('The length of level-1 code is  ') + str(rule[0]) + ' .' + '\n\r' + _('The length of subject dose not match length of level-1 encoding rule，please re-enter.'))
            self.ps_account_level = 1
        elif self.parent_id:
            par_id = self.parent_id.id  # self.env['ps.account.account.copy'].search([('id', '=', self.parent_show_id.id)]).copy_id#上级ID
            par_lev = self.search([('id', '=', par_id)]).ps_account_level  # 上级所处科目级数
            if par_lev == 1:
                if len(self.code) != (int(rule[0]) + int(rule[1])):
                    raise exceptions.ValidationError(
                        _('The current subject is level-2, the length should be ') + str(int(rule[0]) + int(rule[1])) + ' .' + '\n\r' +
                        _('The length of subject dose not match length of level-2 encoding rule，please re-enter.'))
                self.ps_account_level = 2
            if par_lev == 2:
                if len(self.code) != (int(rule[0]) + int(rule[1]) + int(rule[2])):
                    raise exceptions.ValidationError(
                        _('The current subject is level-3, the length should be ') + str(int(rule[0]) + int(rule[1]) + int(rule[2])) + ' .' + '\n\r' +
                        _('The length of subject dose not match length of level-3 encoding rule，please re-enter.'))
                self.ps_account_level = 3
            if par_lev == 3:
                if len(self.code) != (int(rule[0]) + int(rule[1]) + int(rule[2]) + int(rule[3])):
                    raise exceptions.ValidationError(_('The current subject is level-4, the length should be ') + str(
                        int(rule[0]) + int(rule[1]) + int(rule[2]) + int(rule[3])) + ' .' + '\n\r' +
                                                     _('The length of subject dose not match length of level-4 encoding rule，please re-enter.'))
                self.ps_account_level = 4
            if par_lev == 4:
                if len(self.code) != (int(rule[0]) + int(rule[1]) + int(rule[2]) + int(rule[3]) + int(rule[4])):
                    raise exceptions.ValidationError(_('The current subject is level-5, the length should be ') + str(
                        int(rule[0]) + int(rule[1]) + int(rule[2]) + int(rule[3]) + int(rule[4])) + ' .' + '\n\r' +
                                                     _('The length of subject dose not match length of level-5 encoding rule，please re-enter.'))
                self.ps_account_level = 5
        if szf:
            if self.code[0:1] != szf:
                raise exceptions.ValidationError(_('The first character of the subject attribute is ') + szf + ' .' +
                                                 _('The first character of current subject dose not match that of subject attribute，please re-enter.'))



                #上级科目初始化
    #科目上级初始化，   --×-- 切记： 需要把account_account表中的一级科目级数字段初始化为1 --×--
    def parent_init(self):
        #初始化，先删掉ps.account.account.copy表里的所有数据
        account_copy = self.env['ps.account.account.copy'].search([])
        if len(account_copy):
            account_copy.unlink()

        #将account.account表里的数据插入到ps.account.account.copy表里
        account = self.search([])
        if len(account):
            val = {}
            account_copy = self.env['ps.account.account.copy']
            for r in account:
                r.write({'ps_account_level': 1})
                item = r.code + '【' + r.name + '】'
                id = r.id
                code = r.code
                val = {'name': item, 'copy_id': id, 'code': code}
                account_copy.create(val)
            return True

    #根据科目code生成子级科目或者同级科目
    def get_account_next(self):
        newcode = ''
        code = self.code
        ctx = self.env.context.get('par_account')#获取上下文，判断是生成同级科目same_level,还是生成子级科目child_level
        rule = self._get_account_rule()  # 获取编码规则
        lrule = len(rule)  # 编码级数
        rec = self.search([('code', '=', code)])
        curr_name = rec.name
        curr_id = rec.id  # 取当前科目ID
        account_attribute_id = rec.account_attribute_id.id
        user_type_id = rec.user_type_id.id
        ps_balance_direction = rec.ps_balance_direction
        if rec.parent_id:
            curr_par_id = rec.parent_id.id
        else:
            curr_par_id = 0
        curr_lev = rec.ps_account_level  # 当前编码级数
        t_id = (curr_id,)
        p_id = (curr_par_id,)
        if ctx == 'child_level':
            self._cr.execute("""\
                                    SELECT      max(code)
                                    FROM        account_account
                                    WHERE       parent_id = %s
                                    """, t_id)
            maxcode = self._cr.fetchone()[0]  # 获取父级ID是当前科目ID的最大code,如果有结果，说明已经存在下级，需要在下级后追加1
                                              # 无返回结果，则在当前code下追加1
            # print('当前科目：' + code)
            # print('科目最大级数：%d' % lrule )
            # if maxcode:
            #     print('当前科目级数:%d' % curr_lev)
            #     print('最大下级科目:'+maxcode)
            # else:
            #     print('当前科目级数:%d' % curr_lev)
            #     print('最大下级科目:' + '无')
            if curr_lev < lrule:
                if curr_lev == 1:
                    if maxcode:#如果当前科目有下级
                        if len(str(int(maxcode[-int(rule[1]):]) + 1)) < int(rule[1]):
                            newcode = maxcode[:-int(rule[1])] + str(int(maxcode[-int(rule[1]):]) + 1).zfill(int(rule[1]))
                            newlev = curr_lev + 1
                        else:
                            raise exceptions.ValidationError(_('The level-2 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                    else:#没有下级
                        newcode = code + str(1).zfill(int(rule[1]))
                        newlev = curr_lev + 1
                    newname = curr_name + _('【Level-2 transcript】')

                if curr_lev == 2:
                    if maxcode:#如果当前科目有下级
                        if len(str(int(maxcode[-int(rule[2]):]) + 1)) < int(rule[2]):
                            newcode = maxcode[:-int(rule[2])] + str(int(maxcode[-int(rule[2]):]) + 1).zfill(int(rule[2]))
                            newlev = curr_lev + 1
                        else:
                            raise exceptions.ValidationError(_('The level-3 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                    else:#没有下级
                        newcode = code + str(1).zfill(int(rule[2]))
                        newlev = curr_lev + 1
                    newname = curr_name + _('【Level-3 transcript】')

                if curr_lev == 3:
                    if maxcode:#如果当前科目有下级
                        if len(str(int(maxcode[-int(rule[3]):]) + 1)) < int(rule[3]):
                            newcode = maxcode[:-int(rule[3])] + str(int(maxcode[-int(rule[3]):]) + 1).zfill(int(rule[3]))
                            newlev = curr_lev + 1
                        else:
                            raise exceptions.ValidationError(_('The level-4 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                    else:#没有下级
                        newcode = code + str(1).zfill(int(rule[3]))
                        newlev = curr_lev + 1
                    newname = curr_name + _('【Level-4 transcript】')

                if curr_lev == 4:
                    if maxcode:#如果当前科目有下级
                        if len(str(int(maxcode[-int(rule[4]):]) + 1)) < int(rule[4]):
                            newcode = maxcode[:-int(rule[4])] + str(int(maxcode[-int(rule[4]):]) + 1).zfill(int(rule[4]))
                            newlev = curr_lev + 1
                        else:
                            raise exceptions.ValidationError(_('The level-5 subject【')+maxcode+_('】has reached the maximum and cannot create child subject.'))
                    else:#没有下级
                        newcode = code + str(1).zfill(int(rule[4]))
                        newlev = curr_lev + 1
                    newname = curr_name + _('【Level-5 transcript】')

            elif curr_lev == lrule:
                raise exceptions.ValidationError(_('The current subject is the last level and cannot create child subject.'))
            if rec.user_type_id.type in ('receivable', 'payable'):
                reconcile = True
            else:
                reconcile = False
            ret = {'newlev': newlev, 'newcode': newcode,
                   'parent_id': curr_id, 'newname': newname,
                   'account_attribute_id': account_attribute_id,
                   'user_type_id': user_type_id,
                   'reconcile': reconcile,
                   'ps_balance_direction': ps_balance_direction}
            # print(ret)
            return ret
        if ctx == 'same_level':
            if curr_lev == 1:
                szf = (code[0:1],)
                self._cr.execute("""\
                                 SELECT  max(code)
                                 FROM    account_account
                                 WHERE   ps_account_level = 1 and 
                                         left(code,1) = %s
                                 """, szf)
                maxcode = self._cr.fetchone()[0]
                newcode = str(int(maxcode)+1)
            elif curr_lev > 1 and curr_lev <= lrule:
                self._cr.execute("""\
                                 SELECT      max(code)
                                 FROM        account_account
                                 WHERE       parent_id = %s
                                 """, p_id)
                maxcode = self._cr.fetchone()[0]
                if curr_lev == 2:
                    if maxcode:
                        if len(str(int(maxcode[-int(rule[1]):]) + 1)) <= int(rule[1]):
                            newcode = str(int(maxcode) + 1)
                        else:
                            raise exceptions.ValidationError(_('The level-2 subject【') + maxcode +_('】has reached the maximum and cannot create peer subject.'))
                if curr_lev == 3:
                    if maxcode:
                        if len(str(int(maxcode[-int(rule[2]):]) + 1)) <= int(rule[2]):
                            newcode = str(int(maxcode) + 1)
                        else:
                            raise exceptions.ValidationError(_('The level-3 subject【') + maxcode + _('】has reached the maximum and cannot create peer subject.'))
                if curr_lev == 4:
                    if maxcode:
                        if len(str(int(maxcode[-int(rule[3]):]) + 1)) <= int(rule[3]):
                            newcode = str(int(maxcode) + 1)
                        else:
                            raise exceptions.ValidationError(_('The level-4 subject【') + maxcode + _('】has reached the maximum and cannot create peer subject.'))
                if curr_lev == 5:
                    if maxcode:
                        if len(str(int(maxcode[-int(rule[4]):]) + 1)) <= int(rule[4]):
                            newcode = str(int(maxcode) + 1)
                        else:
                            raise exceptions.ValidationError(_('The level-5 subject【') + maxcode + _('】has reached the maximum and cannot create peer subject.'))
            newname = curr_name + _('【Transcript】')
            if rec.user_type_id.type in ('receivable', 'payable'):
                reconcile = True
            else:
                reconcile = False
            ret = {'newlev': curr_lev, 'newcode': newcode,
                   'parent_id': curr_par_id, 'newname': newname,
                   'account_attribute_id': account_attribute_id,
                   'user_type_id': user_type_id,
                   'reconcile': reconcile,
                   'ps_balance_direction': ps_balance_direction}
            # print(ret)
            return ret

    #打开辅助核算列表视图窗口
    def open_ps_auxiliary_list(self):
        ps_id = self.env.context.get('auxiliary_account_id')
        """ Called by the 'Initial Balances' button of the setup bar."""
        company = self.env.user.company_id
        company.create_op_move_if_non_existant()
        # new_wizard = self.env['account.opening'].create({'company_id': company.id})

        #获取辅助核算主表ID
        res_id = 0
        move = self.env['account.move.line'].search([('move_id', '=', company.account_opening_move_id.id),
                                                       ('account_id', '=', ps_id)])
        if move:
            res_id = move[0].main_auxiliary_id

        if not res_id:
            res_id = 0
        view_id = self.env.ref('ps_account.setup_ps_account_opening_auxiliary_wizard_form').id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Auxiliary Accounting'),
            'view_mode': 'form',
            'res_model': 'ps.sub.opening',
            'target': 'new',
            'res_id': res_id,
            'views': [[view_id, 'form']],
            'context': {'auxiliary_account_id': ps_id},
        }

    #视图按钮调用函数
    def create_new_account(self):
        rec = self.account_copy()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('ps_account.view_account_form_new').id,
            'target': 'current',
            'res_model': 'account.account',
            'res_id': rec.id,
            # 'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            'context': {'form_view_initial_mode': 'edit', 'force_detailed_view': True}
        }

    #获取编码规则
    def _get_account_rule(self):
        rule = self.env.user.company_id.ps_account_code_structure
        rul4 = self.env.user.company_id.ps_account_code_structure_l4
        rul5 = self.env.user.company_id.ps_account_code_structure_l5
        l = []
        if rule:
            if len(rule) == 5:
                if rul4:
                    if int(rul4) > 0:
                        rule = rule + '-' + rul4
                if rul5:
                    if int(rul5) > 0:
                        rule = rule + '-' + rul5
            rule = rule.split('-')
            for r in rule:
                l.append(int(r))
        else:
            l = [4, 3, 3]

        return l

    #生成子级或同级函数
    def account_copy(self):
        default = {}
        # accountcopy = self.env['ps.account.account.copy']
        rec = self.get_account_next()
        curr_lev = rec['newlev']#self.search([('id', '=', self.id)]).ps_account_level
        # print('创建时的级数：' + str(curr_lev))
        # parent_show_id = accountcopy.search([('copy_id', '=', rec['parent_id'])]).id
        parent_id = rec['parent_id']
        account_attribute_id = rec['account_attribute_id']
        user_type_id = rec['user_type_id']
        ps_balance_direction = rec['ps_balance_direction']
        reconcile = rec['reconcile']
        if curr_lev == 1:
            default = {
                'code': rec['newcode'],
                'name': rec['newname'],
                'ps_account_level': rec['newlev'],
                'account_attribute_id': account_attribute_id,
                'user_type_id': user_type_id,
                'ps_balance_direction': ps_balance_direction,
                'reconcile': reconcile
                }
        elif curr_lev > 1:
            aa = self.search([('id', '=', parent_id)])
            if aa:
                aa.write({'ps_is_leaf': False})  # 将当前父级是否为末级改为false
            default = {
                'code': rec['newcode'],
                'name': rec['newname'],
                'ps_account_level': rec['newlev'],
                'account_attribute_id': account_attribute_id,
                'user_type_id': user_type_id,
                'ps_balance_direction': ps_balance_direction,
                'parent_id': parent_id,
                'reconcile': reconcile
                # 'parent_show_id': parent_show_id
            }
        newrecord = self.create(default)
        # #科目复制表创建记录
        # newcopy = {'copy_id': newrecord.id, 'name': newrecord.name, 'code': newrecord.code}
        # accountcopy.create(newcopy)
        #返回创建的记录
        return newrecord

    #重写create函数
    @api.model
    def create(self, vals):
        rec = super(PsAccountAccount, self).create(vals)
        if rec.parent_id:
            self.search([('id', '=', rec.parent_id.id)]).write({'ps_is_leaf': False})  # 将当前父级是否为末级改为false
        return rec

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        first_period = self.env['ps.account.period'].search([], order='date_start', limit=1)
        if first_period.financial_state == '2':
            raise exceptions.ValidationError(_('期初会计期间已月结'))  # 期初会计期间已月结
        return super(PsAccountAccount, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    #重写unlink函数
    @api.multi
    def unlink(self):
        # ids = []
        par_ids = []
        for r in self:
            aa = self.search([('parent_id', '=', r.id)])
            if aa:
                raise exceptions.ValidationError(_('Subject【') + r.name + _('】has child subject，please delete the child subject first before deleting the subject.'))
            # ids.append(r.id)
            if r.parent_id:
                par_ids.append(r.parent_id.id)
        if len(par_ids):
            # delcopy = self.env['ps.account.account.copy']
            # delcopy.search([('copy_id', 'in', ids)]).unlink()
            res = super(PsAccountAccount, self).unlink()
            if len(par_ids):
                for r_id in par_ids:
                    aa = self.search([('parent_id', '=', r_id)])
                    if not aa:
                        self.search([('id', '=', r_id)]).write({'ps_is_leaf': True})
        else:
            res = super(PsAccountAccount, self).unlink()
        return res



#创建凭证编码流水表
class PsAccountDocumentNo(models.Model):
    _name = 'ps.account.document.no'
    _description = 'ps.account.document.no'

    company_id = fields.Many2one('res.company',  string='Company')
    year = fields.Char(string='Fiscal Year')
    period = fields.Char(string='Fiscal Period')
    voucher_name = fields.Char(string='Voucher Character')
    voucher_no = fields.Char( string='Voucher Number')
    date = fields.Date(string='Voucher Date')

    @api.model_cr
    def init(self):
        cr = self._cr
        cr.execute('Update ps_account_document_no Set company_id = %s Where company_id is null ', (self.env.user.company_id.id,))












