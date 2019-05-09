# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models


class AdjustWorkingPapersGenerate(models.TransientModel):
	"""Adjust the working papers """
	_name = "ps.adjust.working.papers.generate.wizard"

	organization_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='cascade', string='Organization name ', required=True, domain=[('is_entity_company', '=', True)])
	account_period = fields.Date(string="Accounting period ", required=True)
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ', required=True)

	def generate_adjust_working_papers(self):
		"""Adjust the working papers """
		period = fields.Date.from_string(self.account_period).strftime('%Y%m')
		self.env['ps.combined.statements.adjust.working.paper.project'].save_adjust_working_papers(self.organization_id, period, self.project_id)
