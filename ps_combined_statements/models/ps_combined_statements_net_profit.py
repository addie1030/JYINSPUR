# -*- coding: utf-8 -*-
# Created by Jalena at 2018/10/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models


class CombinedStatementsNetProfit(models.Model):
	"""The subsidiary net profit table """
	_name = 'ps.combined.statements.net.profit'

	# TODO Using the new model  ps.subsidiary.profit.statement
	active = fields.Boolean(string='Active', default=True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='investment company')  # The investment company ID
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Investee companies')  # The invested company ID
	investment_day = fields.Date(string='Investment day')  # The invested, 
	period_id = fields.Date(string='During the period of ')
	net_profit = fields.Float(string='Net profit', digits=dp.get_precision('Combined Statements Decimal'))  # Net profit 
	cash_dividend = fields.Float(string='Net profit', digits=dp.get_precision('Combined Statements Decimal'), help='Declared cash dividends distributed')  # Is the cash dividend distribution 
