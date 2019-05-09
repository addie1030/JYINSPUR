# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models


class MergeStatementsGenerate(models.TransientModel):
	"""Merge report generation """
	_name = "ps.merge.statements.generate.wizard"

	merge_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', string='Merging organizations ', domain=[('is_entity_company', '=', False)])
	account_period = fields.Date(string="Accounting period ", required=True)
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ')

	def generate_merge_statements_papers(self):
		"""Generate consolidated """
		period = fields.Date.from_string(self.account_period).strftime('%Y%m')
		self.env['ps.combined.statements.merge.project'].save_merge_statements(self.merge_organization, period, self.project_id)
