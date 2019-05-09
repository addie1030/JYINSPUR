# -*- coding: utf-8 -*-
# Created by Jalena at 2018/10/17
import datetime
import json
import logging

from odoo import _
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import ValidationError
# from combined_statements_formulas import is_number

def is_number(val):
	try:
		float(val)
		return True
	except ValueError:
		pass
	try:
		import unicodedata
		unicodedata.numeric(val)
		return True
	except (TypeError, ValueError):
		pass
	return False


_logger = logging.getLogger(__name__)


class CombinedStatementsAdjustWorkingPaperProject(models.Model):
	"""Adjust the working papers """
	_name = "ps.combined.statements.adjust.working.paper.project"

	active = fields.Boolean(string='Active', default=True)
	company_id = fields.Many2one('res.company', string='The company ', default=lambda self: self.env.user.company_id)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string="Set the table ", ondelete="cascade")
	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Organization name ')

	period = fields.Char(string="During the period of ", size=6, copy=False)
	adj_workingpaper_ids = fields.One2many(comodel_name='ps.combined.statements.adjust.working.paper', inverse_name='adj_work_paper_project_id', string='Working papers ', copy=True)

	@api.model
	def adjrecalculate(self, adjworking_papers_project_id):
		"""
		To recalculate the working papers 
		:param adjworking_papers_project_id: But working papers id
		:return:
		"""
		if not adjworking_papers_project_id:
			return {'message': _("Parameter is not correct "), 'state': False}

		# Process calculation data According to the line +Column coordinates to reorganize the data dict This is done to reduce the cycle of data
		def _process_src_data(x):
			src_dict[str(x['row_index'])+'|'+str(x['col_index'])] = x

		start_time = datetime.datetime.now()

		adjworking_paper_project = self.browse(adjworking_papers_project_id)
		update_data = list()
		src_dict = dict()
		for adjworking_paper in adjworking_paper_project.adj_workingpaper_ids:
			src_data = self.get_adj_working_paper_data(adjworking_paper.working_paper_define, adjworking_paper.organization_id, adjworking_paper.period)[-1]
			filter(_process_src_data, map(lambda r: r[-1], src_data))
			# Find all need to recalculate the cell 
			update_cells = adjworking_paper.cell_ids.filtered(lambda r: r.col_index > 3)
			for update_cell in update_cells:
				dict_key = str(update_cell.row_index)+'|'+str(update_cell.col_index)
				update_data.append([1, update_cell.id, {
					'value': src_dict[dict_key]['value'] if dict_key in src_dict.keys() else None,
					'formula': src_dict[dict_key]['formula'] if dict_key in src_dict.keys() else None
				}])
			adjworking_paper.write({'cell_ids': update_data})
		_logger.debug(u"Working papers to time-consuming calculation data  %s", (start_time-datetime.datetime.now()).seconds)
		return {'message': _("completes "), 'state': True}

	@api.model
	def adj_carry_over(self, adj_working_papers, date):
		"""
		But carry forward working papers 
		:param adj_working_papers: ID
		:param date: The date of  201212
		:return:
		"""
		current_date = date[:4]+date[5:]
		current = self.browse(adj_working_papers)
		vals = current.copy_data(default={'period': current_date})

		# Remove the value 
		for working_papers in vals[0]['adj_workingpaper_ids']:
			for working_paper in working_papers:
				if isinstance(working_paper, dict):
					for key, value in working_paper.items():
						if isinstance(value, list) and key == 'cell_ids':
							for cells in value:
								for cell in cells:
									if isinstance(cell, dict):
										for k, v in cell.items():
											if k == 'value_type' and v != 'char':
												cell['value'] = None
		result = self.create(vals[0])
		if result:
			return dict(status=True, message=_('Carry forward successful '))

	@api.model
	def update_adjust_working_papers(self, adj_working_papers_project_id, bind_info, sheets):
		"""
		Update to adjust working papers 
		:param adj_working_papers_project_id: Working paper project id
		:param bind_info: SheetThe binding information 
		:param sheets: Sheets
		:return: dict
		"""
		if not adj_working_papers_project_id and not sheets:
			raise UserWarning(_("Parameter is not correct "))
		start_time = datetime.datetime.now()
		values = list()
		info = json.loads(bind_info)
		for sheetname, sheetvalue in sheets.items():
			# To obtain work papers 
			adj_working_paper = self.env['ps.combined.statements.adjust.working.paper'].browse(info.get(sheetname))
			# To obtain work papers combined series 
			up_col = adj_working_paper.column_ids.filtered(lambda r: r.col_name == u'合并数').col_order
			# To obtain work papers merge cells in series 
			wp_cells = adj_working_paper.cell_ids.filtered(lambda r: r.col_index == int(up_col))

			for wp_cell in wp_cells:
				j = dict()
				val = sheetvalue.get('data').get('dataTable').get(str(wp_cell.row_index)).get(str(wp_cell.col_index))
				if not val:
					values.append((1, wp_cell.id, {'value': None, 'formula': None}))
					continue
				if 'value' in val.keys():
					j['value'] = val.get('value')
				if 'formula' in val.keys():
					j['formula'] = val.get('formula')
				values.append([1, wp_cell.id, j])
			adj_working_paper.write({'cell_ids': values})
			_logger.debug('Update the cell  %s a ', len(wp_cells))
		_logger.debug(u"Working papers for updated time-consuming  %s", (start_time-datetime.datetime.now()).seconds)
		return {'message': _("completes ")}

	@api.model
	def save_adjust_working_papers(self, organization_id, period, tmpl_project):
		"""
		Adjust the working papers 
		:param organization_id: Organization name 
		:param period: str Accounting period (201812)
		:param tmpl_project: Set the table 
		:return:
		"""
		if not organization_id or not period or not tmpl_project:
			raise ValidationError(u"Save the error Please pass parameters correctly ")
		_logger.debug("Organization name ===> %s, During the period of ===> %s,  Set the table ===> %s" % (organization_id.name, period, tmpl_project.name))

		domain = [('organization_id', '=', organization_id.id), ('period', '=', period), ('project_id', '=', tmpl_project.id)]
		project = self.search_count(domain)
		if project > 0:
			raise ValidationError(_("The adjustment work papers already exists "))

		# Find a defined set of table definition work papers 
		adj_working_paper_define_ids = self.env['ps.merge.manuscript.init'].search([('project_id', '=', tmpl_project.id)])

		# Building work papers 
		adj_workingpaper_data = list()
		for define_id in adj_working_paper_define_ids:
			columnInfo, row_data = self.get_adj_working_paper_data(define_id, organization_id, period)
			adj_workingpaper_data.append([0, False, {
				'active': True,
				'company_id': self.env.user.company_id.id,
				'adj_work_paper_project_id': False,
				'project_id': tmpl_project.id,
				'organization_id': organization_id.id,
				'working_paper_define': define_id.id,
				'period': period,
				'cell_ids': row_data,
				'column_ids': columnInfo
			}])

		# save 
		self.create({
			'active': True,
			'company_id': self.env.user.company_id.id,
			'project_id': tmpl_project.id,
			'organization_id': organization_id.id,
			'period': period,
			'adj_workingpaper_ids': adj_workingpaper_data,
		})

	def get_adj_working_paper_data(self, define_id, organization_id, period):
		"""
		Get job finalized define the data structure 
		:param define_id: Define the project 
		:param organization_id: Organization name 
		:param period: During the period of 
		:return:
		"""
		decimal = self.env['ir.config_parameter'].sudo().get_param('combined.statements.decimal')
		fat = '%.{}f'.format(decimal)
		row_data = list()

		# Build storage column information 
		columnInfo = list()
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 0,
			'col_coordinate': 0,
			'col_name': "报表项目",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 1
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 1,
			'col_coordinate': 1,
			'col_name': "项目类型",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 2,
			'col_coordinate': 2,
			'col_name': "余额方向",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 3,
			'col_coordinate': 3,
			'col_name': "合并科目",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 4,
			'col_coordinate': 4,
			'col_name': "组织名称",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 5,
			'col_coordinate': 5,
			'col_name': "合计数",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 6,
			'col_coordinate': 6,
			'col_name': "抵销分录/借",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 7,
			'col_coordinate': 7,
			'col_name': "抵销分录/贷",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 8,
			'col_coordinate': 8,
			'col_name': "少数股东",
			'col_isnumber': 1,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'adj_work_paper_id': False,
			'col_order': 9,
			'col_coordinate': 9,
			'col_name': "合并数",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])

		# Set the table  Sheet
		_journaling_template = define_id.journaling_id

		# Get all the individual report 
		rs = self.env['ps.respective.statements'].search([('journaling_template_id', '=', _journaling_template.id), ('period', 'like', period), ('app_company', '=', organization_id.id), ('state', '=', 'archive'), ('statements_type', '=', 'respective')])

		# Get all the individual report submitted to cell 
		rcs_cell = self.env['ps.respective.statements.cell'].search([('journaling_id', 'in', rs.ids)])

		# Set the table  SheetDefined in the column information 
		define_ids = self.env['ps.combined.statements.journaling.template.define'].search([('journaling_id', '=', define_id.journaling_id.id)])

		# Get papers definition in all the subjects 
		subject_ids = [x.merge_subject.id for x in define_id.init_line_ids]

		# Gets the current date All merge sort of offset entry combined by subject value of the organization
		eliminationentry = self.env['ps.combined.statements.elimination.entry']
		# Through the organization During the period of Papers that are defined in the subject to get the total value
		es_values = eliminationentry.get_sumvalues_by_adj_subject(organization_id, period, subject_ids)

		def get_value(values, key, key1):
			val = 0
			if isinstance(values, list):
				for value in values:
					if key in value.keys():
						val = value.get(key).get(key1)
			return val

		# Build a line  Loop merging papers definition
		for define_line in define_id.init_line_ids:

			sum_value = list()

			# Report project 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 0,
				'value': define_line.cell_id.value,
				'value_type': 'char',
				'formula': None
			}])
			# Project type 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 1,
				'value': define_line.line_project_id.name,
				'value_type': 'char',
				'formula': None
			}])
			# The balance of the direction 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 2,
				'value': '借' if define_line.balance_dirextin == 'debit' else '贷',
				'value_type': 'char',
				'formula': None
			}])
			# Merging subject 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3,
				'value': define_line.merge_subject.name,
				'value_type': 'char',
				'formula': None
			}])

			# By sampling all the corresponding column in the table definition information 
			tmpl_col_num = [x.col_index for x in define_ids.filtered(lambda r: r.col_type == define_line.line_project_id)]  # [2,6]
			tmpl_row_num = define_line.cell_id.row_index

			# Handle your company merge sort individual reporting data 
			# Judge set table SheetDefined in the column offset value  If it is 0 Don't do data migration  Take the first data directly
			# Jax
			value_index = 0 if _journaling_template.col_offset == 0 else int(define_line.col_index / _journaling_template.col_offset)
			if isinstance(tmpl_col_num, list):
				cell_value = rcs_cell.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num[value_index] and r.app_company.id == organization_id.id).value
			else:
				cell_value = rcs_cell.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num and r.app_company.id == organization_id.id).value
			if not cell_value:
				cell_value = '0.0'
			sum_value.append(eval(cell_value))
			# Organization name 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 4,
				'value': fat % float(cell_value) if is_number(cell_value) else fat % float(cell_value),
				'value_type': 'float',
				'formula': None
			}])
			# total 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 5,
				'value': fat % float(sum(sum_value)) if is_number(sum(sum_value)) else fat % float(sum(sum_value)),
				'value_type': 'float',
				'formula': None
			}])
			# Offset entries  borrow 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 6,
				'value': fat % float(get_value(es_values, define_line.merge_subject.id, 'debit')) if is_number(get_value(es_values, define_line.merge_subject.id, 'debit')) else fat % float(get_value(es_values, define_line.merge_subject.id, 'debit')),
				'value_type': 'float',
				'formula': None
			}])
			# Offset entries  credit 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 7,
				'value': fat % float(get_value(es_values, define_line.merge_subject.id, 'credit')) if is_number(get_value(es_values, define_line.merge_subject.id, 'debit')) else fat % float(get_value(es_values, define_line.merge_subject.id, 'debit')),
				'value_type': 'float',
				'formula': None
			}])
			# Minority shareholders 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 8,
				'value': None,  # TODO Waiting for the calculation rules 
				'value_type': 'float',
				'formula': None
			}])
			# Number of merger 
			row_data.append([0, False, {
				'adj_work_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 9,
				'src_row_index': define_line.row_index,
				'src_col_index': define_line.col_index,
				'src_journaling_id': define_line.journaling_id.id,
				'src_columntype_id': define_line.line_project_id.id,
				'project_col_index': define_line.project_col_index,
				'value': None,  # TODO Waiting for the calculation rules 
				'value_type': 'float',
				'formula': None
			}])
		return columnInfo, row_data

	@api.model
	def get_adjust_working_papers(self, model_id):
		"""
		To obtain work papers data 
		:param model_id: model id
		:return: dict
		"""
		if not model_id:
			raise UserWarning(u"Did not get right to the information inquiry work papers to you need to look at ")

		working_papers = self.browse(model_id)
		datatable = list()

		# Iterate through all the working papers 
		for working_paper in working_papers.adj_workingpaper_ids:
			sheet = list()
			bingInfo = list()
			cells = working_paper.cell_ids
			column_ids = working_paper.column_ids
			sheetname = working_paper.working_paper_define.journaling_id.name

			# Build the front line display collections 
			for num in range(len(working_paper.working_paper_define.init_line_ids)):
				row = dict()
				for col in column_ids.sorted(key=lambda r: r.col_order):
					row[col.col_name] = cells.filtered(lambda j: j.row_index == num and j.col_index == col.col_coordinate).value or None
				sheet.append(row)

			# Build the front display column information 
			for column_id in column_ids.sorted(key=lambda r: r.col_coordinate):
				bingInfo.append({
					'name': column_id.col_name,
					'displayName': column_id.col_name,
					'size': 400 if column_id.col_isitem == '1' else 110,
					'formatter': '0.00' if column_id.col_isnumber == '1' else False
				})
			datatable.append({'data': sheet, 'bindInfo': bingInfo, 'name': sheetname, 'id': working_paper.id})

		return json.dumps(datatable, ensure_ascii=False)

	@api.model
	def get_adjust_working_papers_sheets(self, model_id):
		"""To obtain work papers reports JSONdata """
		if not model_id:
			return {'status': False, 'message': _('Parameter error ')}
		start_time = datetime.datetime.now()
		# To obtain work papers 
		adjust_working_papers_project = self.browse(model_id)

		if not adjust_working_papers_project.adj_workingpaper_ids:
			return False

		sheets = dict()
		bindInfo = dict()
		index = 0
		for adj_workingpaper in adjust_working_papers_project.adj_workingpaper_ids:
			bindInfo[adj_workingpaper.working_paper_define.journaling_id.name+'['+adj_workingpaper.working_paper_define.line_project_id.name+']'] = adj_workingpaper.id
			cells = adj_workingpaper.cell_ids
			columns = list()
			colHeaderData = dict()
			dataTable = dict()

			for num in range(len(adj_workingpaper.working_paper_define.init_line_ids)):
				sheet_cells = dict()
				for col in adj_workingpaper.column_ids.sorted(key=lambda r: r.col_order):
					sheet_cells[col.col_coordinate] = {
						'value': cells.filtered(lambda r: r.row_index == num and r.col_index == col.col_coordinate).value or None,
						'formula': cells.filtered(lambda r: r.row_index == num and r.col_index == col.col_coordinate).formula or None
					}
				dataTable[num] = sheet_cells

			for col in adj_workingpaper.column_ids.sorted(key=lambda r: r.col_order):
				columns.append({
					'name': col.col_name,
					'displayName': col.col_name,
					'size': 400 if col.col_isitem == '1' else 110,
					'formatter': '0.00' if col.col_isnumber == '1' else None
				})
				colHeaderData[col.col_coordinate] = dict(value=col.col_name)

			# organization Sheetformat 
			# sheets[workingpaper.working_paper_define.journaling_id.name + '[' + workingpaper.working_paper_define.line_project_id.name + ']'] = {
			sheets[adj_workingpaper.id] = {
				'name': adj_workingpaper.working_paper_define.journaling_id.name+'['+adj_workingpaper.working_paper_define.line_project_id.name+']',
				'rowCount': len(adj_workingpaper.working_paper_define.init_line_ids),
				'columnCount': len(adj_workingpaper.column_ids),
				'activeRow': 0,
				'activeCol': 0,
				'columns': columns,
				'rows': [],
				'spans': [],
				'theme': 'Office',
				'rowHeaderData': {
					'defaultDataNode': {
						'style': {
							'themeFont': 'Body'
						}
					}
				},
				'colHeaderData': {
					'dataTable': {'0': colHeaderData}
				},
				'data': {
					'dataTable': dataTable,
					'defaultDataNode': {
						'style': {
							'themeFont': 'Body'
						}
					}
				},
				'index': index
			}
			index += 1

		_logger.debug(u"Access to adjust working paper data time-consuming  %s", (start_time-datetime.datetime.now()).seconds)
		if sheets:
			result = {'spread': dict(version="9.40.20161.0", sheets=sheets, newTabVisible=False, tabEditable=False, tabNavigationVisible=False, sheetCount=len(sheets), activeSheetIndex=0), 'bindInfo': bindInfo}
			return json.dumps(result, ensure_ascii=False)
		return False


