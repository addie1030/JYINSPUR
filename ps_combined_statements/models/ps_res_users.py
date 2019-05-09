# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, exceptions, fields, models


class Users(models.Model):
	_inherit = 'res.users'

	organization_ids = fields.Many2many(comodel_name='ps.combined.statements.organization', relation='combined_statements_organization_users_rel',
								column1='user_id', column2='org_id', string='Allowing the merger of the organization ')

	@api.multi
	def write(self, vals):
		"""Clear the cache """
		if 'organization_ids' in vals:
			self.env['ir.model.access'].call_cache_clearing_methods()
			self.env['ir.rule'].clear_caches()
			self.has_group.clear_cache(self)
		return super(Users, self).write(vals)

