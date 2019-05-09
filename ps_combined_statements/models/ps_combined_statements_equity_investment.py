# -*- coding: utf-8 -*-
# Created by Jalena at 2018/10/9

import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning


class CombinedStatementsInvested(models.Model):
	"""Equity investment table """
	_name = 'ps.combined.statements.equity.investment'
	_description = 'Equity investment table '
	_rec_name = 'investee_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The investment company ')  # The investment company ID
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The invested company ')  # The invested company ID
	accounting_method = fields.Selection(string='A long-term equity investment accounting methods ', selection=[('cost-method', 'Cost method '), ('equity-method', 'The equity method ')], help='Long-term equity investment accounting method', default='equity-method')  # A long-term equity investment accounting methods
	# investment_day = fields.Date(string='Investment, ')  # Investment,
	period = fields.Date(string='Date of investment ')
	shareholding_ratio = fields.Float(string='Direct stake ', digits=dp.get_precision('Combined Statements Decimal'))  # Direct stake
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	book_value = fields.Float('The book value of long-term equity investment ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Book value of long-term equity investment')  # The book value of long-term equity investment
	impairment_preparation = fields.Float('The impairment of long-term equity investment ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Long-term equity investment impairment provision')  # The impairment of long-term equity investment
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)
	related_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ', compute='_compute_related_organization', store=True)  # This field is used to calculate the common superior offset business

	@api.depends('investee_organization_id', 'investment_organization_id')
	def _compute_related_organization(self):
		org_ids = {}
		if self.investee_organization_id and self.investment_organization_id:
			for company in self.investee_organization_id+self.investment_organization_id:
				org_ids[company.id] = list()
				org = company.parent_id
				while org:
					org_ids[company.id].append(org.id)
					org = org.parent_id
		if org_ids:
			# Jax Type conversion 
			for x in list(org_ids.values())[0]:
				for y in list(org_ids.values())[1]:
					if x == y:
						self.related_organization = x
						return True


class CombinedStatementsInvestedReverse(models.Model):
	"""The invested table """
	_name = 'ps.combined.statements.equity.investment.reverse'
	_description = 'The invested table '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The invested company ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The investment company ')
	investment_day = fields.Date(string='Investment, ')
	paid_in_capital = fields.Float(string='Paid-in capital ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Paid-in Capital')
	capital_reserves = fields.Float(string='Capital reserves ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Capital Reserves')
	surplus_reserve = fields.Float(string='Surplus reserves ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Surplus Reserve')
	undistributed_profits = fields.Float(string='Undistributed profit ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Undistributed Profits')
	treasury_stock = fields.Float(string='Treasury stock ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='Treasury Stock')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)


class SubsidiaryProfitStatement(models.Model):
	"""Subsidiary of the income statement """
	_name = 'ps.subsidiary.profit.statement'
	_description = 'Subsidiary of the income statement '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The invested company ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The investment company ')
	investment_day = fields.Date(string='Investment, ')
	period = fields.Date(string='During the merger ')
	current_period_profit = fields.Float(string='The current profit ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	cur_cash_dividends = fields.Float(string='This issue has been declared the cash dividend distribution ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='This issue has been declared the cash dividend distribution ')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)
	cre_type = fields.Selection(string='The data type ', selection=[('bedin', 'At the beginning '), ('cur', 'In this issue '), ], default='cur')

	related_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ', compute='_compute_related_organization', store=True)  # This field is used to calculate the common superior offset business

	@api.depends('investee_organization_id', 'investment_organization_id')
	def _compute_related_organization(self):
		org_ids = {}
		if self.investee_organization_id and self.investment_organization_id:
			for company in self.investee_organization_id+self.investment_organization_id:
				org_ids[company.id] = list()
				org = company.parent_id
				while org:
					org_ids[company.id].append(org.id)
					org = org.parent_id
		if org_ids:
			# Jax list(dict_values)
			for x in list(org_ids.values())[0]:
				if len(list(org_ids.values())) > 1:
					for y in list(org_ids.values())[1]:
						if x == y:
							self.related_organization = x
							return True
				else:
					raise ValidationError(_('An investment company cannot be the same as an invested company.'))


class ChangeType(models.Model):
	"""Change the type """
	_name = 'ps.change.type'
	_description = 'Change the type '

	name = fields.Char(string='The name of the ')
	code = fields.Char(string='Serial number ')
	_sql_constraints = [('code_name_uniq', 'unique (code,name)', 'Code name already exists ')]


