# -*- coding: utf-8 -*-
# Created by martin at 2018/11/18
import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _

from odoo.exceptions import AccessError

FIELDS_CREDIT_DEBIT = [
	('receivable', 'Accounts receivable ', 'payable', 'Accounts payable '),
	('dividends_receivable', 'Dividends receivable ', 'dividends_payable', 'Dividends payable '),
	('other_receivable', 'Other receivables ', 'other_payable', 'Other to cope with '),
	('deposit_receivable', 'Deferred revenue ', 'deposit_payable', 'Advance payment '),
	('notes_receivable', 'Notes receivable ', 'notes_payable', 'Notes payable '),
	('interest_receivable', 'Interest receivable ', 'interest_payable', 'Interest payable '),
]


class CombinedStatementsInsideCreditDebt(models.Model):
	"""Internal creditor's rights debt table """
	_name = 'ps.combined.statements.inside.credit.debt'
	_description = 'Internal creditors rights debt table '
	_rec_name = 'investment_organization_id'

	active = fields.Boolean(string='Active', default=True)
	investee_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ')
	investment_organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Our company ')
	cre_type = fields.Selection(string='Debt type ', selection=[('bedin', 'At the beginning '), ('cur', 'In this issue '), ], default='cur')
	period = fields.Char(string='During the merger ')

	receivable = fields.Float(string='Accounts receivable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	dividends_receivable = fields.Float(string='Dividends receivable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	other_receivable = fields.Float(string='Other receivables ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	deposit_receivable = fields.Float(string='Deferred revenue ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	notes_receivable = fields.Float(string='Notes receivable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	interest_receivable = fields.Float(string='Interest receivable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	payable = fields.Float(string='Accounts payable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	dividends_payable = fields.Float(string='Dividends payable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	other_payable = fields.Float(string='Other to cope with ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	deposit_payable = fields.Float(string='Advance payment ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	notes_payable = fields.Float(string='Notes payable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	interest_payable = fields.Float(string='Interest payable ', currency_field='currency_id', digits=dp.get_precision('Combined Statements Decimal'))
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)
	eli_ids = fields.Many2many(comodel_name='ps.combined.statements.elimination.entry', relation='statements_inside_credit_debt_entry_rel', column1='cre_debit_id', column2='entry_id', string='Offset business ')

	related_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ', compute='_compute_related_organization', store=True)  # This field is used to calculate the common superior offset business

	@api.depends('investee_organization_id', 'investment_organization_id')
	def _compute_related_organization(self):
		org_ids = {}
		if self.investee_organization_id and self.investment_organization_id:
			for company in self.investee_organization_id + self.investment_organization_id:
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
	def build_inside_credit_debit(self, organization, period):
		"""
		Access to the internal table of creditor's rights debt 
		:param organization: The company organization 
		:param period: During the period of 
		:return: Boolean
		"""
		if not organization or not period:
			return {'status': True, 'message': _("Parameter is not correct ")}

		def _get_banlance(line):
			"""
			According to the proof obtain amount balance data 
			:param line: Proof of line odject
			:return: Float
			"""
			return line.debit-line.credit if line.account_id.balance_direction == 'debit' else line.credit-line.debit

		period_new = period[5:7]+'/'+period[0:4]
		result = self.env['ps.account.move.trade'].sudo().search([('src_code', '=', organization), ('period_id.code', '=', period_new)])
		res_groups = self.env['ps.account.move.trade'].sudo().read_group([('src_code', '=', organization), ('period_id.code', '=', period_new)], ['des_partner_id'], ['des_partner_id'], lazy=False)
		organization_ids = self.env['ps.combined.statements.organization'].search([])
		if not result:
			return {'status': True, 'message': _("No data exist ")}
		data = list()
		for res_group in res_groups:
			code = self.env['res.partner'].sudo().browse(res_group['des_partner_id'][0]).sap_code	 # Retrieves associated company number 
			investment_organization_id = organization_ids.filtered(lambda r: r.code == organization).id   # Our company 
			investee_organization_id = organization_ids.filtered(lambda r: r.code == code).id  # Associated companies 
			record = self.search([
				('investment_organization_id', '=', investment_organization_id),
				('period', '=', period_new),
				('investee_organization_id', '=', investee_organization_id),
				('cre_type', '=', 'cur')
			])
			# If the existing data out of the building of the current data 
			if record.exists():
				continue
			info = {
				'investment_organization_id': investment_organization_id,
				'period': period_new,
				'investee_organization_id': investee_organization_id,
				'cre_type': 'cur',
				'receivable': 0.0,  # 1122
				'dividends_receivable': 0.0,  # 1131
				'other_receivable': 0.0,  # 1221
				'deposit_receivable': 0.0,  # 2203
				'notes_receivable': 0.0,  # 1121
				'interest_receivable': 0.0,  # 1132
				'payable': 0.0,  # 2202
				'dividends_payable': 0.0,  # 2232
				'other_payable': 0.0,  # 2241
				'deposit_payable': 0.0,  # 1123
				'notes_payable': 0.0,  # 2201
				'interest_payable': 0.0  # 2231
			}
			for x in result.filtered(lambda r: r.des_partner_id.id == res_group['des_partner_id'][0]):
				for line in x.src_move_id.line_ids:
					if '1122' in line.account_id.code:
						info['receivable'] += _get_banlance(line)
					elif '1131' in line.account_id.code:
						info['dividends_receivable'] += _get_banlance(line)
					elif '1221' in line.account_id.code:
						info['other_receivable'] += _get_banlance(line)
					elif '2203' in line.account_id.code:
						info['deposit_receivable'] += _get_banlance(line)
					elif '1121' in line.account_id.code:
						info['notes_receivable'] += _get_banlance(line)
					elif '1132' in line.account_id.code:
						info['interest_receivable'] += _get_banlance(line)
					elif '2202' in line.account_id.code:
						info['payable'] += _get_banlance(line)
					elif '2232' in line.account_id.code:
						info['dividends_payable'] += _get_banlance(line)
					elif '2241' in line.account_id.code:
						info['other_payable'] += _get_banlance(line)
					elif '1123' in line.account_id.code:
						info['deposit_payable'] += _get_banlance(line)
					elif '2201' in line.account_id.code:
						info['notes_payable'] += _get_banlance(line)
					elif '2231' in line.account_id.code:
						info['interest_payable'] += _get_banlance(line)
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

	@api.model
	def carry_inside_credit_debit(self, organization, period, carry_period, is_all):
		"""
			Internal creditor's rights debt table at the beginning of carry forward 
			:param organization: The company organization 
			:param period: During the period of 
			:param carry_period: During the period of carry forward 
			:param is_all: Carry forward all the company logo 
			:return: Boolean
			"""
		if not organization or not period or not carry_period:
			return {'status': True, 'message': _("Parameter is not correct ")}
		period_new = period[5:7]+'/'+period[0:4]
		organization_id = self.env['ps.combined.statements.organization'].search([('code', '=', organization)])
		# if is_allIs true, carry forward all entities 
		data = list()
		if is_all:
			result = self.read_group([('period', '=', period_new)],
									['investment_organization_id', 'period', 'investee_organization_id', 'receivable', 'dividends_receivable', 'other_receivable',
									'deposit_receivable', 'notes_receivable', 'interest_receivable', 'payable', 'dividends_payable', 'other_payable',
									'deposit_payable', 'notes_payable', 'interest_payable', ],
									['investment_organization_id', 'investee_organization_id'], lazy=False)
		else:
			result = self.read_group([('period', '=', period_new), ('investment_organization_id', '=', organization_id.id)],
									['investment_organization_id', 'period', 'investee_organization_id', 'receivable', 'dividends_receivable', 'other_receivable',
									'deposit_receivable', 'notes_receivable', 'interest_receivable', 'payable', 'dividends_payable', 'other_payable',
									'deposit_payable', 'notes_payable', 'interest_payable', ],
									['investment_organization_id', 'investee_organization_id'], lazy=False)
		if not result:
			return {'status': True, 'message': _("There is no data ")}
		for x in result:
			record = self.search([
				('investment_organization_id', '=', x['investment_organization_id'][0]),
				('period', '=', carry_period[5:7]+'/'+carry_period[0:4]),
				('investee_organization_id', '=', x['investee_organization_id'][0]),
				('cre_type', '=', 'bedin')
			])
			# If the existing data out of the building of the current data 
			if record.exists():
				continue
			info = {
				'investment_organization_id': x['investment_organization_id'][0],
				'period': carry_period[5:7]+'/'+carry_period[0:4],
				'investee_organization_id': x['investee_organization_id'][0],
				'cre_type': 'bedin',
				'receivable': x['receivable'],  # 1122
				'dividends_receivable': x['dividends_receivable'],  # 1131
				'other_receivable': x['other_receivable'],  # 1221
				'deposit_receivable': x['deposit_receivable'],  # 2203
				'notes_receivable': x['notes_receivable'],  # 1121
				'interest_receivable': x['interest_receivable'],  # 1132
				'payable': x['payable'],  # 2202
				'dividends_payable': x['dividends_payable'],  # 2232
				'other_payable': x['other_payable'],  # 2241
				'deposit_payable': x['deposit_payable'],  # 1123
				'notes_payable': x['notes_payable'],  # 2201
				'interest_payable': x['interest_payable']  # 2231
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
				return {'status': False, 'message': _("Create a failure :There may be a reason why the data has been carried forward ")}
		except AccessError:
			return {'status': False, 'message': _("Create a failure You do not have permission ")}

	@api.model
	def check_inside_credit_debit(self, organization, period):
		"""
			Access to the internal table of creditor's rights debt reconciliation results 
			:param organization: The company organization (Virtual organization )
			:param period: During the period of 
			:return: Boolean
			"""
		if not organization or not period:
			return {'status': True, 'message': _("Parameter is not correct ")}
		check_infos = list()
		period_new = period[5:7]+'/'+period[0:4]
		organization_id = self.env['ps.combined.statements.organization'].search([('code', '=', organization)])
		result = self.search([('period', '=', period_new), ('related_organization', '=', organization_id.id)])
		result_group = self.read_group([('period', '=', period_new), ('related_organization', '=', organization_id.id)],
								['investment_organization_id', 'period', 'investee_organization_id', 'receivable', 'dividends_receivable', 'other_receivable',
								'deposit_receivable', 'notes_receivable', 'interest_receivable', 'payable', 'dividends_payable', 'other_payable',
								'deposit_payable', 'notes_payable', 'interest_payable', ],
								['investment_organization_id', 'investee_organization_id'], lazy=False)
		for x in result_group:
			# After get grouped data 
			xresult = result.sudo().filtered(lambda r: r.investee_organization_id.id == x['investee_organization_id'][0] and r.investment_organization_id.id == x['investment_organization_id'][0])
			# To obtain a reverse data 
			yresult = result.sudo().filtered(lambda r: r.investment_organization_id.id == x['investee_organization_id'][0] and r.investee_organization_id.id == x['investment_organization_id'][0])
			if not xresult or not yresult:
				continue

			for field in FIELDS_CREDIT_DEBIT:
				if sum(xresult.mapped(field[0])) != sum(yresult.mapped(field[2])):
					check_infos.append({
						'period': period_new,
						'investment_organization_id': x['investment_organization_id'][1],
						'investee_organization_id': x['investee_organization_id'][1],
						'X_field': field[1],
						'X_field_price': sum(xresult.mapped(field[0])),
						'investment_organization_id1': x['investee_organization_id'][1],
						'investee_organization_id2': x['investment_organization_id'][1],
						'y_field': field[3],
						'y_field_price': sum(yresult.mapped(field[2])),
					})
		return check_infos



