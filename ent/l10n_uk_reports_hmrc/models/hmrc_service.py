# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
import json
import requests
from werkzeug import urls

from odoo import api, models, _
from odoo.http import request
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DEBUG = False
SANDBOX_API_URL = 'https://test-api.service.hmrc.gov.uk'
PRODUCTION_API_URL = 'https://api.service.hmrc.gov.uk'
if DEBUG:
    HMRC_CLIENT_ID = 'dTdANDSeX4fiw63DicmUaAVQDSMa'
    PROXY_SERVER = 'https://www.test.odoo.com'
else:
    HMRC_CLIENT_ID = 'GqJgi8Hal1hsEwbG6rY6i9Ag1qUa'
    PROXY_SERVER = 'https://onlinesync.odoo.com'
TIMEOUT = 10


class HmrcService(models.AbstractModel):
    """
    Service in order to pass through our authentication proxy
    """
    _name = 'hmrc.service'
    _description = 'HMRC service'

    @api.model
    def _login(self):
        """
        Checks if there is a userlogin (proxy) or a refresh of the tokens needed and ask for new ones
        If needed, it returns the url action to log in with HMRC
        Raise when something unexpected happens (enterprise contract not valid e.g.)
        :return: False when no login through hmrc needed by the user, otherwise the url action
        """
        user = self.env.user
        login_needed = False
        if user.l10n_uk_user_token:
            if not user.l10n_uk_hmrc_vat_token or user.l10n_uk_hmrc_vat_token_expiration_time < datetime.now() + timedelta(minutes=1):
                try:
                    url = PROXY_SERVER + '/onlinesync/l10n_uk/get_tokens'
                    dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
                    data = json.dumps({'params': {'user_token': self.env.user.l10n_uk_user_token, 'dbuuid': dbuuid}})
                    resp = requests.request('GET', url, data=data,
                                            headers={'content-type': "application/json"}, timeout=TIMEOUT) #json-rpc
                    resp.raise_for_status()
                    response = resp.json()
                    response = response.get('result', {})
                    self._write_tokens(response)
                except:
                    # If it is a connection error, don't delete credentials and re-raise
                    raise
                else: #In case no error was thrown, but an error is indicated
                    if response.get('error'):
                        self._clean_tokens()
                        self._cr.commit() # Even with the raise, we want to commit the cleaning of the tokens in the db
                        raise UserError(_('There was a problem refreshing the tokens.  Please log in again. ') + response.get('message'))
        else:
            # if no user_token, ask for one
            url = PROXY_SERVER + '/onlinesync/l10n_uk/get_user'
            dbuuid = self.env['ir.config_parameter'].sudo().get_param('database.uuid')
            data = json.dumps({'params': {'dbuuid': dbuuid}})
            resp = requests.request('POST', url, data=data, headers={'content-type': 'application/json', 'Accept': 'text/plain'})
            resp.raise_for_status()
            contents = resp.json()
            contents = contents.get('result')
            if contents.get('error'):
                raise UserError(contents.get('message'))
            user.sudo().write({'l10n_uk_user_token': contents.get('user_token')})
            login_needed = True

        if login_needed:
            url = self.env['hmrc.service']._get_oauth_url(user.l10n_uk_user_token)
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'self',
            }
        return False

    @api.model
    def _write_tokens(self, tokens):
        vals = {}
        vals['l10n_uk_hmrc_vat_token_expiration_time'] = tokens.get('expiration_time')
        vals['l10n_uk_hmrc_vat_token'] = tokens.get('access_token')
        self.env.user.sudo().write(vals)

    @api.model
    def _clean_tokens(self):
        vals = {}
        vals['l10n_uk_user_token'] = ''
        vals['l10n_uk_hmrc_vat_token_expiration_time'] = False
        vals['l10n_uk_hmrc_vat_token'] = ''
        self.env.user.sudo().write(vals)

    def _get_local_hmrc_oauth_url(self):
        """ The user will be redirected to this url after accepting (or not) permission grant.
        """
        return PROXY_SERVER + '/onlinesync/l10n_uk/hmrc'

    @api.model
    def _get_state(self, userlogin):
        report_id = self.env.ref('l10n_uk_reports.financial_report_l10n_uk').id
        action = self.env.ref('l10n_uk_reports.account_financial_html_report_action_' + str(report_id))
        # Search your own host
        url = request.httprequest.scheme + '://' + request.httprequest.host
        return json.dumps({
            'url': url,
            'user': userlogin,
            'action': action.id,
        })

    @api.model
    def _get_oauth_url(self, login):
        """ Generates the url to hmrc oauth endpoint.
        """
        oauth_url = self._get_endpoint_url('/oauth/authorize')
        url_params = {
            'response_type': 'code',
            'client_id': HMRC_CLIENT_ID,
            'scope': 'read:vat write:vat',
            'state': self._get_state(login),
            'redirect_uri': self._get_local_hmrc_oauth_url(),
        }
        return oauth_url + '?' + urls.url_encode(url_params)

    @api.model
    def _get_endpoint_url(self, endpoint):
        base_url = SANDBOX_API_URL if DEBUG else PRODUCTION_API_URL
        return base_url + endpoint