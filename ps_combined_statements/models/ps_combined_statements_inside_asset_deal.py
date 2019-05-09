# -*- coding: utf-8 -*-
# Created by martin at 2018/11/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api


class CombinedStatementsInsideAssetDeal(models.Model):
	"""Long-term assets transactions within schedule """
	_name = 'ps.combined.statements.inside.asset.deal'
	_description = 'Long-term assets transactions within schedule '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The seller company ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The buyer of the company ')
	business_type = fields.Many2one(comodel_name='ps.combined.statements.business.type', string='Business types ')
	period = fields.Date(string='During the merger ')
	deal_day = fields.Date(string='Transaction date ')
	asset_code = fields.Char(string='Assets encoding ')
	asset_id = fields.Char(string='assets ')
	report_item = fields.Char(string='Report project expenses course ')
	taking_price = fields.Float(string='Operating income ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	taking_costs = fields.Float(string='Operating cost ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	taking_out_price = fields.Float(string='Non-operating income ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	taking_out_expenditure = fields.Float(string='Non-business expenses ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	unrealized_loss = fields.Float(string='Remaining unrealized internal profit and loss ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	depreciation = fields.Integer(string='Depreciable months ')
	depreciation_price = fields.Float(string='Month depreciation ', compute='_compute_depreciation_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	dispose_moth = fields.Integer(string='Handle months ')
	dispose_price = fields.Float(string='Is handling the unrealized profits and losses ', compute='_compute_dispose_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	change_data = fields.Date(string='Change the date ')
	change_type = fields.Many2one(comodel_name='ps.change.type', string='Change the type ')
	clear_data = fields.Date(string='Clean up the date ')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)

	@api.multi
	@api.depends('unrealized_loss', 'depreciation')
	def _compute_depreciation_price(self):
		"""Month depreciation calculation logic """
		for record in self:
			if record.depreciation > 0:
				record.depreciation_price = record.unrealized_loss / record.depreciation

	@api.multi
	@api.depends('depreciation_price', 'dispose_moth')
	def _compute_dispose_price(self):
		"""Is treatment of unrealized profit and loss calculation logic """
		for record in self:
			record.dispose_price = record.depreciation_price * record.dispose_moth

