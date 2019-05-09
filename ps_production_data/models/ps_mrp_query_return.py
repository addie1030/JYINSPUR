# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models


class PsMrpQueryReturn(models.Model):
    _name = "ps.mrp.query.return"
    _description = 'Return of MRP Routing Query'
    _auto = False

    product_tmpl_id = fields.Many2one(
        'product.template', string='Product')  # 产品模版
    code = fields.Char('Reference')  # 参考
    version = fields.Integer(string='Version')  # BOM版本
    product_qty = fields.Float(strng='Quantity')  # 数量
    product_uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
        help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control")  # 计量单位
    company_id = fields.Many2one('res.company', string='Company')  # 公司
    routing_id = fields.Many2one('mrp.routing', 'Routing')  # 工艺


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        is_mrp_plm_installed = self.env['ir.module.module'].search(
            [('name', '=', 'mrp_plm'), ('state', '=', 'installed')])
        if is_mrp_plm_installed:
            query = """
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        MB.product_tmpl_id AS product_tmpl_id,
                        MB.code AS code,
                        MB.version AS version,
                        MB.product_qty AS product_qty, 
                        MB.product_uom_id AS product_uom_id,
                        MB.company_id AS company_id,
                        MB.routing_id AS routing_id
                    FROM mrp_bom MB 
                    ORDER BY id
            )"""% self._table
            self.env.cr.execute(query)
        else:
            query = """
                CREATE or REPLACE VIEW %s as (
                    SELECT
                        CAST(row_number() OVER () AS int) AS id,
                        MB.product_tmpl_id AS product_tmpl_id,
                        MB.code AS code,
                        CAST(null AS int) AS version,
                        MB.product_qty AS product_qty, 
                        MB.product_uom_id AS product_uom_id,
                        MB.company_id AS company_id,
                        MB.routing_id AS routing_id
                    FROM mrp_bom MB 
                    ORDER BY id
            )"""% self._table
            self.env.cr.execute(query)


