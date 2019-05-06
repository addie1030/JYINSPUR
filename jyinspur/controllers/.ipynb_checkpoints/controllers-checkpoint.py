# -*- coding: utf-8 -*-
from odoo import http

class Jyinspur(http.Controller):
    @http.route('/jyinspur/jyinspur/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/jyinspur/jyinspur/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('jyinspur.listing', {
            'root': '/jyinspur/jyinspur',
            'objects': http.request.env['jyinspur.jyinspur'].search([]),
        })

    @http.route('/jyinspur/jyinspur/objects/<model("jyinspur.jyinspur"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('jyinspur.object', {
            'object': obj
        })