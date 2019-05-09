# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AuthOAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'

    response_type = fields.Selection([
        ('token', 'Token'),
        ('code', 'Code'), 
    ], required=True, default='token')
    client_secret = fields.Char(string='Client Secret')  # Our identifier

#  vim:et:si:sta:ts=4:sts=4:sw=4:tw=79:
