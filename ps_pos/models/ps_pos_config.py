# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _

class InheritPosConfig(models.Model):

    _inherit = 'pos.config'

    require_set_customer = fields.Boolean(string='Require Set Customer', default=False)
