# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models
from odoo import api
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

FIELDS_CREDIT_DEBIT = [
	('receivable', 'Accounts receivable '),
	('dividends_receivable', 'Dividends receivable '),
	('other_receivable', 'Other receivables '),
	('deposit_receivable', 'Deferred revenue '),
	('notes_receivable', 'Notes receivable '),
	('interest_receivable', 'Interest receivable '),
]
FIELD_FAMILAR_DEAL = ['taking_price', 'taking_costs', 'manage_costs', 'sell_costs']


class MergeEliminationEntryBuilder(models.TransientModel):
	"""Combine the offset entries generated """
	_name = "ps.merge.elimination.entry.builder.wizard"
	_rec_name = "merge_organization"

	account_period = fields.Date(string="Accounting period ", required=True)
	merge_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', required=True, string='Merging organizations ', domain=[('is_entity_company', '=', False)])
	elimination = fields.Many2many(comodel_name='ps.merge.elimination.entry.type', relation='merge_elimination_entry_builder_type_rel', column1='buil_wiz_id', column2='elimination_id', required=True, string='Offset type ')

	def builder_elimination_info(self):
		"""Processing offset data """
		entry_data = list()
		eliminations = [x.model for x in self.elimination]
		models = self.env['ir.model'].search([]).mapped('model')
		# Jax type 
		curr_period = str(self.account_period)[5:7]+'/'+str(self.account_period)[:4]
		# Whether offset type number set is correct 
		for elimination in eliminations:
			if elimination not in models:
				raise ValidationError('Offset type is  "{}" Set the number of errors '.format(self.env['ps.merge.elimination.entry.type'].search([('model', '=', elimination)]).name))
		# Get all the subjects 
		sub_contrasts = self.env['ps.combined.statements.merged.subject.contrast'].search([])

		for elimination in eliminations:
			el_data = list()
			dict_data = {elimination: el_data}
			domain = [('related_organization', '=', self.merge_organization.id)]
			domain_group = [('related_organization', '=', self.merge_organization.id), ('period', '=', curr_period)]
			display_field = ['investee_organization_id', 'investment_organization_id']
			group_field = ['investee_organization_id', 'investment_organization_id']
			# Obtain all meet the conditions of the data 
			result = self.env[elimination].sudo().search(domain)
			# The cash flow 
			if elimination == 'ps.combined.statements.inside.cash.detail':
				if result[0].eli_ids:
					raise ValidationError('Table name for  "{}" Offset entries have been generated cannot repeat generated '.format(self.elimination.filtered(lambda r: r.model == elimination).name))
				result_group = self.env[elimination].sudo().read_group(domain_group, ['investee_organization_id', 'investment_organization_id'], ['investee_organization_id', 'investment_organization_id'], lazy=False)
				dict_data[elimination] += self._process_builder_cash_detail(result.filtered(lambda r: r.period == curr_period), result_group, sub_contrasts)

			# Bonds are debt 
			if elimination == 'ps.combined.statements.inside.credit.debt':
				if result[0].eli_ids:
					raise ValidationError('Table name for  "{}" Offset entries have been generated cannot repeat generated '.format(self.elimination.filtered(lambda r: r.model == elimination).name))
				result_group = self.env[elimination].sudo().read_group(domain_group, display_field, group_field, lazy=False)
				dict_data[elimination] += self._process_builder_credit_debit(result.filtered(lambda r: r.period == curr_period), result_group, sub_contrasts)

			# Common trading 
			if elimination == 'ps.combined.statements.inside.familiar.deal':
				if result[0].eli_ids:
					raise ValidationError('Table name for  "{}" Offset entries have been generated cannot repeat generated '.format(self.elimination.filtered(lambda r: r.model == elimination).name))
				result_group = self.env[elimination].sudo().read_group(domain_group, display_field, group_field, lazy=False)
				dict_data[elimination] += self._process_builder_familiar_deal(result.filtered(lambda r: r.period == curr_period), result_group, sub_contrasts)

			# The equity method to adjust 
			if elimination == 'ps.subsidiary.profit.statement':
				# Find meet the conditions of all subsidiary profit information 
				subsidiary_ids = result.filtered(lambda r: r.period <= self.account_period)
				# Find the rights and interests class subjects 
				equity_id = self.env['ps.combined.statements.equity.contrast'].search([])
				# Find meet the conditions of investment table information ,One of the most recent data and get the current time 
				investment_id = self.env['ps.combined.statements.equity.investment'].search([('related_organization', '=', self.merge_organization.id), ('period', '<=', self.account_period)], order='period', limit=1)
				dict_data[elimination] += self._process_builder_subsidiary_profit(subsidiary_ids, equity_id, investment_id)
			# The owner's equity 
			entry_data.append(dict_data)
		# Write offset entry data 
		data_ids = []
		for entry in entry_data:
			tabe_ids = []
			for x in entry[entry.keys()[0]]:
				_logger.debug('Table name for  "{}"To build data :"{}"'.format(entry.keys()[0], x))
				res_id = self.env['ps.combined.statements.elimination.entry'].create(x)
				data_ids.append(res_id)
				tabe_ids.append(res_id.id)
			if entry.keys()[0] not in ['ps.subsidiary.profit.statement']:
				self.env[entry.keys()[0]].search([('related_organization', '=', self.merge_organization.id), ('period', '=', curr_period)]).write({'eli_ids': [(6, 0, tabe_ids)]})
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': self.env.ref('combined_statements.dialog_info_wizard').id,
			'target': 'new',
			'res_model': 'ps.dialog.info.wizard',
			'context': {'default_info': 'generate  "{}" The data '.format(len(data_ids)), 'model': 'ps.combined.statements.elimination.entry'}
		}

	# The rights and interests class offset entries generated 
	def _process_builder_subsidiary_profit(self, subsidiary_ids, equity_id, investment_id):
		"""
			The rights and interests class offset entries generated 
			:param subsidiary_ids: Subsidiary profit object
			:param equity_id: Rights and interests class subjects object
			:param investment_id: Investment table object
			:return: list
			"""
		data = list()
		# Achieve annual during the merger 
		period_year = self.account_period[:4]
		if not subsidiary_ids:
			raise ValidationError('Unit to profit statement ')
		if not equity_id:
			raise ValidationError('Rights and interests kind course control is not set  Please go to basic profile Settings ')
		if not investment_id:
			raise ValidationError('Investment table no relevant data ')

		curr_subsidiarys = subsidiary_ids.filtered(lambda r: period_year in r.period)  # Gets the current year's data 
		no_curr_subsidiarys = subsidiary_ids.filtered(lambda r: period_year not in r.period)  # To obtain the maximal data 
		if curr_subsidiarys:
			data.append(self._process_builder_subsidiary_profit_entry(
				[curr_subsidiarys[0].investment_organization_id.id, curr_subsidiarys[0].investee_organization_id.id],
				(sum(curr_subsidiarys.mapped('current_period_profit')) - sum(curr_subsidiarys.mapped('cur_cash_dividends'))) * investment_id.shareholding_ratio,
				equity_id.filtered(lambda r: r.category_id == 'cur_year' and r.ir_model_id.model == 'ps.subsidiary.profit.statement'),
				'Rights and interests class offset data '
			))
		if no_curr_subsidiarys:
			data.append(self._process_builder_subsidiary_profit_entry(
				[curr_subsidiarys[0].investment_organization_id.id, curr_subsidiarys[0].investee_organization_id.id],
				(sum(no_curr_subsidiarys.mapped('current_period_profit'))-sum(no_curr_subsidiarys.mapped('cur_cash_dividends'))) * investment_id.shareholding_ratio,
				equity_id.filtered(lambda r: r.category_id == 'span_year' and r.ir_model_id.model == 'ps.subsidiary.profit.statement'),
				'The maximal interests class offset data '
			))
		return data

	# Common trading 
	def _process_builder_familiar_deal(self, result, result_group, sub_contrasts):
		"""
			Build common transaction offset entry data 
			:param result: The data set 
			:param result_group: Packet data set 
			:param sub_contrasts: Subject contrast data 
			:return: list
			"""
		data = list()
		for x in result_group:
			# After get grouped data 
			xresult = result.filtered(lambda r: r.investee_organization_id.id == x['investee_organization_id'][0] and r.investment_organization_id.id == x['investment_organization_id'][0])
			# To obtain a reverse data 
			yresult = result.filtered(lambda r: r.investment_organization_id.id == x['investee_organization_id'][0] and r.investee_organization_id.id == x['investment_organization_id'][0])
			if not xresult or not yresult:
				continue
			# Comparison relationship matching subjects 
			sub_cons = sub_contrasts.filtered(lambda r: r.field_id.name in FIELD_FAMILAR_DEAL or r.field_id1.name in FIELD_FAMILAR_DEAL)
			for con in sub_cons:
				for_number = sum(yresult.mapped(con.field_id1.name)) if sum(xresult.mapped(con.field_id.name)) > sum(yresult.mapped(con.field_id1.name)) else sum(xresult.mapped(con.field_id.name))
				if for_number == 0:
					continue
				else:
					data.append(self._process_builder_elimination_entry(xresult, con, for_number, 'Common trading  "{}" Offset data '.format(con.field_id.field_description)))
		return data

	# The new traffic 
	def _process_builder_cash_detail(self, result, result_group, sub_contrasts):
		"""
			Build cash flow offset entry data 
			:param result: The data set 
			:param result_group: Packet data set 
			:param sub_contrasts: Subject contrast data 
			:return: list
			"""
		data = list()
		sub_cons = sub_contrasts.filtered(lambda r: r.ir_model_id.model == 'ps.combined.statements.inside.cash.detail')
		for con in sub_cons:
			for x in result_group:
				# After get grouped data 
				xresult = result.filtered(lambda r: r.investee_organization_id.id == x['investee_organization_id'][0] and r.investment_organization_id.id == x['investment_organization_id'][0] and r.cash_id.id == con.re_cash.id)
				# To obtain a reverse data 
				yresult = result.filtered(lambda r: r.investment_organization_id.id == x['investee_organization_id'][0] and r.investee_organization_id.id == x['investment_organization_id'][0] and r.cash_id.id == con.re_cash1.id)
				if not xresult or not yresult:
					continue
				# Comparison relationship matching subjects 
				for_number = sum(yresult.mapped('current_period_price')) if sum(xresult.mapped('current_period_price')) > sum(yresult.mapped('current_period_price')) else sum(xresult.mapped('current_period_price'))
				if for_number == 0:
					continue
				else:
					data.append(self._process_builder_elimination_entry(xresult, con, for_number, 'The cash flow to offset data '))
		return data

	# Creditor's rights debt 
	def _process_builder_credit_debit(self, result, result_group, sub_contrasts):
		"""
			Construction of creditor's rights debt offset entry data 
			:param result: The data set 
			:param result_group: Packet data set 
			:param sub_contrasts: Subject contrast data 
			:return: list
			"""
		data = list()
		for x in result_group:
			# After get grouped data 
			xresult = result.sudo().filtered(lambda r: r.investee_organization_id.id == x['investee_organization_id'][0] and r.investment_organization_id.id == x['investment_organization_id'][0])
			# To obtain a reverse data 
			yresult = result.sudo().filtered(lambda r: r.investment_organization_id.id == x['investee_organization_id'][0] and r.investee_organization_id.id == x['investment_organization_id'][0])
			if not xresult or not yresult:
				continue
			for field in FIELDS_CREDIT_DEBIT:
				# Comparison relationship matching subjects 
				sub_contrast = sub_contrasts.filtered(lambda r: r.field_id.name == field[0] or r.field_id1.name == field[0])
				# Determine subject control whether there is a control offset relations 
				if not sub_contrast or sub_contrast.field_id.name is False or sub_contrast.field_id1.name is False:
					raise ValidationError('Subjects in the table  "{}" Comparison relationship  Please go to course maintenance in the table '.format(field[1]))
				if len(sub_contrast) > 1:
					raise ValidationError('Subjects in the table  "{}"Repeated comparison relationship  Please go to course control standard maintenance  '.format(field[1]))
				for_number = sum(yresult.mapped(sub_contrast.field_id1.name)) if sum(xresult.mapped(sub_contrast.field_id.name)) > sum(yresult.mapped(sub_contrast.field_id1.name)) else sum(xresult.mapped(sub_contrast.field_id.name))
				if for_number == 0:
					continue
				else:
					data.append(self._process_builder_elimination_entry(xresult, sub_contrast, for_number, 'Creditors rights debt  "{}" Offset data '.format(field[1])))
		return data

	# Build offset entries 
	def _process_builder_elimination_entry(self, xresult, sub_contrast, for_number, label):
		"""
			Build offset entry data 
			:param xresult: With the company dimensions as a starting point 
			:param sub_contrast: Subject contrast relationship 
			:param for_number: To offset the amount 
			:param label: This paper shows that 
			:return: Offset entries dict
			"""
		elimination_line = list()
		# Build offset entries rows of data 
		for line in range(2):
			# Access to the subject 
			subject_id = sub_contrast.debit_subject.id if line == 0 else sub_contrast.credit_subject.id
			# Circular building offset entries rows of data 
			elimination_line.append([0, False, {
				'subject': subject_id,
				'label': label,
				'debit': for_number if sub_contrast.debit_subject.id == subject_id else 0.0,
				'credit': for_number if sub_contrast.credit_subject.id == subject_id else 0.0,
			}])
		# Build the offset data el_data
		return {
			'type': 'counteract',
			'line_ids': elimination_line,
			'state': 'draft',
			'date': self.account_period,
			'generation_type': 'system',
			'description': label,
			'ref_company': [(6, 0, [xresult[0].investment_organization_id.id, xresult[0].investee_organization_id.id])],
		}

	# The rights and interests class offset entries generated 
	def _process_builder_subsidiary_profit_entry(self, tulp, total_price, equity_id, label):
		"""
			Build equity offset entry data 
			:param total_price: Lenders amount 
			:param equity_id: Subject contrast relationship 
			:param label: This paper shows that 
			:return: Offset entries dict
			"""
		if not equity_id:
			raise ValidationError('Build equity offset entry data Cant find the subjects comparison relationship Please go to control maintenance rights and interests class subjects ')
		elimination_line = list()
		for line in range(2):
			# Access to the subject 
			subject_id = equity_id.debit_subject[0].id if line == 0 else equity_id.credit_subject[0].id
			# Circular building offset entries rows of data 
			elimination_line.append([0, False, {
				'subject': subject_id,
				'label': label,
				'debit': total_price if equity_id.debit_subject[0].id == subject_id else 0.0,
				'credit': total_price if equity_id.credit_subject[0].id == subject_id else 0.0,
			}])
		# Build the offset data el_data
		return {
			'type': 'counteract',
			'line_ids': elimination_line,
			'state': 'draft',
			'date': self.account_period,
			'generation_type': 'system',
			'description': label,
			'ref_company': [(6, 0, tulp)],
		}
