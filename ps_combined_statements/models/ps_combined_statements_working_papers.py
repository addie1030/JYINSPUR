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
# from combined_statements_journaling_template import CUSTOMFUNCTIONS
CUSTOMFUNCTIONS = '{"GET": {"typeName": "namespace.AsyncFormulas", "maxArgs": 255, "minArgs": 0, "name": "GET"}}'


_logger = logging.getLogger(__name__)


def convent_column_to_char(column):
	"""
	Converts Numbers Excelcolumn 
	1 => A, 2 => B, ......, 27 => AA
	:param column: int
	:return: str
	"""
	if not isinstance(column, int):
		return column
	tStr = str()
	while column != 0:
		res = column % 26
		if res == 0:
			res = 26
			column -= 26
		tStr = chr(ord('A') + res - 1) + tStr
		column = column // 26
	return tStr


def colname_to_num(colname):
	"""
	conversion ExcelColumn Numbers for Numbers 
	A => 1, B => 2, ......, 27 => AA
	:param colname: Column number 
	:return: int
	"""
	if not isinstance(colname, str):
		return colname
	col = 0
	power = 1

	for i in xrange(len(colname) - 1, -1, -1):
		ch = colname[i]
		col += (ord(ch) - ord('A') + 1) * power
		power *= 26
	return col - 1


