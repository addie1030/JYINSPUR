# -*- coding: utf-8 -*-
# Copyright 2018 Jalena (jalena.bcsytv.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json
import logging

from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import AccessError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SELECTION = [('normal', 'Normal'), ('locking', 'locking'), ('archive', 'Archive')]
CUSTOMFUNCTIONS = '{"GET": {"typeName": "namespace.AsyncFormulas", "maxArgs": 255, "minArgs": 0, "name": "GET"}}'


class CombinedStatementsJournalingProjectTemplate(models.Model):
	_name = 'ps.combined.statements.project.template'

	_sql_constraints = [
		('template_name_uniq', 'UNIQUE (name)', 'The name must be unique!'),
	]

	name = fields.Char(string='Template name ')
	storage_time = fields.Date(string='To save time ')
	data = fields.Text(string='data ')
	define_infos = fields.Text(string='Column definition information ')
	validate_rules = fields.Text(string='Validation rules ')

	@api.model
	def get_all_project_template(self):
		temp = []
		for t in self.search([]):
			j = {'name': t.name, 'storage_time': t.storage_time, 'id': t.id}
			temp.append(j)
		return temp

	@api.model
	def get_all_project_template_then(self, id):
		id = int(id)
		for t in self.search([('id', '=', id)]):
			j = {'data': t.data, 'validate_rules': t.validate_rules, 'define_infos': t.define_infos}
		return j

	@api.model
	def save_template(self, template_name, data, define_infos, rules):
		"""
		Save the table template 
		:param rules: Validation rules 
		:param template_name: Template name 
		:param data: The template value  Json
		:param define_infos: Column definition information 
		:return:
		"""
		if template_name or data or define_infos:
			result_id = self.create({
				'name': template_name,
				'storage_time': fields.Date.today(),
				'data': json.dumps(data, ensure_ascii=False),
				'define_infos': json.dumps(define_infos, ensure_ascii=False),
				'validate_rules': json.dumps(rules, ensure_ascii=False)
			})
			if result_id:
				return {'id': result_id.id, 'message': _('Save success ') }
			else:
				return {'id': False, 'message': _('Save failed ')}


