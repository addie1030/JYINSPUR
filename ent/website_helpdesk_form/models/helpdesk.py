# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.addons.http_routing.models.ir_http import slug


class HelpdeskTeam(models.Model):
    _inherit = ['helpdesk.team']

    feature_form_url = fields.Char('URL to Submit Issue', readonly=True, compute='_get_form_url')

    def _get_form_url(self):
        for team in self.filtered(lambda team: team.name and team.use_website_helpdesk_form and team.id):
            team.feature_form_url = (team.use_website_helpdesk_form and team.id) and ('/helpdesk/' + slug(team) + '/submit') or False
