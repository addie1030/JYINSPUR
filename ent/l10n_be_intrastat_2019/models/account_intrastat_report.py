# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api


class IntrastatReport(models.AbstractModel):
    _inherit = 'account.intrastat.report'

    @api.model
    def _build_query(self, date_from, date_to, journal_ids, invoice_types=None):
        query, params = super(IntrastatReport, self)._build_query(date_from, date_to, journal_ids, invoice_types=invoice_types)
        # If you don't know the country of origin of the goods, as an exception you may replace the country code by "QU".
        query['select'] += ', CASE WHEN inv_line.intrastat_product_origin_country_id IS NULL THEN \'QU\' ELSE product_country.code END AS intrastat_product_origin_country'
        query['from'] += ' LEFT JOIN res_country product_country ON product_country.id = inv_line.intrastat_product_origin_country_id'
        # For VAT numbers of companies outside the European Union, for example in the case of triangular trade, you always have to use the code "QV999999999999".
        query['select'] += ', CASE WHEN partner_country.id IS NULL THEN \'QV999999999999\' ELSE partner.vat END AS partner_vat'
        query['from'] += ' LEFT JOIN res_country partner_country ON partner.country_id = partner_country.id AND partner_country.intrastat IS TRUE'
        return query, params

    def _get_expedition_code(self, extended):
        return 'INTRASTAT_X_E' if extended else 'INTRASTAT_X_S'

    def _get_expedition_form(self, extended):
        return 'INTRASTAT_X_EF' if extended else 'INTRASTAT_X_SF'
