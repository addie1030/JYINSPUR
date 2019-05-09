# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.osv.expression import expression


class StockReport(models.Model):
    _inherit = 'stock.report'

    valuation = fields.Float("Valuation of Inventory using a Domain", readonly=True, store=False,
                             help="Note that you can only access this value in the read_group, only the sum operator is supported")
    stock_value = fields.Float("Total Valuation of Inventory", readonly=True, store=False,
                               help="Note that you can only access this value in the read_group, only the sum operator is supported and only date_done is used from the domain")

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            This is a hack made in order to improve performance as adding
            inventory valuation on the report itself would be too costly.

            Basically when asked to return the valuation, it will run a smaller
            SQL query that will calculate the inventory valuation on the given
            domain.

            Only the SUM operator is supported for valuation.

            We can also get the stock_value of the inventory at a specific date
            (default is today).

            The same applies to this stock_value field, it only supports the sum operator
            and does not support the group by.

            NB: This should probably be implemented in a read instead of read_group since
                we don't support grouping

            NB: We might be able to avoid doing this hack by optimizing the query used to
                generate the report (= TODO: see nse)
        """
        stock_value = next((field for field in fields if re.search(r'\bstock_value\b', field)), False)
        valuation = next((field for field in fields if re.search(r'\bvaluation\b', field)), False)

        if stock_value:
            fields.remove(stock_value)

        if valuation:
            fields.remove(valuation)

        if stock_value or valuation:
            if groupby:
                raise UserError("valuation and stock_value don't support grouping")

            if any(field.split(':')[1].split('(')[0] != 'sum' for field in [stock_value, valuation] if field):
                raise UserError("read_group only support operator sum for valuation and stock_value")

        res = []
        if fields:
            res = super(StockReport, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        if not res and (stock_value or valuation):
            res = [{}]

        if stock_value:
            date = Date.to_string(Date.from_string(next((d[2] for d in domain if d[0] == 'date_done'), Date.today())))

            products = self.env['product.product'].with_context(to_date=date).search([('product_tmpl_id.type', '=', 'product')])
            value = sum(product.stock_value for product in products)

            res[0].update({
                '__count': 1,
                stock_value.split(':')[0]: value,
            })

        if valuation:
            query = """
                SELECT
                    SUM(move_valuation.valuation) as valuation
                FROM (
                    SELECT
                        CASE property.value_text -- cost method
                            WHEN 'fifo' THEN move.value
                            WHEN 'average' THEN move.value
                            ELSE move.product_qty * product_property.value_float -- standard price
                        END as valuation
                    FROM
                        stock_move move
                        INNER JOIN product_product product ON move.product_id = product.id
                        INNER JOIN product_template ON product.product_tmpl_id = product_template.id
                        INNER JOIN product_category category ON product_template.categ_id = category.id
                        LEFT JOIN ir_property property ON property.res_id = CONCAT('product.category,', category.id)
                        INNER JOIN ir_property product_property ON product_property.res_id = CONCAT('product.product,', product.id)
                    WHERE
                        move.id IN (
                            SELECT id
                            FROM stock_report
                            WHERE %s )
                        AND (property.company_id is null or property.company_id = move.company_id)
                        AND product_property.company_id = move.company_id
                ) as move_valuation
            """

            where, args = expression(domain + [('company_id', '=', self.env.user.company_id.id)], self).to_sql()
            self.env.cr.execute(query % where, args)
            res[0].update({
                '__count': 1,
                valuation.split(':')[0]: self.env.cr.fetchall()[0][0],
            })

        return res
