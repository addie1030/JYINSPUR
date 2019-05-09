# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.tools import ormcache

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ps_account_begin_use = fields.Boolean(string="Enable General Ledger")
    ps_account_begin_date = fields.Date(string="Activate Financial Date")
    ps_same_user_approval = fields.Boolean(string="The creator and reviewer can be the same person")
    ps_bank_must_record_or_not = fields.Boolean(string="Whether the bank class must record the settlement method and settlement number")
    ps_account_code_structure = fields.Char(string="Subject Encoding Structure")
    ps_account_code_structure_l4 = fields.Char(string="Subject Encoding Structure-level 4")
    ps_account_code_structure_l5 = fields.Char(string="Subject Encoding Structure-level 5")
    ps_account_profit_id = fields.Many2one('account.account', string="Current Profit Account",
                                           domain=lambda self: [('ps_is_leaf', '=', True)])
    ps_profit_loss_same_user_approval = fields.Boolean(string="Direct review of the vouchers created by profit and loss carryover")



    @api.onchange('ps_account_code_structure_l4', 'ps_account_code_structure_l5')
    def check_ps_account_code_structure_l4_ps_account_code_structure_l5(self):
        accs_lev_four = self.env['account.account'].search([('ps_account_level', '=', 4)])
        old_cs4 = self.env.user.company_id.ps_account_code_structure_l4
        old_cs5 = self.env.user.company_id.ps_account_code_structure_l5
        cs4 = self.ps_account_code_structure_l4
        if cs4:
            if cs4.isdigit():
                if accs_lev_four and int(self.ps_account_code_structure_l4) != int(old_cs4):
                    raise ValidationError(_('There are already level-4 subject in the chart of subject, thus the value cannot be changed.'))#科目表中已有4级科目，不能更改该值.
                if int(cs4) <= 0 or int(cs4) > 9:
                    raise ValidationError(_('Please enter the number between 0-9.'))
            else:
                raise ValidationError(_('Please enter the number.'))
        else:
            if accs_lev_four:
                raise ValidationError(_('There are already level-4 subject in the chart of subject, thus the value cannot be changed.'))#科目表中已有4级科目，不能更改该值.

        accs_lev_five = self.env['account.account'].search([('ps_account_level', '=', 5)])
        cs5 = self.ps_account_code_structure_l5
        if cs5:
            if cs5.isdigit():
                if accs_lev_five and int(self.ps_account_code_structure_l5) != int(old_cs5):
                    raise ValidationError(_('There are already level-5 subject in the chart of subject, thus the value cannot be changed.'))#科目表中已有5级科目，不能更改该值.
                if int(cs5) <= 0 or int(cs5) > 9:
                    raise ValidationError(_('Please enter the number between 0-9.'))
            else:
                raise ValidationError(_('Please enter the number.'))
        else:
            if accs_lev_five:
                raise ValidationError(_('There are already level-5 subject in the chart of subject, thus the value cannot be changed.'))#科目表中已有5级科目，不能更改该值.

    @api.multi
    def set_values(self):
        old_coa_template_id = self.company_id.chart_template_id
        super(ResConfigSettings, self).set_values()
        # add by 李有辙 切换科目模板时，如果切换到“2017小企业会计科目表”时，需要执行ps_account_account.xml文件
        if self.chart_template_id.name == '2017小企业会计科目表' and old_coa_template_id != self.chart_template_id:
            tools.convert_file(self._cr, 'ps_account', 'data/ps_account_account.xml', {}, 'init', False, 'data', 0)
            self._cr.commit()

            # 去掉多余的账簿类型
            self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id)]).unlink()
            # 只保留默认账簿类型
            JournalObj = self.env['account.journal']
            vals = {
                'type': 'general',
                'name': _('Default'),
                'code': _('Default'),
                'company_id': self.env.user.company_id.id,
                'show_on_dashboard': True,
                'color': False,
                'sequence': 1
            }
            JournalObj.create(vals)

            # 删除自动添加的两个科目10011、10021
            self.env['account.account'].search([('code', 'in', ['10011', '10021']),
                                                ('company_id', '=', self.env.user.company_id.id)]).unlink()
            self.env.user.company_id.ps_account_code_structure = '4-3-3'
            self.env.user.company_id.profit_loss_attribute_id = '5'
        self.env.user.company_id.ps_account_begin_use = self.ps_account_begin_use
        self.env.user.company_id.ps_account_begin_date = self.ps_account_begin_date
        self.env.user.company_id.ps_same_user_approval = self.ps_same_user_approval
        self.env.user.company_id.ps_bank_must_record_or_not = self.ps_bank_must_record_or_not
        self.env.user.company_id.ps_account_profit_id = self.ps_account_profit_id.id
        self.env.user.company_id.ps_account_code_structure_l4 = self.ps_account_code_structure_l4
        self.env.user.company_id.ps_account_code_structure_l5 = self.ps_account_code_structure_l5
        self.env.user.company_id.ps_profit_loss_same_user_approval = self.ps_profit_loss_same_user_approval


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            ps_account_begin_use=self.env.user.company_id.ps_account_begin_use,
            ps_account_begin_date=self.env.user.company_id.ps_account_begin_date,
            ps_same_user_approval=self.env.user.company_id.ps_same_user_approval,
            ps_bank_must_record_or_not=self.env.user.company_id.ps_bank_must_record_or_not,
            ps_account_code_structure=self.env.user.company_id.ps_account_code_structure,
            ps_account_profit_id=self.env.user.company_id.ps_account_profit_id.id,
            ps_account_code_structure_l4=self.env.user.company_id.ps_account_code_structure_l4,
            ps_account_code_structure_l5=self.env.user.company_id.ps_account_code_structure_l5,
            ps_profit_loss_same_user_approval=self.env.user.company_id.ps_profit_loss_same_user_approval
        )
        return res


