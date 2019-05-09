# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_setup_switch_coa_done = fields.Boolean(string=_('Subject switching marks are completed.'), related='company_id.account_setup_switch_coa_done')

    @api.multi
    def _existing_accounting(self, company_id):
        model_to_check = ['account.move.line', 'account.invoice', 'account.move', 'account.payment', 'account.bank.statement']
        for model in model_to_check:
            if len(self.env[model].search([('company_id', '=', company_id.id)])) > 0:
                return True
        return False

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
	        account_setup_switch_coa_done = self.env.user.company_id.account_setup_switch_coa_done,
	        chart_template_id = self.env.user.company_id.chart_template_id.id,
	        has_accounting_entries = self._existing_accounting(self.env.user.company_id),
        )
        return res

    def mark_switch_coa_as_done(self):
        self.company_id.account_setup_switch_coa_done = True
        self.set_values()

    def unmark_switch_coa_as_done(self):
        self.company_id.account_setup_switch_coa_done = False

class PsAccountFiscalYear(models.Model):
    _inherit = "ps.account.fiscalyear"

    account_setup_fiscalyear_period_done = fields.Boolean(string=_('Period marked completion'), related='company_id.account_setup_fiscalyear_period_done')

    def mark_fiscalyear_period_setup_as_done_action(self):
        """ Marks the 'bank setup' step as done in the setup bar and in the company."""
        self.company_id.account_setup_fiscalyear_period_done = True


    def unmark_fiscalyear_period_setup_as_done_action(self):
        """ Marks the 'bank setup' step as not done in the setup bar and in the company."""
        self.company_id.account_setup_fiscalyear_period_done = False

class ResCompany(models.Model):
    _inherit = "res.company"

    # Fields marking the completion of a setup step
    account_setup_fiscalyear_period_done = fields.Boolean(string=_('Financial Year Setup Marked As Done'),
                                                help=_("Initial account fiscalyear and period."))
    account_setup_switch_coa_done = fields.Boolean(string=_('Chart of Account Checked'),
                                            help=_("Switch chart of account to satisfy the needs of the enterprise"))

    @api.model
    def action_setup_fiscalyear_period_done(self):
	    """ Called by the 'Fiscal Year Opening' button of the setup bar."""
	    company = self.env.user.company_id
	    new_wizard = self.env['account.financial.year.op'].create({'company_id': company.id})
	    view_id = self.env.ref('account.setup_financial_year_opening_form').id

	    return {
		    'type': 'ir.actions.act_window',
		    'name': _('Fiscal Year'),
		    'view_mode': 'form',
		    'res_model': 'account.financial.year.op',
		    'target': 'new',
		    'res_id': new_wizard.id,
		    'views': [[view_id, 'form']],
	    }

    @api.model
    def switch_chart_of_accounts_action(self):
        """由设置工具条上的‘切换科目’按钮调用"""
        company = self.env.user.company_id
        view_id = self.env.ref('ps_account.setup_switch_coa_form').id

        # domain = [('user_type_id', '!=', self.env.ref('account.data_unaffected_earnings').id), ('company_id','=', company.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Subject setting'),
            'view_mode': 'form',
            'res_model': 'res.config.settings',
            'target': 'new',
            'views': [[view_id, 'form']],
        }

    @api.model
    def setting_init_fiscal_year_period_action(self):
        """由设置工具条上的 '会计期间'按钮调用"""
        company = self.env.user.company_id
        view_id = self.env.ref('ps_account.setup_account_year_period_form').id
        res = {
            'type': 'ir.actions.act_window',
            'name': _('Accounting Period'),
            'view_mode': 'form',
            'res_model': 'ps.account.fiscalyear',
            'target': 'new',
            'views': [[view_id, 'form']],
        }
        # 如果已有会计区间，则打开，允许编辑.
        # 没有，则打开页面，并在新建状态.
        fiscal_year = self.env['ps.account.fiscalyear'].search([('company_id','=', company.id)], limit=1)
        if fiscal_year:
            res['res_id'] = fiscal_year.id
        return res

    @api.model
    def setting_account_initial_balance_action(self):
        """由设置工具条上的 '余额初始'按钮调用"""
        company = self.env.user.company_id
        view_id = self.env.ref('ps_account.init_accounts_tree_new').id
        res = {
            'type': 'ir.actions.act_window',
            'name': _('Initial balance'),
            'view_mode': 'tree',
            'res_model': 'account.account',
            # 'target': 'new',
            'views': [[view_id, 'list']],
        }
        return res