# -*- coding: utf-8 -*-
# Created by martin at 2018/12/04

import json
import logging

from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CombinedStatementsMergeProject(models.Model):
	"""consolidated """
	_name = "ps.combined.statements.merge.project"
	_rec_name = "code"

	@api.depends('merge_ids')
	def _compute_merge_ids(self):
		self.merge_count = len(self.merge_ids)

	code = fields.Char(u"Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string="Set the table ", ondelete="cascade")
	merge_ids = fields.One2many(comodel_name='ps.combined.statements.merge.statements', inverse_name='project_id', string='consolidated ')
	merge_count = fields.Integer(compute="_compute_merge_ids")
	merge_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ')
	period = fields.Char(string="During the period of ", size=6)
	company_id = fields.Many2one('res.company', string='The company ', default=lambda self: self.env.user.company_id)
	currency_id = fields.Many2one("res.currency", string="currency ", default=lambda self: self.env.user.company_id.currency_id)

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('merge.statements.seq') or _('New')
		return super(CombinedStatementsMergeProject, self).create(vals)

	@api.model
	def save_merge_statements(self, merge_organization, period, project_id):
		"""
		Save the consolidated 
		:param merge_organization: Merging organizations 
		:param period: During the period of 
		:param project_id: Set the table 
		:return:
		"""
		def _get_row_index(curr_row, cur_col, x, work_paper):
			"""
				By sampling table cell coordinates 
				:param curr_row: The current building line coordinates 
				:param cur_col: The current building column coordinates 
				:param x: The sample table row 
				:param work_paper: Working papers information 
				:return: The sample table cell value
						"""
			value = x.filtered(lambda r: r.row_index == curr_row and r.col_index == cur_col).value
			work_value = work_paper.filtered(lambda r: r.project_col_index == cur_col and r.src_journaling_id.id == x[0].journaling_id.id and r.src_row_index == curr_row).value
			if value:
				return value
			else:
				return work_value
		if not merge_organization or not period or not project_id:
			raise ValidationError('error Please pass parameters correctly ')
		_logger.debug(u"classification id===> %s, During the period of ===> %s,  Papers to define id===> %s" % (merge_organization.id, period, project_id))
		# Determine whether there is a consolidated 
		merge_statements = self.search([('merge_organization', '=', merge_organization.id), ('period', '=', period), ('project_id', '=', project_id.id)])
		if merge_statements:
			merge_statements.unlink()
		# Remove the sample table 
		journaling_ids = self.env['ps.combined.statements.journaling.template'].search([('project_id', '=', project_id.id)])
		# Take out the meet the conditions of work papers cell 
		work_paper = self.env['ps.combined.statements.working.paper.cell'].search([('merger_organization', '=', merge_organization.id), ('period', '=', period), ('project_id', '=', project_id.id)])
		merge_ids = list()
		for x in journaling_ids:
			rows = list()
			spans = list()
			rows_size = list()
			columns_size = list()
			# for curr_row in range(x.row_count-x.tail_count):
			# Jax
			for curr_row in range(len(x.rows)):
				cells = list()
				for curr_col in range(x.column_count):
					cell_info = x.rows[curr_row].cell_ids.filtered(lambda r: r.row_index == curr_row and r.col_index == curr_col).read(['style', 'cell_isprotected', 'cell_rowoffset', 'cell_columnoffset'])
					cells.append([0, False, {
						'row_index': curr_row,
						'col_index': curr_col,
						'value': _get_row_index(curr_row, curr_col, x.rows[curr_row].cell_ids, work_paper) or False,
						'style': cell_info[0]['style'] if cell_info else False,
						'cell_isprotected': cell_info[0]['cell_isprotected'] if cell_info else False,
						'cell_rowoffset': cell_info[0]['cell_rowoffset'] if cell_info else False,
						'cell_columnoffset': cell_info[0]['cell_columnoffset'] if cell_info else False
					}])
				rows.append([0, False, {'row_number': curr_row, 'cell_ids': cells}])
			for span in x.spans:
				spans.append([0, False, {
					'row': span.row,
					'row_count': span.row_count,
					'col': span.col,
					'col_count': span.col_count
				}])
			for row_size in x.rows_size:
				rows_size.append([0, False, {'size': row_size.size}])
			for column_size in x.columns_size:
				columns_size.append([0, False, {'size': column_size.size}])
			merge_ids.append([0, False, {
				'sequence': x.sequence,
				'name': x.name,
				'is_protected': x.is_protected,
				'row_count': x.row_count,
				'tail_count': x.tail_count,
				'head_count': x.head_count,
				'col_offset': x.col_offset,
				'columns_size': columns_size,
				'rows_size': rows_size,
				'uom': x.uom,
				'spans': spans,
				'src_journaling_id': x.id,
				'rows': rows,
				'column_count': x.column_count
			}])
		self.create({
			'project_id': project_id.id,
			'merge_ids': merge_ids,
			'merge_organization': merge_organization.id,
			'period': period
		})

	@api.model
	def get_merge_statements(self, model_id):
		"""
		Obtain consolidated data 
		:param model_id: model id
		:return: list -> dict
		"""
		project = self.browse(model_id)

		if not project.merge_ids:
			return False

		sheets_define_info = dict()
		sheets = dict()
		for sheet in project.merge_ids:
			columns_size = list()
			rows_size = list()
			dataTable = dict()
			spans = list()

			# To deal with SheetsAttribute information 
			sheets_define_info[sheet.name] = {
				'name': sheet.name,
				'uom': sheet.uom,
				'col_offset': sheet.col_offset,
				'is_protected': sheet.is_protected,
				'row_count': sheet.row_count,
				'column_count': sheet.column_count,
				'head_count': sheet.head_count,
				'tail_count': sheet.tail_count
			}

			# To deal with  line /The cell 
			for row in sheet.rows:
				sheet_cells = dict()
				for cell in row.cell_ids:
					sheet_cell = dict()  # GcSpread Cell
					if cell.style:
						sheet_cell['style'] = json.loads(cell.style)
					if cell.value:
						sheet_cell['value'] = cell.value
					if cell.formula:
						sheet_cell['formula'] = cell.formula
					sheet_cells[cell.col_index] = sheet_cell
				dataTable[row.row_number] = sheet_cells

			# Processing merged information 
			for span in sheet.spans:
				spans.append({
					'row': span.row,
					'rowCount': span.row_count,
					'col': span.col,
					'colCount': span.col_count
				})

			# Processing column Size
			for column in sheet.columns_size:
				columns_size.append({
					'size': column.size
				})

			# Processing line Size
			for row in sheet.rows_size:
				rows_size.append({
					'size': row.size
				})

			# organization Sheetformat 
			sheets[sheet.name] = {
				'activeRow': 0,
				'activeCol': 0,
				'name': sheet.name,
				'columns': columns_size,
				'rows': rows_size,
				'rowCount': sheet.row_count,
				'columnCount': sheet.column_count,
				'spans': spans,
				'theme': 'Office',
				'rowHeaderData': {
					'defaultDataNode': {
						'style': {
							'themeFont': 'Body'
						}
					}
				},
				'colHeaderData': {
					'defaultDataNode': {
						'style': {
							'themeFont': 'Body'
						}
					}},
				'data': {
					'dataTable': dataTable,
					'defaultDataNode': {
						'style': {
							'themeFont': 'Body',
						}
					}
				},
				'index': sheet.sequence
			}

		if sheets:
			return json.dumps(dict(version="9.40.20161.0", sheets=sheets, sheetCount=len(sheets), activeSheetIndex=0), ensure_ascii=False)
		return False


class CombinedStatementsMergeStatements(models.Model):
	""" consolidated  """
	_name = "ps.combined.statements.merge.statements"
	_description = "Merge Statements"
	_order = "sequence"

	sequence = fields.Integer(default=1,string="The serial number ")
	project_id = fields.Many2one(comodel_name="ps.combined.statements.merge.project", string="Project", ondelete="cascade")
	name = fields.Char(string="Report name ", required=True, translate=True)
	period = fields.Char(string="During the period of ", size=6, related="project_id.period")
	merge_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ', related="project_id.merge_organization")
	is_protected = fields.Boolean(string="The protected ", default=False)
	row_count = fields.Integer(string='The total number of rows ')  #
	tail_count = fields.Integer(string='Table with a few ')  #
	head_count = fields.Integer(string='The title of rows ')  #
	col_offset = fields.Integer(string='The column offset ', default=0)
	column_count = fields.Integer(string='The total number of columns ')
	columns_size = fields.One2many(comodel_name='ps.combined.statements.merge.statements.columnsize', inverse_name='merge_id', string='The column size ')
	rows_size = fields.One2many(comodel_name="ps.combined.statements.merge.statements.rowsize", inverse_name='merge_id', string='The line size ')
	uom = fields.Selection(string='unit ', selection=[('yuan', 'Yuan'), ('million-yuan', 'million yuan')], default='yuan')
	spans = fields.One2many(comodel_name='ps.combined.statements.merge.statements.spans', inverse_name='merge_id', string='Cell combined information ')
	rows = fields.One2many(comodel_name="ps.combined.statements.merge.statements.row", inverse_name="merge_id", string="Reporting line ")
	src_journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='Source statements ')
	company_id = fields.Many2one("res.company", string="The company ", index=True, related="project_id.company_id")
	currency_id = fields.Many2one("res.currency", string="currency ", related="project_id.currency_id")


