# -*- coding: utf-8 -*-
from odoo import fields
from odoo import models


class Partner(models.Model):
	_inherit = 'res.partner'

	is_client = fields.Boolean(string='In the group ')
