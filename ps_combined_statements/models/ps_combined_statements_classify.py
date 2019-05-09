# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CombinedStatementsClassify(models.Model):
	"""Merge sort """
	_name = 'ps.combined.statements.classify'
	_description = 'Classification of consolidated statements'

	active = fields.Boolean(string='Active', default=True)
	code = fields.Char(string='Serial number ')
	name = fields.Char(string='Classification name', require=True, translate=True)
	organization_ids = fields.Many2many(comodel_name='ps.combined.statements.organization', relation='combined_statements_organization_classify_rel', string='Organization')
	tree_id = fields.Many2one(comodel_name='ps.combined.statements.organization.tree', string='Oraganization Tree')
	company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id)



