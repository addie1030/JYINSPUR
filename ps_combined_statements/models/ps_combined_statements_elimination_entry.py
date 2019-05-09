# -*- coding: utf-8 -*-
# Created by Jalena at 2018/10/17

from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError, AccessError


class CombinedStatementsEliminationEntry(models.Model):
	"""Offset entries """
	_name = "ps.combined.statements.elimination.entry"
	_rec_name = "code"
	_description = "elimination entry"
	_order = "date desc, id desc"

	@api.one
	@api.depends("company_id")
	def _compute_currency(self):
		self.currency_id = self.company_id.currency_id or self.env.user.company_id.currency_id

	@api.multi
	@api.depends('line_ids.debit', 'line_ids.credit')
	def _amount_compute(self):
		for move in self:
			total = 0.0
			for line in move.line_ids:
				total += line.debit
			move.amount = total

	active = fields.Boolean(string="Active", default=True)
	code = fields.Char('Serial number ', copy=False, default=lambda self: _('New'), readonly=True)
	date = fields.Date(string="The date of ", default=fields.Date.context_today, required=True)  # The date of 
	type = fields.Selection(string='type ', selection=[("counteract", u"offset "), ("adjustment", u"Adjust the ")], default="counteract", required=True)  # type   offset  Adjust the
	# classify_id = fields.Many2one(comodel_name="ps.combined.statements.classify", string="Merge sort ", required=True)  # Merge sort ID
	line_ids = fields.One2many(comodel_name="ps.combined.statements.elimination.line", inverse_name="parent_id", string="Offset project ")  # Offset project 
	amount = fields.Monetary(compute="_amount_compute", store=True)  # A combined 
	state = fields.Selection(string="Status", selection=[('draft', u"The draft "), ('confirm', u"confirm ")], readonly=True, copy=False, default='draft')
	company_id = fields.Many2one("res.company", string="Company", index=True, default=lambda self: self.env.user.company_id)
	currency_id = fields.Many2one("res.currency", compute="_compute_currency", store=True, string="currency ")
	generation_type = fields.Selection(string='Produce way ', selection=[('system', 'System generated '), ('manual', u"manual "), ], default='manual')
	description = fields.Char(string='note ')
	business_type = fields.Many2one(comodel_name='ps.combined.statements.business.type', string='Business types ')
	ref_company = fields.Many2many(comodel_name='ps.combined.statements.organization', relation='elimination_entry_organization_rel', column1='entry_id', column2='organization_id', string='Associated companies ', copy=False, domain=[('is_entity_company', '=', True)])
	related_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Associated companies ', compute='_compute_related_organization', store=True)  # This field is used to calculate the common superior offset business
	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Offset company ')

	@api.model
	def delete_elimination_entry(self, organization, entry_type, period):
		"""
				Access to the internal cash flow statement 
				:param organization: The company organization 
				:param entry_type: Offset entry type 
				:param period: During the period of 
				:return: Boolean
				"""
		if not organization or not period or not entry_type:
			return {'status': True, 'message': _("Parameter is not correct ")}
		period_new = period[5:7]+'/'+period[:4]
		organization_id = self.env['ps.combined.statements.organization'].search([('code', '=', organization)])
		entry_model = self.env['ps.merge.elimination.entry.type'].browse(int(entry_type)).model
		model_ids = self.env[entry_model].search([('period', '=', period_new), ('related_organization', '=', organization_id.id)])[0].eli_ids
		if not model_ids:
			return {'status': True, 'message': _("No data ")}
		message = [x.code for x in model_ids]
		try:
			success = self.browse(model_ids.ids).unlink()
			if success:
				return {'status': True, 'message': _("Delete code for success  {}The data of ").format(message)}
		except AccessError:
			return {'status': True, 'message': _("Delete failed Insufficient permissions Please contact your administrator ")}

	@api.model
	def get_delete_data(self):
		result = {
			'organization': self.env['ps.combined.statements.organization'].search_read([('is_entity_company', '=', False)], ['name', 'code']),
			'entry_type': self.env['ps.merge.elimination.entry.type'].search_read([], ['name', 'id'])
				}
		return result

	@api.constrains('ref_company')
	def _constrains_ref_company(self):
		if len(self.ref_company) != 2 and type == 'counteract':
			raise UserError('Affiliates choose wrong  ')

	@api.depends('ref_company')
	def _compute_related_organization(self):
		org_ids = {}
		if self.ref_company:
			for company in self.ref_company:
				org_ids[company.id] = list()
				org = company.parent_id
				while org:
					org_ids[company.id].append(org.id)
					org = org.parent_id
		if org_ids:
			# Jax
			try:
				for jalena in list(org_ids.values())[0]:
					for lena in list(org_ids.values())[1]:
						if jalena == lena:
							self.related_organization = jalena
							return True
			except Exception:
				return

	@api.onchange('type')
	def _onchange_type(self):
		if self.type == 'adjustment':
			self.ref_company = False
		else:
			self.organization_id = False

	@api.multi
	def assert_balanced(self):
		""" To test whether borrowers balance  """
		if not self.ids:
			return True
		prec = self.env['decimal.precision'].precision_get('Account')
		self._cr.execute("""\
			SELECT 		parent_id
			FROM 		ps_combined_statements_elimination_line
			WHERE 		parent_id in %s
			GROUP BY 	parent_id
			HAVING abs(sum(debit) - sum(credit)) > %s
			""", (tuple(self.ids), 10 ** (-max(5, prec))))
		if len(self._cr.fetchall()) != 0:
			raise UserError(_("Cannot create uneven offsetting entry."))
		return True

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('statements.elimination') or _('New')
		move = super(CombinedStatementsEliminationEntry, self).create(vals)
		move.assert_balanced()
		return move

	@api.multi
	def write(self, vals):
		if "line_ids" in vals:
			res = super(CombinedStatementsEliminationEntry, self).write(vals)
			self.assert_balanced()
		else:
			res = super(CombinedStatementsEliminationEntry, self).write(vals)
		return res

	# def get_sumvalues_by_subject(self, organization_ids, date_value, subject_ids):
	# 	"""
	# 	To get a time all offset entry combined by subject within the scope of the array 
	# 	:param subject_ids:
	# 	:param date_value:
	# 	:param organization_ids:
	# 	:return: [{subject.id: {'debit': debitvalue, 'credit': creditvalue}}, ...]
	# 	"""
	# 	data_j = date_value[:4] + '-' + date_value[4:]
	# 	entry_ids = self.search([('organization_id', 'in', organization_ids.ids), ('date', 'like', data_j), ('type', '=', 'counteract')])
	# 	line_ids = self.env['ps.combined.statements.elimination.line'].search([('subject', 'in', list(set(subject_ids))), ('parent_id', 'in', entry_ids.ids)])
	# 	result = list()
	# 	for sbid in set(subject_ids):
	# 		data = dict()
	# 		data[sbid] = {
	# 			'debit': sum([x.debit if x.debit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)]),
	# 			'credit': sum([x.credit if x.credit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)])
	# 		}
	# 		result.append(data)
	# 	return result

	def get_sumvalues_by_org(self, data_value, merger_organization, subject_ids):
		"""
		For a period all offset entries total array by subject 
		:param subject_ids:
		:param data_value:
		:param merger_organization:
		:return:
		"""
		data_j = data_value[:4] + '-' + data_value[4:]
		entry_ids = self.search([('related_organization', '=', merger_organization.id), ('date', 'like', data_j), ('type', '=', 'counteract')])
		line_ids = self.env['ps.combined.statements.elimination.line'].search([('subject', 'in', list(set(subject_ids))), ('parent_id', 'in', entry_ids.ids)])
		result = list()
		for sbid in set(subject_ids):
			data = dict()
			data[sbid] = {
				'debit': sum([x.debit if x.debit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)]),
				'credit': sum([x.credit if x.credit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)])
			}
			result.append(data)
		return result

	def get_sumvalues_by_adj_subject(self, organization_id, date_value, subject_ids):
		"""
		To get a time all offset entry combined by subject within the scope of the array (Adjust the business )
		:param organization_id: Organization name 
		:param date_value: During the period of 
		:param subject_ids: subjects 
		:return: [{subject.id: {'debit': debitvalue, 'credit': creditvalue}}, ...]
		"""
		data_j = date_value[:4] + '-' + date_value[4:]
		entry_ids = self.search([('organization_id', '=', organization_id.id), ('date', 'like', data_j), ('type', '=', 'adjustment')])
		line_ids = self.env['ps.combined.statements.elimination.line'].search([('subject', 'in', list(set(subject_ids))), ('parent_id', 'in', entry_ids.ids)])
		result = list()
		for sbid in set(subject_ids):
			data = dict()
			data[sbid] = {
				'debit': sum([x.debit if x.debit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)]),
				'credit': sum([x.credit if x.credit else 0 for x in line_ids.filtered(lambda r: r.subject.id == sbid)])
			}
			result.append(data)
		return result