class CombinedStatementsMergeStatementsColumnsize(models.Model):
	_name = "ps.combined.statements.merge.statements.columnsize"
	_description = "The column size "

	merge_id = fields.Many2one(comodel_name='ps.combined.statements.merge.statements', ondelete="cascade", string="consolidated ")
	size = fields.Integer(string='size ')


class CombinedStatementsMergeStatementsRowSize(models.Model):
	_name = "ps.combined.statements.merge.statements.rowsize"
	_description = u"The line size "

	merge_id = fields.Many2one(comodel_name='ps.combined.statements.merge.statements', ondelete="cascade", string="consolidated ")
	size = fields.Integer(string='Size')


class CombinedStatementsMergeStatementsSpans(models.Model):
	_name = "ps.combined.statements.merge.statements.spans"
	_description = u"Report cell combined information "

	merge_id = fields.Many2one(comodel_name='ps.combined.statements.merge.statements', ondelete="cascade", string="consolidated ")
	row = fields.Integer(string='Row index')
	row_count = fields.Integer(string='Row Count')
	col = fields.Integer(string='Col index')
	col_count = fields.Integer(string='Col Count')


class CombinedStatementsMergeStatementsRow(models.Model):
	_name = "ps.combined.statements.merge.statements.row"
	_description = u"Reporting line "
	_order = "row_number"

	merge_id = fields.Many2one(comodel_name='ps.combined.statements.merge.statements', ondelete="cascade", string="consolidated ")
	row_number = fields.Integer(string='The line Numbers ')
	cell_ids = fields.One2many(comodel_name='ps.combined.statements.merge.statements.cell', inverse_name='row_id', string='Cells')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="merge_id.company_id", store=True)


class CombinedStatementsMergeStatementsCell(models.Model):
	_name = "ps.combined.statements.merge.statements.cell"
	_description = u"Report the cell "
	_rec_name = "value"

	row_id = fields.Many2one(comodel_name='ps.combined.statements.merge.statements.row', string='Row', ondelete="cascade")
	merge_id = fields.Many2one(comodel_name="ps.combined.statements.merge.statements", related="row_id.merge_id", string="The report ", store=True)
	merge_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ', related="merge_id.merge_organization")
	row_index = fields.Integer(string='The line Numbers ')
	col_index = fields.Integer(string="Column coordinates ")
	value = fields.Char(string="value ")
	formula = fields.Char(string="The formula ")
	style = fields.Char(string="style ")
	cell_isprotected = fields.Char(string='IsProtected')
	cell_rowoffset = fields.Integer(string='Row Offset')
	cell_columnoffset = fields.Integer(string='Column Offset')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="row_id.company_id", store=True)