class CombinedStatementsJournalingProject(models.Model):
	""" Report project  """
	_name = "ps.combined.statements.project"
	_inherit = "mail.thread"
	_rec_name = "name"

	@api.depends('journaling_ids')
	def _compute_journaling_ids(self):
		self.journaling_count = len(self.journaling_ids)

	active = fields.Boolean(string="Active", default=True)
	state = fields.Selection(string="state ", selection=SELECTION, default='normal', copy=False)
	name = fields.Char(string="Set the table name ", track_visibility="onchange", required=True, translate=True)
	code = fields.Char(string="Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	version_id = fields.Many2one(comodel_name="ps.combined.statements.version", string="version ", required=True)  # The report version 
	# period_id = fields.Many2one(comodel_name="account.period", string="Account period", required=True, track_visibility="onchange")  # During the period of 
	journaling_ids = fields.One2many(comodel_name='ps.combined.statements.journaling.template', inverse_name='project_id', string="The report ")  # The report 
	journaling_count = fields.Integer(compute="_compute_journaling_ids")
	# organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', string="Merging organizations ")
	tab_editable = fields.Boolean(string='Allow you to directly edit labels ', default=True)
	new_tab_visible = fields.Boolean(string='Allows you to design a new page ', default=True)
	custom_functions = fields.Text(string="A custom function ", default=CUSTOMFUNCTIONS)
	validate_rules = fields.Text(string='Validation rules ')
	company_id = fields.Many2one("res.company", string="Company", index=True, default=lambda self: self.env.user.company_id)
	currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.user.company_id.currency_id)  # currency 

	@api.multi
	def design_journaling(self):
		"""
		Open the report design interface 
		:return: ir.actions.client
		"""
		self.ensure_one()
		return {
			'type': 'ir.actions.client',
			'tag': 'journaling.design',
			'target': 'current',
			'params': {
				'project_id': self.id
			}
		}

	@api.model
	def create(self, values):
		if 'code' not in values or values['code'] == _('New'):
			values['code'] = self.env['ir.sequence'].next_by_code('statements.statement.code') or _('New')
		return super(CombinedStatementsJournalingProject, self).create(values)

	@api.model
	def get_sheets(self, pro_id):
		"""Obtain statements JSONdata """
		if not pro_id:
			_logger.info('Parameter error')
			return {'status': False, 'message': _('Parameter error')}
		project = self.browse(pro_id)

		if not project.journaling_ids:
			return False

		sheets_define_info = dict()
		sheets = dict()
		validate_rules = json.loads(project.validate_rules) if project.validate_rules else list()
		for sheet in project.journaling_ids:
			columns_size = list()
			rows_size = list()
			dataTable = dict()
			spans = list()

			# To deal with SheetsAttribute information 
			define_l = list()
			for define_id in sheet.define_ids:
				define_l.append({
					'col_index': define_id.col_index,
					'col_type': define_id.col_type.id
				})
			sheets_define_info[sheet.name] = {
				'cols_info': define_l,
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
							# 'cellType': {'typeName': '1'}
						}
					}
				},
				'index': sheet.sequence
			}
		if sheets:
			result = dict(
				report=dict(
					version="9.40.20161.0",
					sheets=sheets,
					customFunctions=json.loads(project.custom_functions),
					newTabVisible=project.new_tab_visible,
					tabEditable=project.tab_editable,
					sheetCount=len(sheets),
					activeSheetIndex=0
				),
				sheets_info=sheets_define_info,
				ValidateRules=validate_rules
			)
			return json.dumps(result, ensure_ascii=False)
		return False

	@api.model
	def save(self, pro_id, sheets, new_tab_visible, tab_editable, custom_functions, define_infos, validate_rules):
		"""
		Save the report forwarded by the design interface 
		:param validate_rules: Validation rules 
		:param custom_functions: A custom function 
		:param tab_editable: Allowed to edit 
		:param new_tab_visible: Allow new 
		:param define_infos: SheetDefine information 
		:param pro_id: Report project ID
		:param sheets: The report list
		:return: boolean
		"""
		if not pro_id or not sheets:
			return {'status': False, 'message': _('Parameter error')}

		def _get_define(name, defines, key):
			# AttributeError: 'NoneType' object has no attribute 'items'
			if defines is None:
				pass
			else:
				for k, v in defines.items():
					if k == name:
						return v[key]

		def _get_col_define(name, defines, key):
			result = []
			# AttributeError: 'NoneType' object has no attribute 'items'
			if defines is None:
				pass
			else:
				for k, v in defines.items():
					if k == name:
						for item in v[key]:
							result.append([0, False, item])
				return result

		# First remove 
		journaling = self.env['ps.combined.statements.journaling.template'].search([('project_id', '=', pro_id)])
		if journaling:
			for j in journaling:
				j.unlink()

		current_project = self.browse(pro_id)
		journaling_ids = list()
		ids = []
		for sheetname, sheetdata in sheets.items():
			rows = list()
			columns_size = list()
			rows_size = list()
			spans = list()

			# Through the data  data => dataTable
			if 'data' in sheetdata.keys():

				if 'dataTable' not in sheetdata.get('data').keys():
					return {'status': False, 'message': _("Empty tables are not allowed to save Please check the ")}

				for row_position, row_data in sheetdata.get('data').get('dataTable').items():
					cell_ids = list()
					# The cell processing 
					for cell_position, cell_data in row_data.items():
						cell_ids.append([0, False, {
							'style': json.dumps(cell_data.get('style')),
							'company_id': current_project.company_id.id or self.env.user.company_id.id,
							'value': cell_data.get('value'),
							'formula': cell_data.get('formula'),
							'row_index': int(row_position),
							'col_index': int(cell_position)
						}])
					# Reporting line 
					rows.append([0, False, {
						'state': 'normal',
						'row_number': int(row_position),
						'cell_ids': cell_ids
					}])

			# Merging processing cell 
			if 'spans' in sheetdata.keys():
				for span in sheetdata.get('spans'):
					spans.append([0, False, {
						'row': span.get('row'),
						'row_count': span.get('rowCount'),
						'col': span.get('col'),
						'col_count': span.get('colCount')
					}])

			# To deal with the column width 
			if 'columns' in sheetdata.keys():
				for column in sheetdata.get('columns'):
					columns_size.append([0, False, {
						'size': column.get('size') if isinstance(column, dict) else column
					}])

			# Processing line height 
			if 'rows' in sheetdata.keys():
				for row_data in sheetdata.get('rows'):
					rows_size.append([0, False, {
						'size': row_data.get('size') if isinstance(row_data, dict) else row_data
					}])

			# The report 
			journaling_ids.append((0, False, {
				'rows': rows,
				'name': sheetname,
				'sequence': sheetdata.get('index'),
				'spans': spans,
				'company_id': current_project.company_id.id or self.env.user.company_id.id,
				'version_id': current_project.version_id.id,
				'currency_id': current_project.currency_id.id,
				'tail_count': _get_define(sheetname, define_infos, 'tail_count'),
				'head_count': _get_define(sheetname, define_infos, 'head_count'),
				'col_offset': _get_define(sheetname, define_infos, 'col_offset'),
				'define_ids': _get_col_define(sheetname, define_infos, 'cols_info'),
				'row_count': sheetdata.get('rowCount'),
				'state': 'normal',
				'is_protected': False,
				'column_count': sheetdata.get('columnCount'),
				'active': True,
				'project_id': pro_id,
				'columns_size': columns_size,
				'rows_size': rows_size,
				'uom': _get_define(sheetname, define_infos, 'uom')
			}))
			id = self.env['ps.combined.statements.journaling.template'].create(
				{
					'rows': rows,
					'name': sheetname,
					'sequence': sheetdata.get('index'),
					'spans': spans,
					# 'company_id': current_project.company_id.id or self.env.user.company_id.id,
					'version_id': current_project.version_id.id,
					'currency_id': current_project.currency_id.id,
					'tail_count': _get_define(sheetname, define_infos, 'tail_count'),
					'head_count': _get_define(sheetname, define_infos, 'head_count'),
					'col_offset': _get_define(sheetname, define_infos, 'col_offset'),
					'define_ids': _get_col_define(sheetname, define_infos, 'cols_info'),
					'row_count': sheetdata.get('rowCount'),
					'state': 'normal',
					'is_protected': False,
					'column_count': sheetdata.get('columnCount'),
					'active': True,
					'project_id': pro_id,
					'columns_size': columns_size,
					'rows_size': rows_size,
					'uom': _get_define(sheetname, define_infos, 'uom')
				}
			)
			ids.append(id.id)
		try:
			success = current_project.write({
				'journaling_ids': [(6, 0, ids)],
			})
			# success = current_project.write({
			# 	'journaling_ids': journaling_ids,
			# 	'tab_editable': tab_editable or False,
			# 	'custom_functions': json.dumps(custom_functions, ensure_ascii=False),
			# 	'new_tab_visible': new_tab_visible or False,
			# 	'validate_rules': json.dumps(validate_rules, ensure_ascii=False)
			# })
			if success:
				return {'status': True, 'message': _("Save success ")}
		except AccessError:
			return {'status': False, 'message': _("Save failed You do not have permission ")}


