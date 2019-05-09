# -*- coding: utf-8 -*-
# Created by Jalena at 2018/10/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api


class CombinedStatementsFairValueDifference(models.Model):
	"""The fair value difference table """
	_name = 'ps.combined.statements.fair.value.difference'
	_description = 'The fair value difference table '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The invested company ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The investment company ')
	investment_day = fields.Date(string='Investment, ')
	period = fields.Date(string='During the merger ')
	adjustment_item = fields.Selection(string='Adjust the item ', selection=[('fixed_assets', 'Fixed assets '), ('intangible_assets', 'Intangible assets '), ('rest', 'other '), ], default='fixed_assets')
	asset_code = fields.Char(string='Assets encoding ')
	# asset_id = fields.Many2one('account.asset.asset', string='assets ')
	asset_id = fields.Char(string='assets ')
	fair_value = fields.Float(string='The fair value ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='fair value')
	book_value = fields.Float(string='Book value ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), help='book value')
	balance = fields.Float(string='The remaining balance ', compute='_compute_balance', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	depreciation = fields.Integer(string='Depreciable months ')
	depreciation_price = fields.Float(string='Month depreciation ', compute='_compute_depreciation_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	dispose_moth = fields.Integer(string='Handle months ')
	dispose_price = fields.Float(string='Handle the difference ', compute='_compute_dispose_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	change_data = fields.Date(string='Change the date ')
	change_type = fields.Many2one(comodel_name='ps.change.type', string='Change the type ')
	clear_data = fields.Date(string='Clean up the date ')
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)

	@api.multi
	@api.depends('balance', 'depreciation', 'dispose_moth')
	def _compute_dispose_price(self):
		"""Processing the balance calculation logic """
		for record in self:
			if record.depreciation > 0:
				record.dispose_price = (record.balance / record.depreciation) * record.dispose_moth
			else:
				record.dispose_price = (record.balance / 1) * record.dispose_moth

	@api.multi
	@api.depends('balance', 'depreciation')
	def _compute_depreciation_price(self):
		"""Month depreciation calculation logic """
		for record in self:
			if record.depreciation > 0:
				record.depreciation_price = record.balance / record.depreciation

	@api.multi
	@api.depends('fair_value', 'book_value')
	def _compute_balance(self):
		"""To compute the difference logic """
		for record in self:
			record.balance = record.fair_value-record.book_value