class CombinedStatementsAdjustWorkingPaper(models.Model):
	"""Adjust the working papers """
	_name = "ps.combined.statements.adjust.working.paper"

	active = fields.Boolean(string='Active', default=True)
	company_id = fields.Many2one('res.company', string='The company ', default=lambda self: self.env.user.company_id)
	adj_work_paper_project_id = fields.Many2one(comodel_name='ps.combined.statements.adjust.working.paper.project', ondelete='cascade', string='Adjust the working papers ')
	code = fields.Char(u"Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string="Set the table ", ondelete="cascade")
	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Organization name ')
	working_paper_define = fields.Many2one(comodel_name='ps.merge.manuscript.init', string="Working paper defined ")
	period = fields.Char(string="During the period of ", size=6)
	cell_ids = fields.One2many(comodel_name='ps.combined.statements.adjust.working.paper.cell', inverse_name='adj_work_paper_id', string="The cell ", copy=True)
	column_ids = fields.One2many(comodel_name='ps.combined.statements.adjust.working.paper.columns', inverse_name='adj_work_paper_id', string="Column information ", copy=True)

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('adjust.working.paper.seq') or _('New')
		return super(CombinedStatementsAdjustWorkingPaper, self).create(vals)


class CombinedStatementsAdjustWorkingPaperColumns(models.Model):
	"""Adjust the working papers column information """
	_name = "ps.combined.statements.adjust.working.paper.columns"

	adj_work_paper_id = fields.Many2one(comodel_name="ps.combined.statements.adjust.working.paper", ondelete="cascade", string="Adjust the working papers ", copy=False)
	adj_work_paper_code = fields.Char(string="Manuscript number ", related="adj_work_paper_id.code", store=True)
	col_order = fields.Char(String="The column number ", Requird=True)
	col_coordinate = fields.Integer(String="Column coordinates ", Requird=True)
	col_name = fields.Char(String="Column name ", Requird=True)
	col_isnumber = fields.Char(String="Numeric columns ", Requird=True)
	col_isamount = fields.Char(String="Summary column ", Requird=True)
	col_isadjust = fields.Char(String="Adjust the column ", Requird=True)
	col_isitem = fields.Char(String="The project list ", Requird=True)


class CombinedStatementsAdjustWorkingPaperCell(models.Model):
	"""Adjust the unit working papers """
	_name = 'ps.combined.statements.adjust.working.paper.cell'

	adj_work_paper_id = fields.Many2one(comodel_name="ps.combined.statements.adjust.working.paper", ondelete="cascade", string="Adjust the working papers ", copy=False)
	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', related="adj_work_paper_id.organization_id", string='Organization name ', store=True)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", related="adj_work_paper_id.project_id", string="Set the table ", ondelete="cascade")
	period = fields.Char(string="During the period of ", size=6, related="adj_work_paper_id.period", store=True)
	adj_work_paper_code = fields.Char(string="Manuscript number ", related="adj_work_paper_id.code", store=True)
	row_index = fields.Integer(string="Line coordinates ")
	col_index = fields.Integer(string="Column coordinates ")
	src_row_index = fields.Integer(string="Source line coordinates ")
	src_col_index = fields.Integer(string="Source column coordinates ")
	src_journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='Source statements ')
	is_protected = fields.Boolean(string="Whether to protect ", default=False)
	value_type = fields.Selection(string="Value types ", selection=[('char', u"The text "), ('float', u"The numerical "), ], default='char')
	value = fields.Char(string="value ")
	precision = fields.Integer(String="precision ", Requird=False)
	formula = fields.Char(string="The formula ")
	company_id = fields.Many2one("res.company", string="The company ", related="adj_work_paper_id.company_id", store=True)
	project_col_index = fields.Integer(string="Project type offset column coordinates ")
	src_columntype_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.columntype', string='Source project type ')
