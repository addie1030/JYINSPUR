# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.tools import ormcache

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_ps_account_taxbill_wanhong = fields.Boolean(string="Tax bill wanhong") #万鸿税票接口