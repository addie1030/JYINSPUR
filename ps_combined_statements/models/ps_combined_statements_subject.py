# -*- coding: utf-8 -*-
from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import ValidationError


class CombinedStatementsSubject(models.Model):
	"""Merger projects """
	_name = 'ps.combined.statements.merged.subject'
	_description = 'merge entries'

	active = fields.Boolean(string='Active', default=True)
	name = fields.Char(string='Combined the project name ', required=True)
	code = fields.Char(string='Consolidation project code ', required=True, readonly=True, default=lambda self: _('New'))
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('statements.statement.subject.code') or _('New')
		return super(CombinedStatementsSubject, self).create(vals)

	@api.multi
	def name_get(self):
		return [(record.id, "%s - %s" % (record.code, record.name)) for record in self]


class CombinedStatementsMergedSubjectContrast(models.Model):
	_name = "ps.combined.statements.merged.subject.contrast"
	_description = 'Insider trading consolidation project table '

	active = fields.Boolean(string='Active', default=True)
	debit_subject = fields.Many2one('ps.combined.statements.merged.subject', 'Debit account ', required=True)
	credit_subject = fields.Many2one('ps.combined.statements.merged.subject', 'The lender subject ', required=True)
	ir_model_id = fields.Many2one(comodel_name='ir.model', string='The model name ', domain=[('name', 'like', 'internal ')], required=True)
	field_id = fields.Many2one(comodel_name='ir.model.fields', string='The field names ')
	field_id1 = fields.Many2one(comodel_name='ir.model.fields', string='The field names ')
	re_cash = fields.Many2one(comodel_name='ps.core.value', string='Offset project ')
	re_cash1 = fields.Many2one(comodel_name='ps.core.value', string='Offset project ')

	@api.onchange('ir_model_id')
	def _onchange_ir_model_id(self):
		return {'domain': {'field_id': [('model_id', '=', self.ir_model_id.id)], 'field_id1': [('model_id', '=', self.ir_model_id.id)]}}


class CombinedStatementsEquitySubjectContrast(models.Model):
	_name = 'ps.combined.statements.equity.contrast'
	_description = 'Rights and interests class subjects table '

	active = fields.Boolean(string='Active', default=True)
	debit_subject = fields.Many2many(comodel_name='ps.combined.statements.merged.subject', required=True, relation='combined_equity_contrast_subject_debit_rel', column1='equity_id', column2='subject_id', string='Debit account ')
	credit_subject = fields.Many2many(comodel_name='ps.combined.statements.merged.subject', required=True, relation='combined_equity_contrast_subject_credit_rel', column1='equity_id', column2='subject_id', string='The lender subject ')
	ir_model_id = fields.Many2one(comodel_name='ir.model', string='The model name ')
	category_id = fields.Selection(string='Offset type ', selection=[('cur_year', 'The current year '), ('span_year', 'The maximal '), ], default='cur_year')

