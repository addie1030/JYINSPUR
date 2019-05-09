# -*- coding: utf-8 -*-
# Created by martin at 2018/11/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _
from odoo.exceptions import AccessError


class CombinedStatementsInsideCashSetail(models.Model):
	"""Schedule of internal cash flow """
	_name = 'ps.combined.statements.inside.cash.detail'
	_description = 'Schedule of internal cash flow '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Our company ')
	period = fields.Char(string='During the merger ')
	cash_id = fields.Many2one(comodel_name='ps.core.value', string='The cash flow statement ')
	current_period_price = fields.Float(string='This amount ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)

	eli_ids = fields.Many2many(comodel_name='ps.combined.statements.elimination.entry', relation='statements_inside_cash_detail_entry_rel', column1='cash_id', column2='entry_id', string='Offset business ')

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
	def builder_inside_cash_detail(self, organization, period):
		"""
		Access to the internal cash flow statement 
		:param organization: The company organization 
		:param period: During the period of 
		:return: Boolean
		"""
		if not organization or not period:
			return {'status': True, 'message': _("Parameter is not correct ")}
		period_new = period[5:7]+'/'+period[0:4]
		result = self.env['ps.account.move.trade'].sudo().search([('src_code', '=', organization), ('period_id.code', '=', period_new)])
		res_groups = self.env['ps.account.move.trade'].sudo().read_group([('src_code', '=', organization), ('period_id.code', '=', period_new)], ['des_partner_id', 'src_partner_id'], ['des_partner_id'], lazy=False)
		organization_ids = self.env['ps.combined.statements.organization'].search([])
		if not result:
			return {'status': True, 'message': _("No data exist")}
		data = list()
		# For affiliates grouped data 
		for res_group in res_groups:
			# For affiliates group after the satisfaction of all associated companies credentials rows of data  And cash flow can not be empty
			code = self.env['res.partner'].sudo().browse(res_group['des_partner_id'][0]).sap_code
			for line in self.env['account.move.line'].sudo().read_group([('move_id', '=', [move.src_move_id.id for move in result.filtered(lambda r: r.des_partner_id.id == res_group['des_partner_id'][0])]),
															('cash_id', '!=', False)],
															['cash_id', 'debit', 'credit'], ['cash_id'], lazy=False):
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
					'investment_organization_id': investment_organization_id,  # Our company 
					'period': period_new,
					'investee_organization_id': investee_organization_id,  # Associated companies 
					'cash_id': line['cash_id'][0],
					'current_period_price': line['debit'] if line['credit'] == 0 else line['credit'],
				}
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