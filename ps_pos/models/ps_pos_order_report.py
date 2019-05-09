# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    ps_member_category_id = fields.Many2one('ps.member.category', string='Member Category', readonly=True)
    ps_member_no = fields.Char(string='Member No.', readonly=True)
    ps_list_price = fields.Float(string='Ordinary Price', readonly=True, group_operator="avg")#普通价格(取产品价格)
    ps_total_discount = fields.Float(string='Discount Amount', readonly=True) #优惠金额
    ps_price_unit = fields.Float(string='Order Price', readonly=True, group_operator="avg")#订单价格(取订单价格)

    def _select(self):
        return """
            SELECT
                MIN(l.id) AS id,
                COUNT(*) AS nbr_lines,
                s.date_order AS date,
                SUM(l.qty) AS product_qty,
                SUM(l.qty * l.price_unit) AS price_sub_total,
                SUM((l.qty * l.price_unit) * (100 - l.discount) / 100) AS price_total,
                SUM((l.qty * l.price_unit) * (l.discount / 100)) AS total_discount,
                (SUM(l.qty*l.price_unit)/SUM(l.qty * u.factor))::decimal AS average_price,
                SUM(cast(to_char(date_trunc('day',s.date_order) - date_trunc('day',s.create_date),'DD') AS INT)) AS delay_validation,
                s.id as order_id,
                s.partner_id AS partner_id,
                s.state AS state,
                s.user_id AS user_id,
                s.location_id AS location_id,
                s.company_id AS company_id,
                s.sale_journal AS journal_id,
                l.product_id AS product_id,
                pt.categ_id AS product_categ_id,
                (SUM(l.qty*pt.list_price)/SUM(l.qty*u.factor))::decimal AS ps_list_price,
                rp.ps_member_category_id AS ps_member_category_id,
                SUM(l.qty*pt.list_price-l.qty*l.price_unit) AS ps_total_discount,
                rp.ps_member_no AS ps_member_no,
                (SUM(l.qty*l.price_unit)/SUM(l.qty * u.factor))::decimal AS ps_price_unit,
                p.product_tmpl_id,
                ps.config_id,
                pt.pos_categ_id,
                pc.stock_location_id,
                s.pricelist_id,
                s.session_id,
                s.invoice_id IS NOT NULL AS invoiced
        """

    def _from(self):
        return """
            FROM pos_order_line AS l
                LEFT JOIN pos_order s ON (s.id=l.order_id)
                LEFT JOIN product_product p ON (l.product_id=p.id)
                LEFT JOIN product_template pt ON (p.product_tmpl_id=pt.id)
                LEFT JOIN uom_uom u ON (u.id=pt.uom_id)
                LEFT JOIN pos_session ps ON (s.session_id=ps.id)
                LEFT JOIN pos_config pc ON (ps.config_id=pc.id)
                LEFT JOIN res_partner rp ON (s.partner_id=rp.id)
                LEFT JOIN ps_member_category pmc ON (rp.ps_member_category_id=pmc.id)
        """

    def _group_by(self):
        return """
            GROUP BY
                s.id, s.date_order, s.partner_id,s.state, pt.categ_id,
                s.user_id, s.location_id, s.company_id, s.sale_journal,
                s.pricelist_id, s.invoice_id, s.create_date, s.session_id,
                l.product_id,
                pt.categ_id, pt.pos_categ_id,
                p.product_tmpl_id,
                ps.config_id,
                pc.stock_location_id,
                rp.ps_member_category_id,
                rp.ps_member_no
        """

    def _having(self):
        return """
            HAVING
                SUM(l.qty * u.factor) != 0
        """

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._group_by(),self._having())
        )