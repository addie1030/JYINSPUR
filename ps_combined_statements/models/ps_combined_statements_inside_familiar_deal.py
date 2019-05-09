# -*- coding: utf-8 -*-
# Created by martin at 2018/11/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class CombinedStatementsInsideFamiliarDeal(models.Model):
	"""Common transactions within tables """
	_name = 'ps.combined.statements.inside.familiar.deal'
	_description = 'Common transactions within tables '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Our company ')
	period = fields.Char(string='During the merger ')
	taking_price = fields.Float(string='Operating income ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	taking_costs = fields.Float(string='Operating cost ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	manage_costs = fields.Float(string='Management fees ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	sell_costs = fields.Float(string='Cost of sales ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))

	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)
	eli_ids = fields.Many2many(comodel_name='ps.combined.statements.elimination.entry', relation='statements_inside_familiar_deal_entry_rel', column1='deal_id', column2='entry_id', string='Offset business ')
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
			for x in org_ids.values()[0]:
				for y in org_ids.values()[1]:
					if x == y:
						self.related_organization = x
						return True

	@api.model
	def build_inside_familiar_deal(self, organization, period):
		"""
			Access to the internal common transaction table 
			:param organization: The company organization 
			:param period: During the period of 
			:return: Boolean
			"""

		def _get_banlance(line):
			"""
			According to the proof obtain amount balance data 
			:param line: Proof of line odject
			:return: Float
			"""
			return line.debit-line.credit if line.account_id.balance_direction == 'debit' else line.credit-line.debit

		if not organization or not period:
			return {'status': True, 'message': _("Parameter is not correct ")}
		period_new = period[5:7]+'/'+period[0:4]
		result = self.env['ps.account.move.trade'].sudo().search([('src_code', '=', organization), ('period_id.code', '=', period_new)])
		res_groups = self.env['ps.account.move.trade'].sudo().read_group([('src_code', '=', organization), ('period_id.code', '=', period_new)], ['des_partner_id', 'type_id'], ['des_partner_id', 'type_id'], lazy=False)
		organization_ids = self.env['ps.combined.statements.organization'].search([])
		if not result:
			return {'status': True, 'message': _("No data exist")}
		data = list()
		for res_group in res_groups:
			code = self.env['res.partner'].sudo().browse(res_group['des_partner_id'][0]).sap_code
			investment_organization_id = organization_ids.filtered(lambda r: r.code == organization).id  # Our company 
			investee_organization_id = organization_ids.filtered(lambda r: r.code == code).id  # Associated companies 
			record = self.search([
				('investment_organization_id', '=', investment_organization_id),
				('period', '=', period_new),
				('investee_organization_id', '=', investee_organization_id)
			])
			# If the existing data out of the building of the current data 
			if record.exists():
				continue
			info = {
				'investment_organization_id': investment_organization_id,
				'period': period_new,
				'investee_organization_id': investee_organization_id,
				'taking_price': 0.0,  # 6001+6051
				'taking_costs': 0.0,  # 6401+ 6402
				'manage_costs': 0.0,  # 6602
				'sell_costs': 0.0,  # 6601
			}
			for x in result.filtered(lambda r: r.des_partner_id.id == res_group['des_partner_id'][0]):
				for line in x.src_move_id.line_ids:
					if '6001' in line.account_id.code or '6051' in line.account_id.code:
						info['taking_price'] += _get_banlance(line)
					elif '6401' in line.account_id.code or '6402' in line.account_id.code:
						info['taking_costs'] += _get_banlance(line)
					elif '6602' in line.account_id.code:
						info['manage_costs'] += _get_banlance(line)
					elif '6601' in line.account_id.code:
						info['sell_costs'] += _get_banlance(line)
			data.append(info)
		try:
			tulp = []
			for x in data:
				res_id = self.create(x)
				tulp.append(res_id)
			if len(tulp) > 0:
				return {'status': True, 'message': _("Successfully created '{}'records ").format(len(tulp), )}
			else:
				return {'status': False, 'message': _("Create a failure ")}
		except AccessError:
			return {'status': False, 'message': _("Create a failure You do not have permission ")}


class CombinedStatementsBusinessType(models.Model):
	"""Business types """
	_name = 'ps.combined.statements.business.type'
	_description = 'Business types '

	name = fields.Char(string='The name of the ')
	code = fields.Char(string='Serial number ')
	_sql_constraints = [('code_name_uniq', 'unique (code,name)', 'Code name already exists ')]
