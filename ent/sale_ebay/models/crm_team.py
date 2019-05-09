# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    team_type = fields.Selection(selection_add=[('ebay', 'eBay')])
