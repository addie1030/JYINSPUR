# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.http import request
from odoo.osv import osv


class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls):
        delete_cookie = False
        response = super(ir_http, cls)._dispatch()
        if response and getattr(response, 'status_code', 0) == 200 and hasattr(response, 'qcontext'):
            template = response.qcontext.get('response_template')
            if template:
                view = request.env['website'].get_template(template)
                if view and view.track:
                    lead_id = request.env["crm.lead"].decode(request)
                    url = request.httprequest.url
                    vals = {'lead_id': lead_id, 'user_id': request.session.get('uid'), 'url': url}
                    if not lead_id or not request.env['website.crm.pageview'].create_pageview(vals):
                        # create_pageview was fail
                        delete_cookie = True
                        request.session.setdefault('pages_viewed', {})[url] = fields.Datetime.now()
                        request.session.modified = True

        if isinstance(response, Exception):
            return response

        if delete_cookie:
            response.delete_cookie('lead_id')

        return response


class view(osv.osv):
    _inherit = "ir.ui.view"

    track = fields.Boolean(string='Track', default=False, help="Allow to specify for one page of the website to be trackable or not")
