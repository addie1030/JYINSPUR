# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)

class SaleReport(models.Model):
    _inherit = 'sale.report'

    days_to_confirm = fields.Float('Days To Confirm', readonly=True)
    invoice_status = fields.Char('Invoice Status', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['days_to_confirm'] = ", DATE_PART('day', s.confirmation_date::timestamp - s.create_date::timestamp) as days_to_confirm"
        fields['invoice_status'] = ', s.invoice_status as invoice_status'

        groupby += ', s.invoice_status'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
