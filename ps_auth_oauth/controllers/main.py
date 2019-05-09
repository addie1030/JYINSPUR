# -*- coding: utf-8 -*-

from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.http import request
import werkzeug
import json

def list_providers(self):
    try:
        providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
    except Exception:
        providers = []
    for provider in providers:
        # 回调地址：auth_oauth/signin,oauth/inspur_check
        return_url = request.httprequest.url_root + 'auth_oauth/signin'
        state = self.get_state(provider)
        params = dict(
            response_type=provider['response_type'],
            client_id=provider['client_id'],
            redirect_uri=return_url,
            scope=provider['scope'],
            state=json.dumps(state),
        )
        provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.url_encode(params))
    return providers


OAuthLogin.list_providers = list_providers

#  vim:et:si:sta:ts=4:sts=4:sw=4:tw=79:
