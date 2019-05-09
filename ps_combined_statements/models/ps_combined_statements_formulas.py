# -*- coding: utf-8 -*-
import logging
import re
from ast import literal_eval
from datetime import date

from odoo import api
from odoo import fields
from odoo import models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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


class CombinedStatementsFormulas(models.Model):
	"""The report formula """
	_name = 'ps.combined.statements.formulas'
	_description = 'The report formula '

	name = fields.Char(String="Formula name ", Requird=True)
	formula_summary = fields.Char(String="Formula describing ", Requird=False)
	formula_object = fields.Char(String="Access the object ", Requird=False)
	formula_design = fields.Text(String="Formula model ", Requird=True, Help="double ## define the parameters, For example, #ACCOUNT#")
	formula_type = fields.Selection([('system', 'system '), ('custom', 'The custom ')], String="Formula type ", Requird=True, default='custom')
	formula_note = fields.Char(String="note ", Requird=False)
	formula_params_ids = fields.One2many('ps.combined.statements.formulas.params', 'formula_id', String='Formula parameters ')

	@api.constrains('formula_design')
	def _constrains_formula_design(self):
		pattern = "([\\w]+)"
		first_word = re.search(pattern, self.formula_design).group(1)
		if first_word.lower() != 'select':
			raise ValidationError(_('You have set SQLBeyond the allowable permissions  Can only use the query '))

	@api.onchange('formula_design')
	def _onchange_formula_design(self):
		if self.formula_design:
			return {'warning': {
				'title': _("Prompt information "),
				'message': _("Formula model has changed  Need to click  Generate the formula parameters  To regenerate the formula parameters  ")
			}}

	def create_params(self):
		"""
		Create a formula 
		:return:
		"""
		result = dict()
		params = list()
		if self.formula_design:
			formula = self.formula_design
			if formula.find('#') > 0:
				parmstr = formula[formula.find('#') + 1:]
				count = 1
				while parmstr.find('#') > 0:
					key = 'param' + str(count)
					temp = parmstr[0:parmstr.find('#')]
					result[key] = '#' + temp + '#'
					parmstr = parmstr[parmstr.find('#') + 1:]
					parmstr = parmstr[parmstr.find('#') + 1:]
					count = count + 1
		else:
			raise ValidationError(_('Model parameters is derived from the formula Please first maintenance model of the formula '))
		if len(result) > 0:
			index = 1
			period_obj = self.env['ps.combined.statements.formulas.params']
			record_ids = period_obj.search([('formula_id', '=', self.id)])
			if record_ids:
				for record in record_ids:
					record.unlink()
			record_ids = period_obj.search([('formula_id', '=', False)])
			if record_ids:
				for record in record_ids:
					record.unlink()
			while index <= len(result):
				param = result['param' + str(index)]
				val = {
					'formula_id': self.id,
					'sequence': index,
					# 'param_id': "{:0>4d}".format(index),
					'name': param,
					'param_description': "parameter " + str(index),
					'param_category': '0',
					'param_type': 'C',
				}
				period_obj.create(val)
				params.append(val)
				index = index + 1
		return params

	@api.model
	def get_value_by_async(self, args, context):
		"""
		Perform the front-end formula return SQLThe execution result
		:param args: The front-end transfer formula content 
		:param context: The front-end cell information 
		:return:
		"""
		if not args:
			return 'Formula of error '

		# Break up the composite parameters  With a single parameter using recursive method is called reuse
		if "FH" in args:
			try:
				parm_lst = literal_eval(args[-1])
				parm_total = list()
				for index, parm in enumerate(parm_lst):
					if isinstance(parm, tuple):
						r_val = self.get_value_by_async(list(parm), context)
						parm_total.append(r_val)
					else:
						parm_total.append(parm)
				rst = eval(''.join(parm_total))
				return rst or 0
			except Exception as e: # Jax
				_logger.warn("Formula of error ", exc_info=True)
				return e

		# Analytical parameters 
		sql_parameter = args[-1].split(',')
		domain = [('name', '=', args[0])]

		# Determine whether there is  Access the object 
		if len(args) > 2:
			domain.append(('formula_object', '=', args[1]))

		formulas = self.search(domain, limit=1)

		if not formulas:
			return 'Not Found'

		# Deal with the default parameters 
		try:
			ctx = self.env.context
			for i, parm in enumerate(sql_parameter):
				if parm == 'PERIOD':
					sql_parameter[i] = "{}".format(ctx.get('period'))
				elif parm == 'ORG':
					sql_parameter[i] = "{}".format(ctx.get('org_code'))
				elif parm == 'BOTY':
					sql_parameter[i] = "{}{}".format(ctx.get('period')[:4], "01")
				elif parm == 'YTD':
					current_year = int(ctx.get('period')[:4])
					current_month = int(ctx.get('period')[4:6])
					sql_parameter[i] = tuple([date(year=current_year, month=num + 1, day=1).strftime('%Y%m') for num in range(0, current_month)])
		except Exception as e: # Jax
			_logger.warn("You have passed the default value of error ", exc_info=True)
			return e

		# SQLpretreatment 
		sql = formulas.formula_design
		pattern = re.compile(r'#[A-Za-z_\d]+#')
		execute_sql = re.sub(pattern, '%s', sql)

		if len(formulas.formula_params_ids) != len(sql_parameter):
			return 'Parameter error '

		_logger.info("SQL ==> [%s] Parameter ==> [%s]" % (execute_sql, sql_parameter))
		self.env.cr.execute(execute_sql, tuple(sql_parameter))
		result = self._cr.fetchone()

		return str(result[0]) if isinstance(result, tuple) and result[0] else '0'

	@api.model
	def get_combined_statements_formulas_data(self):
		"""
		Earlier access to all the definition formula 
		:return:
		"""
		result = self.search_read([], ['name', 'formula_params_ids'])
		for x in result:
			x['formula_params_ids'] = self.env['ps.combined.statements.formulas'].browse(x['id']).formula_params_ids.read(['name'])
		return result


class CombinedStatementsFormulasParams(models.Model):
	_name = "ps.combined.statements.formulas.params"
	_description = u"The report formula parameters "

	sequence = fields.Integer(string='Sequence', default=10)
	formula_id = fields.Many2one('ps.combined.statements.formulas', ondelete='cascade', String="Formula number ")
	# param_id = fields.Char(String="Parameters of the serial number ", Requird=True)
	name = fields.Char(String="The parameter name ", Requird=False)
	param_description = fields.Char(String="Parameters to describe ", Requird=False)
	param_value = fields.Char(String="The parameter value ", Requird=False)
	param_sysvar = fields.Selection(selection='_list_system_variables', String="System variables ")
	param_category = fields.Selection([
		('0', 'Manual entry '),
		('1', 'Table access '),
		('2', 'System parameters '),
	], String="Source way ", Requird=True, default='0')
	param_type = fields.Selection([
		('C', 'character '),
		('N', 'numeric '),
		('B', 'The Boolean '),
	], String="The parameter types ", Requird=True, default='C')
	param_note = fields.Char(String="note ", Requird=False)

	@api.model
	def _list_system_variables(self):
		self._cr.execute("SELECT name, description FROM ps_combined_statements_system_variables ORDER BY name")
		return self._cr.fetchall()


class CombinedStatementsSystemVariables(models.Model):
	_name = "ps.combined.statements.system.variables"
	_description = u"Reporting system variable dictionary "

	name = fields.Char(string="The name of the ", Requird=True)
	description = fields.Char(string="describe ", Requird=True)
	note = fields.Char(String="note ", Requird=True)
