# -*- coding: utf-8 -*-
# Created by martin at 2018/11/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api


class CombinedStatementsInsideIncentoryDeal(models.Model):
	"""Inventory transactions within schedule """
	_name = 'combined.statements.inside.inventory.deal'
	_description = 'Inventory transactions within schedule '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The seller company ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='The buyer of the company ')
	business_type = fields.Many2one(comodel_name='ps.combined.statements.business.type', string='Business types ')
	period = fields.Date(string='During the merger ')
	deal_day = fields.Date(string='Transaction date ')
	taking_price = fields.Float(string='Operating income ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	taking_costs = fields.Float(string='Operating cost ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	unloss_price = fields.Float(string='This period did not achieve the internal profit and loss ', compute='_compute_unloss_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	prior_unloss_price = fields.Float(string='Across the years remaining unrealized internal gains and losses of the previous period ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	curr_realize_price = fields.Float(string='This period has been realized ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	curr_remain_price = fields.Float(string='In this issue of retained ', compute='_compute_curr_remain_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	ago_unloss_price = fields.Float(string='Previous year remaining unrealized internal profit and loss ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	ago_loss_price = fields.Float(string='Previous year has been implemented for this issue ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	ago_remain_price = fields.Float(string='The retained the previous year ', compute='_compute_ago_remain_price', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'), )
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)

	@api.multi
	@api.depends('ago_unloss_price', 'ago_loss_price')
	def _compute_ago_remain_price(self):
		"""Previous calculation logic is retained """
		for record in self:
			record.ago_remain_price = record.ago_unloss_price - record.ago_loss_price

	@api.multi
	@api.depends('taking_price', 'taking_costs')
	def _compute_unloss_price(self):
		"""Current unrealized profit and loss calculation within """
		for record in self:
			record.unloss_price = record.taking_price-record.taking_costs

	@api.multi
	@api.depends('unloss_price', 'prior_unloss_price', 'curr_realize_price')
	def _compute_curr_remain_price(self):
		"""Retained in current calculation """
		for record in self:
			record.curr_remain_price = record.unloss_price +record.prior_unloss_price -record.curr_realize_price