class PsResCompany(models.Model):
    _inherit = 'res.company'

    ps_account_begin_use = fields.Boolean()#启用总账
    ps_account_begin_date = fields.Date()#财务启用日期
    ps_same_user_approval = fields.Boolean()#制单人和审核人可为同一人
    ps_bank_must_record_or_not = fields.Boolean(string="Whether the bank class must record the settlement method and settlement number")
    ps_account_code_structure = fields.Char()#科目编码结构
    ps_account_code_structure_l4 = fields.Char()#科目编码结构四级
    ps_account_code_structure_l5 = fields.Char()#科目编码结构五级
    ps_account_profit_id = fields.Many2one('account.account', domain=lambda self: [('ps_is_leaf', '=', True)])#本年利润科目
    profit_loss_attribute_id = fields.Char()#损益科目属性ID
    ps_current_fiscalyear = fields.Char()#当前会计期间: year + xx
    ps_profit_loss_same_user_approval = fields.Boolean()  # 损益结转生成的凭证直接审核

    @api.model
    def setting_init_fiscal_year_action(self):
        """ Called by the 'Fiscal Year Opening' button of the setup bar."""
        view_id = self.env.ref('ps_account.view_ps_account_fiscal_year_form').id
        rec = self.env['ps.account.period'].search([('financial_state', '=', '1')])
        if rec:
            res = self.env['ps.account.fiscalyear'].search([('id', '=', rec.fiscalyear_id.id)])
            if res:
                res_id = res.id
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Fiscal Year'),
                    'view_mode': 'form',
                    'res_model': 'ps.account.fiscalyear',
                    'target': 'new',
                    'res_id': res_id,
                    'views': [[view_id, 'form']],
                }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Fiscal Year'),
                'view_mode': 'form',
                'res_model': 'ps.account.fiscalyear',
                'target': 'new',
                'views': [[view_id, 'form']],
            }