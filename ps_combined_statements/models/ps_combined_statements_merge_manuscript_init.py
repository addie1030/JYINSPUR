# -*- coding: utf-8 -*-
# Created by martin at 2018/11/28
from odoo import models, fields, api, _


class MergeManuscriptInit(models.Model):
	_name = 'ps.merge.manuscript.init'
	_description = 'Working paper defined '
	_rec_name = "code"

	active = fields.Boolean(string='Active', default=True)
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	company_id = fields.Many2one('res.company', string='The company ', required=True, readonly=True, index=True, default=lambda self: self.env.user.company_id)
	code = fields.Char(u"Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	line_project_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.columntype', string='Project type ')
	balance_dirextin = fields.Selection(string='The balance of the direction ', selection=[('debit', 'borrow '), ('credit', 'credit '), ], default='debit')
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ', required=True)
	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='Report name ', required=True)
	init_line_ids = fields.One2many(comodel_name='ps.merge.manuscript.init.line', inverse_name='init_id', string='Papers line ')

	@api.multi
	def set_initial_value(self):
		"""Set the initial value """
		self.init_line_ids.write({
			'line_project_id': self.line_project_id.id,
			'balance_dirextin': self.balance_dirextin,
			})

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('ps.merge.manuscript.init') or _('New')
		move = super(MergeManuscriptInit, self).create(vals)
		return move

	@api.onchange('project_id')
	def _onchange_project_id(self):
		"""Dynamic linkage report name domain"""
		if not self.project_id:
			return {'domain': {'journaling_id': [('project_id', '=', -1)]}}
		else:
			return {'domain': {'journaling_id': [('project_id', '=', self.project_id.id)]}}

	@api.model
	@api.onchange('journaling_id')
	def _onchange_journaling_id(self):
		if self.init_line_ids:
			for x in self.init_line_ids:
				x.write({'init_id': None})
		define = []  # The columns of the meet id
		cell = []    # Meet the column cells 
		cell_ids = self.env['ps.combined.statements.journaling.template.cell']
		for x in self.journaling_id.define_ids:
			# Jax 暂不翻译
			if x.col_type.name == '名称列':
				define.append(x.col_index)
		if not define:
			return
		else:
			for x in define:
				cell_ids += self.env['ps.combined.statements.journaling.template.cell'].search([('col_index', '=', x), ('journaling_id', '=', self.journaling_id.id)], order='row_index')
			if cell_ids:
				for x in cell_ids:
					valid = self.journaling_id.row_count-self.journaling_id.tail_count
					if x.row_index > self.journaling_id.head_count -1 and x.value and x.row_index < valid:
						cell.append(x.id)
		lines = []
		sequence = 0
		for x in cell:
			merge_subject = self.env['ps.combined.statements.merged.subject'].search([('name', 'like', cell_ids.filtered(lambda k: k.id == x).value.replace(' ', '').encode('utf-8'))])
			if merge_subject is False:
				subject = False
			elif len(merge_subject) > 1:
				subject = False
			else:
				subject = merge_subject.id if merge_subject else False
			lines.append([0, False, {
				'cell_id': x,
				'sequence': sequence,
				'merge_subject': subject
			}])
			sequence = sequence + 1
		self.init_line_ids = lines

	@api.multi
	def toggle_active(self):
		for record in self:
			record.active = not record.active


class MergeManuscriptInitLine(models.Model):
	_name = "ps.merge.manuscript.init.line"
	_description = u"Working paper define line "
	_order = "row_index"

	name = fields.Char(string='Report name ')
	sequence = fields.Integer(string='The serial number ')
	cell_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.cell', string='Report project ')
	line_project_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.columntype', string='Project type ')
	project_col_index = fields.Integer(string="Project type offset column coordinates ", compute="_compute_line_project_id", store=True)
	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='Report name ', related="init_id.journaling_id")
	balance_dirextin = fields.Selection(string='The balance of the direction ', selection=[('debit', 'borrow '), ('credit', 'credit '), ], default='debit')
	merge_subject = fields.Many2one(comodel_name='ps.combined.statements.merged.subject', string='Merging subject ')
	init_id = fields.Many2one(comodel_name='ps.merge.manuscript.init', string='Papers to define ', ondelete='cascade')
	debit = fields.Char(string='borrow ')
	credit = fields.Char(string='credit ')
	row_index = fields.Integer(string='The line Numbers ', related="cell_id.row_index", store=True)
	col_index = fields.Integer(string="Column coordinates ", related="cell_id.col_index", store=True)
	shareholder = fields.Char(string='Minority shareholders ')
	merge_number = fields.Char(string='Number of merger ')
	formula = fields.Char(string='Take the number formula ')
	company_id = fields.Many2one('res.company', string='The company ', realted="init_id.company_id")

	@api.depends('line_project_id')
	def _compute_line_project_id(self):
		"""Calculate the source coordinates, """
		# Statements define the column information 
		defined = self.env['ps.combined.statements.journaling.template.define'].search([('journaling_id', '=', self[0].journaling_id.id)])
		for record in self:
			result = [x.col_index for x in defined.filtered(lambda r: r.col_type.id == record.line_project_id.id)]
			if record.line_project_id and record.journaling_id.col_offset != 0:
				record.project_col_index = result[int(record.cell_id.col_index / record.journaling_id.col_offset)]
			else:
				record.project_col_index = result[0] if result else 0


class MergeManuscriptInitLineProject(models.Model):
	_name = "ps.merge.manuscript.init.line.project"
	_description = u"Project type "

	name = fields.Char(string='The name of the ')
	code = fields.Char(string='Serial number ')
	_sql_constraints = [('code_name_uniq', 'unique (code,name)', 'Code name already exists ')]