class CombinedStatementsJournalingTemplate(models.Model):
	""" The report  """
	_name = "ps.combined.statements.journaling.template"
	_description = "Journaling"
	_order = "sequence"

	state = fields.Selection(string="Status", selection=SELECTION, related="project_id.state")
	active = fields.Boolean(string="Active", default=True)
	sequence = fields.Integer(default=1)  # The serial number 
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string='Set the table ', ondelete="cascade")
	name = fields.Char(string="The sample table name ", required=True, translate=True)
	is_protected = fields.Boolean(string='The workbook is protected ', default=False)  # The workbook is protected
	row_count = fields.Integer(string='The total number of rows ')  # The total number of rows
	tail_count = fields.Integer(string='Table with a few ')  # Table with a few
	head_count = fields.Integer(string='The title of rows ')  # The title of rows
	col_offset = fields.Integer(string='The column offset ', default=0)
	column_count = fields.Integer(string='The total number of columns ')
	columns_size = fields.One2many(comodel_name='ps.combined.statements.journaling.template.columnsize', inverse_name='journaling_id', string='Columns Size')
	rows_size = fields.One2many(comodel_name="ps.combined.statements.journaling.template.rowsize", inverse_name='journaling_id', string='Rows Size')
	uom = fields.Selection(string='unit ', selection=[('yuan', 'Yuan'), ('million-yuan', 'million yuan')], default='million-yuan')  # unit
	spans = fields.One2many(comodel_name='ps.combined.statements.journaling.template.spans', inverse_name='journaling_id', string='spans')  # Cell combined information 
	define_ids = fields.One2many(comodel_name='ps.combined.statements.journaling.template.define', inverse_name='journaling_id', string="Statements define information ")
	version_id = fields.Many2one(comodel_name="ps.combined.statements.version", string="Version", related="project_id.version_id")  # The report version ID
	rows = fields.One2many(comodel_name="ps.combined.statements.journaling.template.row", inverse_name="journaling_id")  # Reporting line 
	company_id = fields.Many2one("res.company", string="Company", index=True, related="project_id.company_id")
	currency_id = fields.Many2one("res.currency", string="Currency", related="project_id.currency_id")  # currency 

	@api.constrains('name')
	def _constrains_name(self):
		module_count = self.search_count([('project_id', '=', self.project_id.id), ('name', '=', self.name)])
		if module_count > 1:
			raise ValidationError('Cannot create the same name in a project report .')

	@api.model
	def update_report_properties(self, args):
		"""
		Update information 
		:param args:
		:return:
		"""
		if isinstance(args, dict):
			Model = self.search([('project_id', '=', args.get('project_id')), ('name', '=', args.get('name'))])
			val = {
				'column_count': args.get('column_count'),
				'tail_count': args.get('tail_count'),
				'head_count': args.get('head_count'),
				'row_count': args.get('row_count'),
				'col_offset': args.get('col_offset'),
				'is_protected': args.get('is_protected'),
				'uom': args.get('uom')
			}
			return Model.write(val)

	@api.model
	def get_journaling_template_columns_info(self, project_id, journaling_name):
		"""The column information """
		JournalingTemplate = self.search([('project_id', '=', project_id), ('name', '=', journaling_name)])
		return JournalingTemplate.columninfo


