# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    elearning_id = fields.Many2one('slide.channel', 'eLearning')
    elearning_url = fields.Char('Presentations URL', readonly=True, related='elearning_id.website_url')

    @api.onchange('use_website_helpdesk_slides')
    def _onchange_use_website_helpdesk_slides(self):
        if self.use_website_helpdesk_slides:
            self.elearning_id = self.env.ref('website_slides.channel_public', raise_if_not_found=False)
        if not self.use_website_helpdesk_slides:
            self.elearning_id = False

    @api.model_cr_context
    def _init_column(self, column_name):
        """ Initialize the value of the given column for existing rows.
            Overridden here because we need the elearning_id to be set during the installationg of this module
            only on records (teams) that have use_website_helpdesk_slides set as True
        """
        if column_name != "elearning_id" or not self.env.ref('website_slides.channel_public', raise_if_not_found=False):
            super(HelpdeskTeam, self)._init_column(column_name)
        else:
            default_value = self.env.ref('website_slides.channel_public').id

            query = 'SELECT id, use_website_helpdesk_slides FROM "%s" WHERE "%s" is NULL' % (
                self._table, column_name)
            self.env.cr.execute(query)
            # query_results = [team_ids, use_website_helpdesk_slides]
            query_results = self.env.cr.fetchall()
            for team in query_results:
                if team[1]:
                    query = 'UPDATE "%s" SET "%s"=%%s WHERE id = %s' % (
                        self._table, column_name, team[0])
                    self.env.cr.execute(query, (default_value,))
