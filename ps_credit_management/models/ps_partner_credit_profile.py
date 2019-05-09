# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PartnerCreditProfile(models.Model):
    _inherit = 'res.partner'

    credit_profile_ids = fields.One2many('ps.credit.profile', 'partner_id')
