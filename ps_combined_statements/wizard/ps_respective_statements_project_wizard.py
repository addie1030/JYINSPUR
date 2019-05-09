# -*- coding: utf-8 -*-
# Created by martin at 2018/11/28
import logging

from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CombinedStatementRespectiveStatementsProjectWizard(models.TransientModel):
	_name = "ps.respective.statements.project.wizard"

	project_id = fields.Many2one(comodel_name='ps.combined.statements.project', string='Set the table ')
	period = fields.Date(string="During the period of ")
	app_company = fields.Many2one(comodel_name='ps.combined.statements.organization', string='Report to the company ', domain=[('is_entity_company', '=', True)])
	# company_id = fields.Many2one(comodel_name='res.company', string='The company ', index=True, default=lambda self: self.env.user.company_id)
	state = fields.Selection(string='If there is a report ', selection=[('yes', 'is '), ('no', 'no '), ], default='no')
	respective_project = fields.Many2one(comodel_name='ps.respective.statements.project', string='Individual statements ')

	@api.multi
	def design_journaling(self):
		domain = []
		self.ensure_one()
		context = dict()
		period = fields.Date.from_string(self.period).strftime('%Y%m') if self.period else None
		if self.state == 'no':
			if self.app_company:
				domain.append(('app_company', '=', self.app_company.id))
			if self.period:
				domain.append(('period', '=', period))
			if self.project_id:
				domain.append(('project_id', '=', self.project_id.id))
			if self.env['ps.respective.statements.project'].search(domain):
				raise UserError(_("During the period of existing reporting data Can't repeat report Please check in the individual reports submitted to query "))

			context.update({
				'period': period,
				'org_name': self.app_company.name,
				'org_code': self.app_company.code,
				'unit': self.project_id.currency_id.name,
				'app_company': self.app_company.id,
				'project_id': self.project_id.id,
				'state': self.state,
				'app_user': self.env.user.name,
				'respective_project': self.respective_project.id
			})

		if self.state == 'yes':
			context.update({
				'period': self.respective_project.period,
				'org_name': self.respective_project.app_company.name,
				'org_code': self.respective_project.app_company.code,
				'unit': self.respective_project.currency_id.name,
				'app_company': self.respective_project.app_company.id,
				'project_id': self.respective_project.project_id.id,
				'app_user': self.sudo().respective_project.app_user.name,
				'respective_project': self.respective_project.id
			})
		return {
			'type': 'ir.actions.client',
			'tag': 'respective.statements',
			'target': 'current',
			'params': {
				'period': self.respective_project.period if self.state == 'yes' else self.period,
				'app_company': self.respective_project.app_company.id if self.state == 'yes' else self.app_company.id,
				'project_id': self.respective_project.project_id.id if self.state == 'yes' else self.project_id.id,
				'state': self.state,
				'respective_project': self.respective_project.id
			},
			'context': context
		}
