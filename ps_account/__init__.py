# -*- coding: utf-8 -*-

from . import models
from . import wizard
from . import controller
from . import reports

import logging

from odoo import api, SUPERUSER_ID
from odoo.api import Environment

_logger = logging.getLogger(__name__)

def pre_init_hook(cr):
	env = Environment(cr, SUPERUSER_ID, {})
	# 因l10n_cn_small_business模块自动安装，但预置的数据不符合需要，需要删除该模块预置的数据，然后重新安装我们自己预置的数据
	# 1、删除关联
	sql = "update account_tax set account_id=NULL, refund_account_id=NULL"
	env.cr.execute(sql)
	sql = "update account_journal set default_credit_account_id=NULL,default_debit_account_id=NULL"
	env.cr.execute(sql)
	# 2、删除数据
	sql = "delete from account_account"
	env.cr.execute(sql)
	sql = "delete from account_journal"
	env.cr.execute(sql)
	sql = "delete from account_tax"
	env.cr.execute(sql)

# 'menu_finance_receivables','menu_finance_payables',
def post_init_hook(cr, registry):
	# 隐藏Sales、Purchases、Reporting、Adviser->Action/Management/菜单、配置中的银行账户和税率设置和替换规则
	env = Environment(cr, SUPERUSER_ID, {})
	menu_list = ['menu_finance_reports', 'menu_finance_entries_actions'
		 ,'menu_action_account_bank_journal_form',
		 'menu_action_account_fiscal_position_form', 'menu_action_tax_form']
	res_ids = env['ir.model.data'].search([
		('model', '=', 'ir.ui.menu'),
		('module', '=', 'account'),
		('name', 'in', menu_list)
		]).mapped('res_id')
	env['ir.ui.menu'].browse(res_ids).update({'active': False})

	# 去掉account.move.line表上不允许录入负数的约束
	env.cr.execute(
		"SELECT constraint_name from information_schema.table_constraints where table_name='account_move_line' and constraint_name = %s",
		('account_move_line_credit_debit2',))
	if cr.fetchone():
		cr.execute('alter table account_move_line DROP CONSTRAINT account_move_line_credit_debit2')

	# 自动安装报表，行号，2017会计科目表
	module_list = []
	# module_list.append('account_statement')
	module_list.append('rowno_in_tree')
	module_list.append('l10n_cn_small_business2017')
	env = api.Environment(cr, SUPERUSER_ID, {})
	module_ids = env['ir.module.module'].search([('name', 'in', module_list), ('state', '=', 'uninstalled')])
	module_ids.sudo().button_install()