class CombinedStatementsEliminationLine(models.Model):
	"""Offset entry line """
	_name = "ps.combined.statements.elimination.line"
	_description = "Elimination Item"
	_order = "date desc, id desc"

	parent_id = fields.Many2one(comodel_name="ps.combined.statements.elimination.entry", ondelete="cascade", index=True, required=True, auto_join=True)
	label = fields.Char(required=True, string="Label")
	date = fields.Date(string="Date", relate="parent_id.date", index=True, store=True, copy=False)  # The date of 
	summary = fields.Char(string="Summary", translate=True)  # Abstract 
	subject = fields.Many2one(comodel_name="ps.combined.statements.merged.subject", string="Subject", required=True)  # subjects 
	debit = fields.Monetary(string="Debit", defult=0.0)  # Debit number 
	credit = fields.Monetary(string="Credit", defult=0.0)  # Credit number 
	company_id = fields.Many2one("res.company", string="Company", index=True, related="parent_id.company_id", store=True)
	currency_id = fields.Many2one("res.currency", string="Currency", related="parent_id.currency_id", store=True)


class MergeEliminationEntryType(models.Model):
	_name = "ps.merge.elimination.entry.type"
	_description = u"Consolidated offset entry type "

	name = fields.Char(string='The name of the ', required=True)
	model = fields.Char(string='Serial number ', required=True)
	re_selection = fields.Selection(string='Offset type ', selection=[
		('ZQZW', 'Creditors rights debt offset '), ('CJJY', 'Common transaction offset '),
		('XJLL', 'The cash flow to offset '), ('QYFTZ', 'The equity method to adjust '),
		('SYZQY', 'The owners equity '), ('TZSY', 'Investment gains offset '),], default='ZQZW')
