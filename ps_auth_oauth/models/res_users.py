# -*- coding: utf-8 -*-
import requests
import base64
import json
import urllib
from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_redirect_uri(self):
        # 回调地址：auth_oauth/signin,auth_oauth/signin
        return "%s/auth_oauth/signin" % (self.env['ir.config_parameter'].get_param('web.base.url'))

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        if validation.get('mail', None):
            validation['email'] = validation['mail']
        return super(ResUsers, self)._generate_signup_values(provider, validation, params)

    @api.model
    def _auth_oauth_token(self, endpoint, code, client_id, client_secret):
        params = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': self.get_redirect_uri()}
        client_id_secret = client_id + ":" + client_secret
        auth = base64.b64encode(client_id_secret.encode('utf-8'))
        Authorization = "Basic".encode('utf-8') + " ".encode('utf-8') + auth
        headers = {'Authorization': Authorization}
        request = urllib.request.Request(endpoint, headers=headers, data=urllib.parse.urlencode(params).encode(encoding='UTF8'))
        response = urllib.request.urlopen(request).read()
        result = urllib.parse.parse_qs(response, True)
        return eval(str(response, encoding="utf-8"))

    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token, token_type=None, client_id=None, client_secret=None):
        if client_id and client_secret:
            return self._auth_oauth_token(endpoint, access_token, client_id, client_secret)
        if token_type == 'bearer':
            return requests.get(endpoint, headers={'Authorization': "Bearer %s" % access_token}).json()
        return requests.get(endpoint, params={'access_token': access_token}).json()

    @api.model
    def _auth_oauth_validate_token(self, provider, code):
        """ return the validation data corresponding to the access token """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        validation = self._auth_oauth_rpc(oauth_provider.validation_endpoint, code, client_id=oauth_provider.client_id, client_secret=oauth_provider.client_secret)
        access_token = validation.get('access_token')
        if validation.get("error"):
            raise Exception(validation['error'])
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_rpc(oauth_provider.data_endpoint, access_token, token_type='bearer')
            validation.update(data)
        return validation

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if oauth_provider.response_type == 'token':
            return super(ResUsers, self).auth_oauth(provider, params)

        code = params.get('code')
        validation = self._auth_oauth_validate_token(provider, code)
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            else:
                raise AccessDenied()

        access_token = validation.get('access_token')
        params.update(validation)

        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, login, access_token)

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        oauth_mail = validation['mail']
        oauth_uid = validation['user_id']

        # 用户的绑定及新增

        oauth_user = self.search([("login", "=", oauth_mail)])
        oauth_user_uid = self.search([("login", "=", oauth_mail), ("oauth_uid", "=", oauth_uid)])
        # 第一次登陆：绑定
        if oauth_user and not oauth_user_uid:
            assert len(oauth_user) == 1
            oauth_user.write({'oauth_access_token': params['access_token']})
            oauth_user.write({'oauth_uid': oauth_uid})
            oauth_user.write({'oauth_provider_id': provider})
            return oauth_user.login
        # 非第一次登陆：直接登陆
        elif oauth_user:
            assert len(oauth_user) == 1
            oauth_user.write({'oauth_access_token': params['access_token']})
            # self.env['res.users']._compute_session_token.clear_cache(self.env['res.users'])
            return oauth_user.login
        # 从未登陆过
        else:
            oauth_uid = validation['user_id']
            try:
                oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
                if not oauth_user:
                    raise AccessDenied()
                assert len(oauth_user) == 1
                oauth_user.write({'oauth_access_token': params['access_token']})
                return oauth_user.login
            except AccessDenied as access_denied_exception:
                if self.env.context.get('no_user_creation'):
                    return None
                state = json.loads(params['state'])
                token = state.get('t')
                values = self._generate_signup_values(provider, validation, params)
                try:
                    _, login, _ = self.signup(values, token)
                    return login
                except (SignupError, UserError):
                    raise access_denied_exception


#  vim:et:si:sta:ts=4:sts=4:sw=4:tw=79:
