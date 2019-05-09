# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models


class IntrastatReport(models.AbstractModel):
    _inherit = 'account.intrastat.report'

    @api.model
    def _fill_missing_values(self, vals, cache=None):
        vals = super(IntrastatReport, self)._fill_missing_values(vals, cache)

        # Erase the company region code by the warehouse region code, if any
        invoice_ids = [row['invoice_id'] for row in vals]
        if cache is None:
            cache = {}
        for index, invoice in enumerate(self.env['account.invoice'].browse(invoice_ids)):
            stock_moves = invoice._get_last_step_stock_moves()
            if stock_moves:
                warehouse = stock_moves[0].warehouse_id or stock_moves[0].picking_id.picking_type_id.warehouse_id
                cache_key = 'warehouse_region_%d' % warehouse.id
                if not cache.get(cache_key) and warehouse.intrastat_region_id.code:
                    # Cache the computed value to avoid performance loss.
                    cache[cache_key] = warehouse.intrastat_region_id.code
                if cache.get(cache_key):
                    vals[index]['region_code'] = cache[cache_key]
        return vals
