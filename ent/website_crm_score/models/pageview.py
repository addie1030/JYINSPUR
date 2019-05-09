# -*- coding: utf-8 -*-
from odoo import fields, models, SUPERUSER_ID, tools, api
from psycopg2 import IntegrityError
from odoo.tools import html_escape


class pageview(models.Model):
    _name = "website.crm.pageview"
    _rec_name = "view_date"
    _description = 'Website CRM Page View'

    view_date = fields.Datetime(string='Viewing Date')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    user_id = fields.Many2one('res.users', string='User', oldname='partner_id')
    url = fields.Char(string='Url')

    @api.model
    def create_pageview(self, vals, test=False):
        # returns True if the operation in the db was successful, False otherwise
        lead_id = vals.get('lead_id', 0)
        user_id = vals.get('user_id')
        url = vals.get('url', '')
        view_date = fields.Datetime.now()

        with self.pool.cursor() as pv_cr:
            if test:
                pv_cr = self._cr
            pv_cr.execute('''
                UPDATE website_crm_pageview SET view_date=%s WHERE lead_id=%s AND url=%s RETURNING id;
                ''', (view_date, lead_id, url))
            fetch = pv_cr.fetchone()
            if fetch:
                return True
            else:
                # update failed
                try:
                    with tools.mute_logger('odoo.sql_db'):
                        pv_cr.execute('''
                            INSERT INTO website_crm_pageview (lead_id, user_id, url, view_date)
                            SELECT %s,%s,%s,%s
                            RETURNING id;
                            ''', (lead_id, user_id, url, view_date))
                    fetch = pv_cr.fetchone()
                    if fetch:
                        # a new pageview has been created, a message is posted
                        url = html_escape(url)
                        body = '<a href="%s" target="_blank"><b>%s</b></a>' % (url, url)
                        ctx = dict(self._context, mail_notify_noemail=True)
                        self.env['crm.lead'].browse(lead_id).sudo().with_context(ctx).message_post(body=body, subject="Page visited")
                        return True
                except IntegrityError:
                    return False
