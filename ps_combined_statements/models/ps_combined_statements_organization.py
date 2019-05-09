# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CombinedStatementsOrganizationTree(models.Model):
	"""The group tree """
	_name = 'ps.combined.statements.organization.tree'

	active = fields.Boolean(string='Active', default=True)
	name = fields.Char(string="Group name of the tree ")
	code = fields.Char(string='coding ')
	state = fields.Selection(string="state ", selection=[('lock', 'Lock'), ('unlock', 'Unlock'), ], default='unlock')
	organization_ids = fields.One2many(comodel_name='ps.combined.statements.organization', inverse_name='tree_id')


class CombinedStatementsOrganization(models.Model):
	_name = 'ps.combined.statements.organization'
	_inherit = ['mail.thread']
	_parent_store = True
	_parent_order = 'code'
	_order = 'code'
	_description = 'mergers '

	active = fields.Boolean(string='Active', default=True)
	tree_id = fields.Many2one(comodel_name='ps.combined.statements.organization.tree', string='The group tree ', ondelete='cascade', required=True)
	ref_company_id = fields.Many2one(comodel_name='res.company', string='Business company ', ondelete='cascade', track_visibility='onchange')
	code = fields.Char(string='The company code ', track_visibility='onchange', required=True)
	name = fields.Char(string='The name of the company ', track_visibility='onchange', required=True)
	parent_id = fields.Many2one(comodel_name='ps.combined.statements.organization', ondelete='cascade', string='Immediate superior company ', track_visibility='onchange')
	child_ids = fields.One2many(comodel_name='ps.combined.statements.organization', inverse_name='parent_id', string='The company at a lower level ')
	is_entity_company = fields.Boolean(string='entity ', default=False)
	is_parent_company = fields.Boolean(string='The parent company ', default=False)
	is_descendant_company = fields.Boolean('Children company ', default=False)
	is_branch_office = fields.Boolean(string='branch ', default=False)
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)
	parent_left = fields.Integer('Left Parent', index=True)
	parent_right = fields.Integer('Right Parent', index=True)

	@api.onchange('ref_company_id')
	def _onchange_ref_company_id(self):
		self.name = self.ref_company_id.name or False

	@api.constrains('parent_id')
	def _constrains_parent_id(self):
		# Jax
		for record in self:
			if record.parent_id.id == record.id:
				raise ValidationError('Dont choose the current data ')

	@api.multi
	def toggle_active(self):
		for record in self:
			record.active = not record.active

	@api.model
	def get_data_organization(self):
		"""Organize information """
		return self.search_read([], ['name', 'code'])