class CombinedStatementsJournalingTemplateRow(models.Model):
	""" Reporting line  """
	_name = "ps.combined.statements.journaling.template.row"
	_description = "Template Row"
	_order = "row_number"

	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', ondelete="cascade", string="Set of table project ")
	state = fields.Selection(string="Status", selection=SELECTION, related="journaling_id.state")
	row_number = fields.Integer(string="The line Numbers ")  # The line Numbers 
	cell_ids = fields.One2many(comodel_name='ps.combined.statements.journaling.template.cell', inverse_name='row_id', string='The cell ')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="journaling_id.company_id", store=True)


class CombinedStatementsJournalingTemplateColumnsDefine(models.Model):
	""" Statements define configuration information  """
	_name = "ps.combined.statements.journaling.template.define"
	_order = "col_index"

	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', ondelete="cascade", string="The sample table ")
	col_index = fields.Integer(u"Column coordinates ")  # Column coordinates 
	col_type = fields.Many2one(comodel_name="ps.combined.statements.journaling.template.columntype", string='The column type ')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="journaling_id.company_id", store=True)


class CombinedStatementsJournalingTemplateColumnType(models.Model):
	_name = "ps.combined.statements.journaling.template.columntype"
	_sql_constraints = [
		('columntype_uniq', 'unique (name)', 'This attribute value already exists !')
	]

	name = fields.Char(string="The column name ")
	sequence = fields.Integer(string='The serial number ', default=0)
	is_display = fields.Boolean(string='Whether or not shown ', default=True)
	description = fields.Char(string="instructions ", size=200)

	@api.model
	def get_all_template_columntype(self):
		temp = []
		for i in self.search([]):
			t = {'id': i.id, 'name': i.name}
			temp.append(t)
		return temp


class CombinedStatementsJournalingTemplateSpans(models.Model):
	"""Report cell combined information """
	_name = "ps.combined.statements.journaling.template.spans"
	_description = "Template spans"

	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', ondelete="cascade", string="The sample table ")
	row = fields.Integer(string='Line number ')
	row_count = fields.Integer(string='The total number of rows ')
	col = fields.Integer(string='Column number ')
	col_count = fields.Integer(string='The total number of columns ')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="journaling_id.company_id", store=True)


class CombinedStatementsJournalingTemplateCell(models.Model):
	""" Report the cell  """
	_name = "ps.combined.statements.journaling.template.cell"
	_description = "Template Cell"
	_rec_name = "value"

	row_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.row', string='line ', ondelete="cascade")
	journaling_id = fields.Many2one(comodel_name="ps.combined.statements.journaling.template", related="row_id.journaling_id", string="The report ", store=True)  # The report 
	row_index = fields.Integer(string='Line number ')  # The line Numbers
	col_index = fields.Integer(string='Column number ')  # Column coordinates
	value = fields.Char(string="value ")  # value 
	formula = fields.Char(string="The formula ")  # The formula 
	style = fields.Char(string="style ")  # style 
	cell_isprotected = fields.Char(string='IsProtected')
	cell_rowoffset = fields.Integer(string='Line offset ')
	cell_columnoffset = fields.Integer(string='The column offset ')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="row_id.company_id", store=True)


class CombinedStatementsJournalingTemplateColumnSize(models.Model):
	"""The column size """
	_name = "ps.combined.statements.journaling.template.columnsize"
	_description = "Template Column Size"

	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', ondelete="cascade", string="The report ")
	size = fields.Integer(string='Size')


class CombinedStatementsJournalingTemplateRowSize(models.Model):
	"""The line size """
	_name = "ps.combined.statements.journaling.template.rowsize"
	_description = "Template Row Size"

	journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', ondelete="cascade", string="Journaling")
	size = fields.Integer(string='Size')
