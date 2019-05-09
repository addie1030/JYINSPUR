# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models
from odoo.exceptions import UserError


class AdjustStatementsGenerate(models.TransientModel):
	"""Adjustment to generate """
	_name = "ps.adjust.statements.generate.wizard"

	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='cascade', string='Organization name ', required=True, domain=[('is_entity_company', '=', True)])
	account_period = fields.Date(string="Accounting period ", required=True)
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ', required=True)

	def generate_adjust_statements_papers(self):
		"""Generate the adjustment form """
		period = fields.Date.from_string(self.account_period).strftime('%Y%m')
		project = self.env['ps.respective.statements.project'].search(
			[('period', '=', period),
			('app_company', '=', self.organization_id.id),
			('project_id', '=', self.project_id.id),
			('statements_type', '=', 'adjust')])
		if project:
			raise UserError(u"Has been in existence during the adjustment Can't repeat generated Please check in the individual reports submitted to query ")
		else:
			self.env['ps.respective.statements.project'].save_respective_adj_statements(self.organization_id, period, self.project_id)
