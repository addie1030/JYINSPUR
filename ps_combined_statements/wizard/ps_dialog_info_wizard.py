# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models
from odoo import api


class DialogInfo(models.TransientModel):
	"""Merge report generation """
	_name = "ps.dialog.info.wizard"

	info = fields.Char(readonly=True)

	@api.multi
	def check_models(self):
		if self._context.get('model') == 'ps.combined.statements.elimination.entry':
			[action] = self.env.ref('combined_statements.combined_statements_elimination_entry_act_window').read()
			return action


