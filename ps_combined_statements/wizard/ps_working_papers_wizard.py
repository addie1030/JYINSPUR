# -*- coding: utf-8 -*-
from odoo import api
from odoo import fields
from odoo import models


class WorkingPapersGenerate(models.TransientModel):
	"""Working papers generated """
	_name = "ps.working.papers.generate.wizard"

	merger_organization = fields.Many2one(comodel_name='ps.combined.statements.organization', string='Merging organizations ', required=True, domain=[('is_entity_company', '=', False)])
	account_period = fields.Date(string="Accounting period ", required=True)
	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ', required=True)

	def generate_working_papers(self):
		"""Generate papers """
		period = fields.Date.from_string(self.account_period).strftime('%Y%m')
		self.env['ps.combined.statements.working.paper.project'].save_working_papers(self.merger_organization, period, self.project_id)
