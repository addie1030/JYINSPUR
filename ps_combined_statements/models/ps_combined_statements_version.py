# -*- coding: utf-8 -*-

# Created by Jalena at 2018/10/11
from odoo import fields, models, api, _


class CombinedStatementsVersion(models.Model):
	"""The report version """
	_name = 'ps.combined.statements.version'

	active = fields.Boolean(string='Active', default=True)
	name = fields.Char('The name of the version ')
	code = fields.Char('Version number ',	copy=False, default=lambda self: _('New'), readonly=True)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)

	@api.model
	def create(self, vals):
		if 'code' not in vals or vals['code'] == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('statements.version') or _('New')
		return super(CombinedStatementsVersion, self).create(vals)

