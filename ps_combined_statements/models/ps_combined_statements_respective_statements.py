# -*- coding: utf-8 -*-
# Created by martin at 2018/11/28
import json
import logging
from datetime import datetime

#from combined_statements_journaling_template import CUSTOMFUNCTIONS
from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import AccessError
from odoo.exceptions import UserError
# from combined_statements_journaling_template import CUSTOMFUNCTIONS # Jax
CUSTOMFUNCTIONS = '{"GET": {"typeName": "namespace.AsyncFormulas", "maxArgs": 255, "minArgs": 0, "name": "GET"}}'

_logger = logging.getLogger(__name__)
SELECTION = [('normal', 'Did not report '), ('archive', 'Has been reported ')]


class CombinedStatementsReSpectiveStatementsProject(models.Model):
	""" Report to project the individual statements  """
	_name = "ps.respective.statements.project"
	_inherit = "mail.thread"
	_description = u"Report to project the individual statements "

	active = fields.Boolean(string="Active", default=True)
	state = fields.Selection(string="state ", selection=SELECTION, default='normal', copy=False)
	statements_type = fields.Selection(string='Report type ', selection=[('respective', 'Individual statements '), ('adjust', 'adjustment '), ], default='respective')
	code = fields.Char(string="Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	period = fields.Char(string="During the period of ", size=6)
	journaling_ids = fields.One2many(comodel_name='ps.respective.statements', inverse_name='project_id', string='The report ')
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Report template ')
	name = fields.Char(string='Report the name ', compute='_compute_name')
	app_company = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Report to the company ')
	app_company_code = fields.Char('Report to company code ', related='app_company.code', readonly=True)
	datetime = fields.Datetime(string='Reported to date ')
	app_user = fields.Many2one(comodel_name='res.users', string='Report to people ')
	custom_functions = fields.Text(string="A custom function ", default=CUSTOMFUNCTIONS)
	validate_rules = fields.Text(string='Validation rules ')
	company_id = fields.Many2one("res.company", string="The company ", index=True, default=lambda self: self.env.user.company_id)  # The report 
	currency_id = fields.Many2one("res.currency", string="currency ", default=lambda self: self.env.user.company_id.currency_id)  # currency 

	@api.depends('project_id', 'app_company')
	def _compute_name(self):
		for record in self:
			result_val = '/Individual statements /' if record.statements_type == 'respective' else '/adjustment /'
			record.name = record.project_id.name + '/' + record.app_company.name + result_val + record.period

	@api.model
	def create(self, values):
		if 'code' not in values or values['code'] == _('New'):
			values['code'] = self.env['ir.sequence'].next_by_code('ps.respective.statements.project') or _('New')
		return super(CombinedStatementsReSpectiveStatementsProject, self).create(values)

	@api.multi
	def design_journaling(self):
		"""
		Open the report interface 
		:return: ir.actions.client
		"""
		self.ensure_one()
		return {
			'type': 'ir.actions.client',
			'tag': 'ps.respective.statements',
			'target': 'current',
			'params': {
				'project_name': self.project_id.name,
				'project_code': self.project_id.code,
				'company_id': self.project_id.company_id.id,
				'currency_id': self.project_id.currency_id.id,
				'project_id': self.project_id.id,
				'organization_id': self.project_id.organization_id.id
			}
		}

	@api.model
	def reported_data(self, success):
		"""Reported data """
		if success == -1:
			return {'status': False, 'message': _("Please save the data and report ")}
		try:
			success = self.browse(success).write({'state': 'archive', 'datetime': datetime.now(), 'app_user': self.env.user.id})
			if success:
				return {'status': True, 'message': _("Report the success ")}
		except AccessError:
			return {'status': False, 'message': _("Report the failure You do not have permission ")}

	@api.model
	def recall(self, success):
		"""Withdraw the report """
		if success == -1:
			return {'status': False, 'message': _("Please save the data and report to withdraw ")}
		try:
			success = self.browse(success).write({'state': 'normal', 'datetime': None, 'app_user': None})
			if success:
				return {'status': True, 'message': _("Withdraw the report successfully")}
		except AccessError:
			return {'status': False, 'message': _("Withdraw the reported failures You do not have permission ")}

	@api.model
	def save(self, state, respective_project, project_id, period, app_company, sheets, custom_functions, validate_rules):
		"""
		Save the report forwarded by the design interface 
		:param validate_rules: The validation rules 
		:param state: state 
		:param respective_project: Report project id
		:param project_id: Set of table template id
		:param period: During the period of id
		:param app_company: Report the organization 
		:param sheets: sheets list
		:param custom_functions: A custom function 
		:return: boolean
		"""
		if state == 'yes':
			project = self.browse(respective_project)
			journalings = project.project_id.journaling_ids
		else:
			if not project_id or not sheets or not period or not app_company:
				return {'status': False, 'message': _('Parameter error')}
			curr_data = self.search([('app_company', '=', int(app_company)), ('project_id', '=', int(project_id)), ('period', '=', fields.Date.from_string(period).strftime('%Y%m')), ('statements_type', '=', 'respective')])
			if curr_data:
				project = curr_data[0]
				journalings = project.project_id.journaling_ids
			else:
				curr_project = {
					'project_id': project_id,
					'period': fields.Date.from_string(period).strftime('%Y%m'),
					'statements_type': 'respective',
					'app_company': app_company
				}
				project = self.create(curr_project)  # Initializes the create project 
				journalings = self.env['ps.combined.statements.journaling.template'].search([('project_id', '=', project_id)])
		journaling = project.journaling_ids
		# First remove 
		if journaling:
			journaling.unlink()
		if project:
			current_project = project
		journaling_ids = list()
		for sheetname, sheetdata in sheets.items():
			rows = list()
			columns_size = list()
			rows_size = list()
			spans = list()

			# Through the data  data => dataTable
			if 'data' in sheetdata.keys():
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
						'size': column.get('size')
					}])
			# Processing line height 
			if 'rows' in sheetdata.keys():
				for row_data in sheetdata.get('rows'):
					rows_size.append([0, False, {
						'size': row_data.get('size')
					}])
			# The report 
			journaling_ids.append([0, False, {
				'rows': rows,
				'name': sheetname,
				'sequence': sheetdata.get('index'),
				'spans': spans,
				'company_id': current_project.company_id.id or self.env.user.company_id.id,
				'currency_id': current_project.currency_id.id,
				'row_count': sheetdata.get('rowCount'),
				'state': 'normal',
				'is_protected': False,
				'journaling_template_id': journalings.filtered(lambda r: r.name == sheetname).id,
				'column_count': sheetdata.get('columnCount'),
				'active': True,
				'project_id': project_id,
				'columns_size': columns_size,
				'rows_size': rows_size,
				'uom': 'million-yuan'
			}])

		try:
			success = current_project.write({
				'journaling_ids': journaling_ids,
				'custom_functions': json.dumps(custom_functions, ensure_ascii=False),
				'validate_rules': json.dumps(validate_rules, ensure_ascii=False)
			})
			if success:
				return {'status': True, 'id': current_project.id, 'message': _("Save success ")}
		except AccessError:
			return {'status': False, 'message': _("Save failed You do not have permission ")}

	@api.model
	def get_sheets(self, repective):
		"""To obtain the report data """
		if not repective:
			_logger.info('Parameter error')
			return {'status': False, 'message': _('Parameter error')}
		project = self.browse(repective)

		if not project.journaling_ids:
			return False

		sheets = dict()
		validate_rules = json.loads(project.validate_rules) if project.validate_rules else list()
		for sheet in project.journaling_ids:
			columns_size = list()
			rows_size = list()
			dataTable = dict()
			spans = list()

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

			for span in sheet.spans:
				spans.append({
					'row': span.row,
					'rowCount': span.row_count,
					'col': span.col,
					'colCount': span.col_count
				})

			for column in sheet.columns_size:
				columns_size.append({
					'size': column.size
				})

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
					sheetCount=len(sheets),
					activeSheetIndex=0
				),
				ValidateRules=validate_rules
			)
			return json.dumps(result, ensure_ascii=False)
		return False

	@api.model
	def save_respective_adj_statements(self, organization_id, period, project_id):
		"""
		Adjustment to generate 
		:param organization_id: Organization name 
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

		if not organization_id or not period or not project_id:
			raise UserError('error  Please pass parameters correctly ')
		_logger.debug(u"organization id===> %s, During the period of ===> %s,  Papers to define id===> %s" % (organization_id.id, period, project_id))
		# For the presence of the project 
		respective_adj_statements = self.search([('app_company', '=', organization_id.id), ('period', '=', period), ('project_id', '=', project_id.id), ('statements_type', '=', 'adjust')])
		# If there are deleted 
		if respective_adj_statements:
			respective_adj_statements.unlink()
		# Take out all the sample table 
		journaling_ids = self.env['ps.combined.statements.journaling.template'].search([('project_id', '=', project_id.id), ('company_id', '=', self.env.user.company_id.id)])
		# Take satisfy the conditions of work papers cell 
		work_paper = self.env['ps.combined.statements.adjust.working.paper.cell'].search([('company_id', '=', self.env.user.company_id.id), ('organization_id', '=', organization_id.id), ('period', '=', period), ('project_id', '=', project_id.id)])
		adj_respective_ids = list()
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
			adj_respective_ids.append([0, False, {
				'sequence': x.sequence,
				'name': x.name,
				'is_protected': x.is_protected,
				'row_count': x.row_count,
				'tail_count': x.tail_count,
				'head_count': x.head_count,
				'column_count': x.column_count,
				'col_offset': x.col_offset,
				'columns_size': columns_size,
				'journaling_template_id': x.id,
				'rows_size': rows_size,
				'uom': x.uom,
				'spans': spans,
				'rows': rows

			}])
		self.create({
			'project_id': project_id.id,
			'journaling_ids': adj_respective_ids,
			'app_company': organization_id.id,
			'period': period,
			'statements_type': 'adjust'
		})


class CombinedStatementsRespectiveStatements(models.Model):
	""" Individual statements  """
	_name = "ps.respective.statements"
	_description = u"Individual statements "

	state = fields.Selection(string="state ", selection=SELECTION, related="project_id.state")
	active = fields.Boolean(string="Active", default=True)
	sequence = fields.Integer(default=10)  # The serial number 
	name = fields.Char(string="Report name ", required=True, translate=True)
	is_protected = fields.Boolean(string="The protected ", default=False)  # The workbook is protected 
	row_count = fields.Integer(string='The total number of rows ')
	tail_count = fields.Integer(string='Table with a few ')
	head_count = fields.Integer(string='The title of rows ')
	column_count = fields.Integer(string='The total number of columns ')
	col_offset = fields.Integer(string='The column offset ', default=0)
	statements_type = fields.Selection(string='Report type ', selection=[('respective', 'Individual statements '), ('adjust', 'adjustment ')], related="project_id.statements_type", store=True)
	journaling_template_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='The sample table ')
	project_id = fields.Many2one(comodel_name="ps.respective.statements.project", string="Set the table name ", ondelete="cascade")
	columns_size = fields.One2many(comodel_name='ps.respective.statements.columnsize', inverse_name='journaling_id', string='The column size ')
	rows_size = fields.One2many(comodel_name="ps.respective.statements.rowsize", inverse_name='journaling_id', string='The line size ')
	spans = fields.One2many(comodel_name='ps.respective.statements.spans', inverse_name='journaling_id', string='Cell combined information ')
	columninfo = fields.One2many(comodel_name='ps.respective.statements.columninfo', inverse_name='journaling_id', string='Column information ')
	rows = fields.One2many(comodel_name='ps.respective.statements.row', inverse_name='journaling_id', string="Reporting line ")
	uom = fields.Selection(string='unit ', selection=[('yuan', 'Yuan'), ('million-yuan', 'million yuan')], default='million-yuan')
	app_company = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Report to the company ', related="project_id.app_company", store=True)
	company_id = fields.Many2one("res.company", string="The company ", index=True, default=lambda self: self.env.user.company_id)
	currency_id = fields.Many2one("res.currency", string="currency ", default=lambda self: self.env.user.company_id.currency_id)
	period = fields.Char(string="During the period of ", size=6, related="project_id.period", store=True)


class CombinedStatementsRespectiveStatementsRow(models.Model):
	""" Reporting line  """
	_name = "ps.respective.statements.row"
	_description = u"Individual reporting line "

	journaling_id = fields.Many2one(comodel_name='ps.respective.statements', ondelete="cascade", string="Journaling")
	state = fields.Selection(string="Status", selection=SELECTION, related="journaling_id.state")
	row_number = fields.Integer(string='Row number')  # The line Numbers 
	cell_ids = fields.One2many(comodel_name='ps.respective.statements.cell', inverse_name='row_id', string='Cells')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="journaling_id.company_id", store=True)


class CombinedStatementsRespectiveStatementsColumninfo(models.Model):
	""" The report column  """
	_name = "ps.respective.statements.columninfo"
	_description = u"Individual report column "

	journaling_id = fields.Many2one(comodel_name='ps.respective.statements', ondelete="cascade", string="Journaling")
	col_coordinate = fields.Integer("Column Coordinate")  # Column coordinates 
	col_name = fields.Char(string='Column Name')
	col_isnumber = fields.Boolean(string='Numeric column', default=False)
	col_isitem = fields.Boolean(string='Item column')


class CombinedStatementsRespectiveStatementsSpans(models.Model):
	"""Individual statements cell combined information """
	_name = "ps.respective.statements.spans"
	_description = u"The cell information individual statements "

	journaling_id = fields.Many2one(comodel_name='ps.respective.statements', ondelete="cascade", string="Journaling")
	row = fields.Integer(string='Row index')
	row_count = fields.Integer(string='Row Count')
	col = fields.Integer(string='Col index')
	col_count = fields.Integer(string='Col Count')


class CombinedStatementsRespectiveStatementsCell(models.Model):
	""" Cell individual statements  """
	_name = "ps.respective.statements.cell"
	_description = u"Cell individual statements "

	row_id = fields.Many2one(comodel_name='ps.respective.statements.row', string='Row', ondelete="cascade")
	journaling_id = fields.Many2one(comodel_name="ps.respective.statements", related="row_id.journaling_id", string="The report ", store=True)
	app_company = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Report to the company ', related="journaling_id.app_company")
	position = fields.Integer(string="location ")
	value = fields.Char(string="value ")
	row_index = fields.Integer(string='The line Numbers ')
	col_index = fields.Integer(string="Column coordinates ")
	formula = fields.Char(string="The formula ")
	style = fields.Char(string="style ")
	cell_isprotected = fields.Char(string='IsProtected')
	cell_rowoffset = fields.Integer(string='Row Offset')
	cell_columnoffset = fields.Integer(string='Column Offset')
	company_id = fields.Many2one("res.company", string="Company", index=True, related="row_id.company_id", store=True)
	period = fields.Char(string="During the period of ", size=6, related="journaling_id.period")

	@api.model
	def get_cell_info(self, journaling_id, row_index, col_index):
		""" Obtain statements cell information 
		:param journaling_id: Individual statements id
		:param row_index: The individual report line coordinates 
		:param col_index: Individual report coordinates 
		:return: object
		"""
		return self.search([('journaling_id', '=', journaling_id), ('row_index', '=', row_index), ('col_index', '=', col_index)])


class CombinedStatementsRespectiveStatementsColumnSize(models.Model):
	""""""
	_name = "ps.respective.statements.columnsize"
	_description = u"Individual report column size "

	journaling_id = fields.Many2one(comodel_name='ps.respective.statements', ondelete="cascade", string="Journaling")
	size = fields.Integer(string='Size')


class CombinedStatementsRespectiveStatementsRowSize(models.Model):
	"""Individual report line size """
	_name = "ps.respective.statements.rowsize"
	_description = u"Individual report line size "

	journaling_id = fields.Many2one(comodel_name='ps.respective.statements', ondelete="cascade", string="Journaling")
	size = fields.Integer(string='Size')