class CombinedStatementsWorkingPaperProject(models.Model):
	"""Working paper project """
	_name = "ps.combined.statements.working.paper.project"

	active = fields.Boolean(string='Active', default=True)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string="Set the table ", ondelete="cascade")
	merger_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ')
	custom_functions = fields.Text(string="A custom function ", default=CUSTOMFUNCTIONS)
	period = fields.Char(string="During the period of ", size=6, copy=False)
	workingpaper_ids = fields.One2many(comodel_name='ps.combined.statements.working.paper', inverse_name='working_paper_project_id', string='Working papers ', copy=True)

	@api.model
	def update_working_papers(self, working_papers_project_id, bind_info, sheets):
		"""
		Update the working paper 
		:param working_papers_project_id: Working papers ID
		:param bind_info: SheetThe binding information 
		:param sheets: Sheets
		:return: dict
		"""
		if not working_papers_project_id and not sheets:
			raise UserWarning(u"Parameter is not correct ")
		start_time = datetime.datetime.now()
		values = list()
		info = json.loads(bind_info)
		for sheetname, sheetvalue in sheets.items():
			working_paper = self.env['ps.combined.statements.working.paper'].browse(info.get(sheetname))
			up_col = working_paper.column_ids.filtered(lambda r: r.col_name == u'合并数').col_order
			wp_cells = working_paper.cell_ids.filtered(lambda r: r.col_index == int(up_col))

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
			working_paper.write({'cell_ids': values})
			_logger.info('Update the cell  %s a ', len(wp_cells))
		_logger.info(u"Working papers for updated time-consuming  %s", (start_time - datetime.datetime.now()).seconds)
		return {'message': _("completes ")}

	@api.model
	def save_working_papers(self, org, period, tmpl):
		"""
		Save the work papers 
		:param org: Merging organizations 
		:param period: str Accounting period (201812)
		:param tmpl: Set the table 
		:return:
		"""
		if not org or not period or not tmpl:
			raise ValidationError(u"Save the error Please pass parameters correctly ")
		_logger.debug(u"classification ===> %s, During the period of ===> %s,  Set the table ===> %s" % (org.name, period, tmpl.name))

		domain = [('merger_organization', '=', org.id), ('period', '=', period), ('project_id', '=', tmpl.id)]
		project = self.search(domain, count=True)
		if project > 0:
			raise ValidationError(u"The working papers already exists ")

		# According to the set of table definition to find all the papers 
		working_paper_define_ids = self.env['ps.merge.manuscript.init'].search([('project_id', '=', tmpl.id)])

		# Building work papers 
		workingpaper_data = list()
		start_time = datetime.datetime.now()
		for define_id in working_paper_define_ids:
			columnInfo, row_data = self.get_working_paper_data(define_id, org, period)
			workingpaper_data.append([0, False, {
				'active': True,
				'company_id': self.env.user.company_id.id,
				'working_paper_project_id': False,
				'project_id': tmpl.id,
				'merger_organization': org.id,
				'working_paper_define': define_id.id,
				'period': period,
				'cell_ids': row_data,
				'column_ids': columnInfo
			}])
		_logger.info(u"Working papers to save data to construct the time-consuming  %s", (start_time - datetime.datetime.now()).seconds)

		# save 
		self.create({
			'active': True,
			'company_id': self.env.user.company_id.id,
			'project_id': tmpl.id,
			'merger_organization': org.id,
			'period': period,
			'workingpaper_ids': workingpaper_data,
			'custom_functions': CUSTOMFUNCTIONS
		})

	def get_working_paper_data(self, define, org, period):
		"""
		Get job finalized define the data structure 
		:param define: Working paper defined 
		:param org: Merging organizations 
		:param period: During the period of (str)
		:return:
		"""
		global cell_value

		row_data = list()
		org_count = len(org.child_ids)

		# Build storage column information 
		columnInfo = list()
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 0,
			'col_coordinate': 0,
			'col_name': "报告项目",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 1
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 1,
			'col_coordinate': 1,
			'col_name': "项目类型",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 2,
			'col_coordinate': 2,
			'col_name': "方向平衡",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3,
			'col_coordinate': 3,
			'col_name': "合并主题",
			'col_isnumber': 0,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		col_num = 1
		for current_org in org.child_ids:
			columnInfo.append([0, False, {
				'working_paper_id': False,
				'col_order': 3 + col_num,
				'col_coordinate': 3 + col_num,
				'col_name': current_org.name,
				'col_isnumber': 1,
				'col_isamount': 0,
				'col_isadjust': 0,
				'col_isitem': 0
			}])
			col_num = col_num + 1
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3 + org_count + 1,
			'col_coordinate': 3 + org_count + 1,
			'col_name': "全部",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3 + org_count + 2,
			'col_coordinate': 3 + org_count + 2,
			'col_name': "抵销分录/借款",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3 + org_count + 3,
			'col_coordinate': 3 + org_count + 3,
			'col_name': "抵销分录/贷方",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3 + org_count + 4,
			'col_coordinate': 3 + org_count + 4,
			'col_name': "少数股东",
			'col_isnumber': 1,
			'col_isamount': 0,
			'col_isadjust': 0,
			'col_isitem': 0
		}])
		columnInfo.append([0, False, {
			'working_paper_id': False,
			'col_order': 3 + org_count + 5,
			'col_coordinate': 3 + org_count + 5,
			'col_name': "合并数",
			'col_isnumber': 1,
			'col_isamount': 1,
			'col_isadjust': 0,
			'col_isitem': 0
		}])

		# Set the table  Sheet
		_journaling_template = define.journaling_id

		# Get all the individual report report data cell 
		# If the entity is adjusted  Take adjustment  Don't take individual statements
		# If it is a merger of companies Then take it consolidated For organizational judgment conditions  Entity to Falsethe
		rs = self.env['ps.respective.statements'].search([('journaling_template_id', '=', _journaling_template.id), ('period', 'like', period), ('app_company', 'in', org.child_ids.ids), ('state', '=', 'archive')])

		# Filter out the adjustment form 
		adjust = rs.filtered(lambda r: r.statements_type == 'adjust')

		# Take out a sheet of the company ID
		adjust_org_ids = [x.app_company.id for x in adjust if adjust]

		# According to the adjustment of the company ID Find out the current set of corresponding individual statements
		rp = rs.filtered(lambda r: r.app_company.id in adjust_org_ids and r.statements_type == 'respective')

		# Take out the data set 
		diff = rs - rp
		rcs_cell = self.env['ps.respective.statements.cell'].search([('journaling_id', 'in', diff.ids)])

		# Take a consolidated data unit 
		merge_statements_cells = self.env['ps.combined.statements.merge.statements.cell']
		if org.child_ids.filtered(lambda r: not r.is_entity_company):
			merge_statements = self.env['ps.combined.statements.merge.statements'].search([('src_journaling_id', '=', _journaling_template.id), ('period', '=', period), ('merge_organization', 'in', org.child_ids.ids)])
			merge_statements_cells = merge_statements_cells.search([('merge_id', 'in', merge_statements.ids)])

			_logger.debug('consolidated id %s' % merge_statements.ids)
		_logger.debug('The total number of consolidated cell  %s' % merge_statements_cells)

		# Set the table  SheetDefined in the column information 
		define_ids = define.journaling_id.define_ids

		# Get papers definition in all the subjects 
		subject_ids = [x.merge_subject.id for x in define.init_line_ids if x.merge_subject]

		# Gets the current date All offset entries total value by subject
		CombinedStatementsEliminationEntry = self.env['ps.combined.statements.elimination.entry']
		es_values = CombinedStatementsEliminationEntry.get_sumvalues_by_org(period, org, subject_ids)

		def get_value(values, key, key1):
			val = 0
			if isinstance(values, list):
				for value in values:
					if key in value.keys():
						val = value.get(key).get(key1)
			return val

		def legal_numbers(s):
			try:
				float(s)
			except ValueError:
				return False
			else:
				return True

		# Build a line Loop merging papers definition
		for define_line in define.init_line_ids:

			# Calculate the current line merge sort of total value of all individual reporting data  All value of the current loop in it for the final total unity
			sum_value = list()

			# Report project 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 0,
				'value': define_line.cell_id.value,
				'value_type': 'char',
				'formula': None
			}])
			# Project type 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 1,
				'value': define_line.line_project_id.name,
				'value_type': 'char',
				'formula': None
			}])
			# The balance of the direction 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 2,
				'value': 'borrow ' if define_line.balance_dirextin == 'debit' else 'credit ',
				'value_type': 'char',
				'formula': None
			}])
			# Merging subject 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3,
				'value': define_line.merge_subject.name,
				'value_type': 'char',
				'formula': None
			}])

			# By sampling all the corresponding column in the table definition information 
			tmpl_col_num = [x.col_index for x in define_ids.filtered(lambda r: r.col_type == define_line.line_project_id)]  # [2,6]
			_logger.debug('Column information  %s' % tmpl_col_num)
			tmpl_row_num = define_line.cell_id.row_index

			# Handle your company merge sort individual reporting data 
			_num = 1
			for current_org in org.child_ids:
				# Judge set table SheetDefined in the column offset value  If it is 0 Don't do data migration  Take the first data directly
				# Jax
				value_index = 0 if _journaling_template.col_offset == 0 else int(define_line.col_index / _journaling_template.col_offset)

				_logger.debug('The subscript  %s' % value_index)

				# Take entity 
				if current_org.is_entity_company:
					if isinstance(tmpl_col_num, list):
						cell_value = rcs_cell.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num[value_index] and r.app_company == current_org).value
					else:
						cell_value = rcs_cell.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num and r.app_company == current_org).value
				# Take a virtual integrated companies 
				elif not current_org.is_entity_company:
					if isinstance(tmpl_col_num, list):
						cell_value = merge_statements_cells.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num[value_index] and r.merge_organization == current_org).value
						_logger.debug('Consolidated cell data  %s' % cell_value)
					else:
						cell_value = merge_statements_cells.filtered(lambda r: r.row_index == tmpl_row_num and r.col_index == tmpl_col_num and r.merge_organization == current_org).value
						_logger.debug('Consolidated cell data  %s' % cell_value)
				if not cell_value or not legal_numbers(cell_value):
					cell_value = '0.0'
				_logger.debug(cell_value)
				sum_value.append(eval(cell_value))
				row_data.append([0, False, {
					'working_paper_id': False,
					'row_index': define_line.sequence,
					'col_index': 3 + _num,
					'value': cell_value,
					'value_type': 'float',
					'formula': None
				}])
				_num += 1
			_logger.debug(sum_value)
			# total 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3 + org_count + 1,
				'value': sum(sum_value),
				'value_type': 'float',
				'formula': None
			}])
			# Offset entries  borrow 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3 + org_count + 2,
				'value': get_value(es_values, define_line.merge_subject.id, 'debit'),
				'value_type': 'float',
				'formula': None
			}])

			# Offset entries  credit 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3 + org_count + 3,
				'value': get_value(es_values, define_line.merge_subject.id, 'credit'),
				'value_type': 'float',
				'formula': None
			}])
			# Minority shareholders 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3 + org_count + 4,
				'value': None,  # TODO Waiting for the calculation rules 
				'value_type': 'float',
				'formula': None
			}])
			# Number of merger 
			row_data.append([0, False, {
				'working_paper_id': False,
				'row_index': define_line.sequence,
				'col_index': 3 + org_count + 5,
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
	def get_working_papers(self, model_id):
		"""
		To obtain work papers data 
		:param model_id: model id
		:return: {'data': [{...}], 'bindInfo': [{....}], 'name': str, 'id': int}
		"""
		if not model_id:
			raise UserWarning(u"Did not get right to the information inquiry work papers to you need to look at ")

		working_papers = self.browse(model_id)
		datatable = list()

		start_time = datetime.datetime.now()

		# Iterate through all the working papers 
		for working_paper in working_papers.workingpaper_ids:
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

		_logger.debug(u"To obtain work papers data time-consuming  %s", (start_time - datetime.datetime.now()).seconds)

		return json.dumps(datatable, ensure_ascii=False)

	@api.model
	def get_working_papers_sheets(self, model_id):
		"""Obtain statements JSONdata """
		if not model_id:
			return {'status': False, 'message': _('Parameter error ')}
		start_time = datetime.datetime.now()
		working_papers_project = self.browse(model_id)

		if not working_papers_project.workingpaper_ids:
			return False

		sheets = dict()
		bindInfo = dict()
		index = 0
		for workingpaper in working_papers_project.workingpaper_ids:
			bindInfo[workingpaper.working_paper_define.journaling_id.name + '[' + workingpaper.working_paper_define.line_project_id.name + ']'] = workingpaper.id
			cells = workingpaper.cell_ids
			columns = list()
			colHeaderData = dict()
			dataTable = dict()

			for num in range(len(workingpaper.working_paper_define.init_line_ids)):
				sheet_cells = dict()
				for col in workingpaper.column_ids.sorted(key=lambda r: r.col_order):
					sheet_cells[col.col_coordinate] = {
						'value': cells.filtered(lambda r: r.row_index == num and r.col_index == col.col_coordinate).value or None,
						'formula': cells.filtered(lambda r: r.row_index == num and r.col_index == col.col_coordinate).formula or None
					}
				dataTable[num] = sheet_cells

			for col in workingpaper.column_ids.sorted(key=lambda r: r.col_order):
				columns.append({
					'name': col.col_name,
					'displayName': col.col_name,
					'size': 400 if col.col_isitem == '1' else 110,
					'formatter': '0.00' if col.col_isnumber == '1' else None
				})
				colHeaderData[col.col_coordinate] = dict(value=col.col_name)

			# organization Sheetformat 
			# sheets[workingpaper.working_paper_define.journaling_id.name + '[' + workingpaper.working_paper_define.line_project_id.name + ']'] = {
			sheets[workingpaper.id] = {
				'name': workingpaper.working_paper_define.journaling_id.name + '[' + workingpaper.working_paper_define.line_project_id.name + ']',
				'rowCount': len(workingpaper.working_paper_define.init_line_ids),
				'columnCount': len(workingpaper.column_ids),
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

		_logger.debug(u"To obtain work papers data time-consuming  %s", (start_time - datetime.datetime.now()).seconds)
		if sheets:
			result = dict(
				spread=dict(
					version="9.40.20161.0",
					sheets=sheets,
					customFunctions=json.loads(working_papers_project.custom_functions),
					newTabVisible=False,
					tabEditable=True,
					tabNavigationVisible=False,
					sheetCount=len(sheets),
					activeSheetIndex=0
				),
				bindInfo=bindInfo
			)
			return json.dumps(result, ensure_ascii=False)
		return False

	@api.model
	def carry_over(self, working_papers, date):
		"""
		Carry forward work papers 
		:param working_papers: ID
		:param date: The date of  201212
		:return:
		"""
		current_date = date[:4] + date[5:]
		current = self.browse(working_papers)
		vals = current.copy_data(default={'period': current_date})

		# Remove the value 
		for working_papers in vals[0]['workingpaper_ids']:
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
	def recalculate(self, working_papers_project_id):
		"""
		To recalculate the working papers 
		:param working_papers_project_id:
		:return:
		"""
		if not working_papers_project_id:
			return {'message': _("Parameter is not correct "), 'state': False}

		# Process calculation data  According to the line +Column coordinates to reorganize the data dict This is done to reduce the cycle of data
		def _process_src_data(x):
			src_dict[str(x['row_index']) + '|' + str(x['col_index'])] = x

		start_time = datetime.datetime.now()

		working_paper_project = self.browse(working_papers_project_id)
		update_data = list()
		src_dict = dict()
		for working_paper in working_paper_project.workingpaper_ids:
			src_data = self.get_working_paper_data(working_paper.working_paper_define, working_paper.merger_organization, working_paper.period)[-1]
			filter(_process_src_data, map(lambda r: r[-1], src_data))
			# Find all need to recalculate the cell 
			update_cells = working_paper.cell_ids.filtered(lambda r: r.col_index > 3)
			for update_cell in update_cells:
				dict_key = str(update_cell.row_index) + '|' + str(update_cell.col_index)
				update_data.append([1, update_cell.id, {
					'value': src_dict[dict_key]['value'] if dict_key in src_dict.keys() else None,
					'formula': src_dict[dict_key]['formula'] if dict_key in src_dict.keys() else None
				}])
			working_paper.write({'cell_ids': update_data})
		_logger.debug(_("Working papers to time-consuming calculation data  %s"), (start_time - datetime.datetime.now()).seconds)
		return {'message': _("completes "), 'state': True}


class CombinedStatementsWorkingPaper(models.Model):
	"""Working papers """
	_name = "ps.combined.statements.working.paper"

	active = fields.Boolean(string='Active', default=True)
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
	working_paper_project_id = fields.Many2one(comodel_name='ps.combined.statements.working.paper.project', ondelete='cascade', string='Working paper project ', copy=False)
	code = fields.Char(u"Serial number ", copy=False, default=lambda self: _('New'), readonly=True)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", string="Set the table ", ondelete="cascade")
	merger_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ')
	working_paper_define = fields.Many2one(comodel_name='ps.merge.manuscript.init', string="Working paper defined ")
	period = fields.Char(string="During the period of ", size=6, related='working_paper_project_id.period', store=True)
	cell_ids = fields.One2many(comodel_name='ps.combined.statements.working.paper.cell', inverse_name='working_paper_id', string="The cell ", copy=True)
	column_ids = fields.One2many(comodel_name='ps.combined.statements.working.paper.columns', inverse_name='working_paper_id', string="Column information ", copy=True)

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('working.paper.seq') or _('New')
		return super(CombinedStatementsWorkingPaper, self).create(vals)


class CombinedStatementsWorkingPaperColumns(models.Model):
	"""Working papers column information """
	_name = "ps.combined.statements.working.paper.columns"

	working_paper_id = fields.Many2one(comodel_name="ps.combined.statements.working.paper", ondelete="cascade", string="Working papers ", copy=False)
	working_paper_code = fields.Char(string="Manuscript number ", related="working_paper_id.code", store=True)
	col_order = fields.Char(String="The column number ", Requird=True)
	col_coordinate = fields.Integer(String="Column coordinates ", Requird=True)
	col_name = fields.Char(String="Column name ", Requird=True)
	col_isnumber = fields.Char(String="Numeric columns ", Requird=True)
	col_isamount = fields.Char(String="Summary column ", Requird=True)
	col_isadjust = fields.Char(String="Adjust the column ", Requird=True)
	col_isitem = fields.Char(String="The project list ", Requird=True)


class CombinedStatementsWorkingPaperCell(models.Model):
	"""Unit of work papers """
	_name = 'ps.combined.statements.working.paper.cell'

	working_paper_id = fields.Many2one(comodel_name="ps.combined.statements.working.paper", ondelete="cascade", string="Working papers ", copy=False)
	working_paper_project_id = fields.Many2one(comodel_name='ps.combined.statements.working.paper.project', related="working_paper_id.working_paper_project_id", string='Working paper project ')
	period = fields.Char(string="During the period of ", related="working_paper_id.period", size=6)
	project_id = fields.Many2one(comodel_name="ps.combined.statements.project", related="working_paper_id.project_id", string="Set the table ", ondelete="cascade")
	merger_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='restrict', string='Merging organizations ', related="working_paper_id.merger_organization")
	working_paper_code = fields.Char(string="Manuscript number ", related="working_paper_id.code", store=True)
	row_index = fields.Integer(string="Line coordinates ")
	col_index = fields.Integer(string="Column coordinates ")
	src_row_index = fields.Integer(string="Source line coordinates ")
	src_col_index = fields.Integer(string="Source column coordinates ")
	src_journaling_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template', string='Source statements ')
	is_protected = fields.Boolean(string="Whether to protect ", default=False)
	value_type = fields.Selection(string="Value types ", selection=[('char', u"The text "), ('float', u"The numerical ")], default='char')
	value = fields.Char(string="value ")
	precision = fields.Integer(String="precision ", Requird=False)
	formula = fields.Char(string="The formula ")
	company_id = fields.Many2one("res.company", string="Company", related="working_paper_id.company_id", store=True)
	project_col_index = fields.Integer(string="Project type offset column coordinates ")
	src_columntype_id = fields.Many2one(comodel_name='ps.combined.statements.journaling.template.columntype', string='Source project type ')
