# -*- coding: utf-8 -*-
from odoo import tools
from dateutil.tz import gettz
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning


class PsStockMoveReport(models.TransientModel):
    _name = 'ps.wizard.stock.price.dispatch'
    _description = 'Stock Price Dispatch Wizard'  # 库存价格分析向导

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=1)  # 仓库
    lot_stock_id = fields.Many2one('stock.location', string='Location',
                                   related='warehouse_id.lot_stock_id')  # 库位
    location_id = fields.Many2one('stock.location', string='Location', required=1)  # 库位

    start_date = fields.Datetime(string='Start  Date', required=1)  # 起始日期
    end_date = fields.Datetime(string='end  Date', default=fields.Datetime.now())  # 截止日期

    @api.onchange('warehouse_id', 'lot_stock_id')
    def onchange_location_id(self):
        if self.location_id:
            self.location_id = False

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            self.check_date(self.start_date, self.end_date)

    def check_date(self, start_date, end_date):
        now_date = datetime.datetime.now()
        if (start_date - end_date).days > 0:
            raise Warning(
                _("Please note：that the starting and ending dates should not be greater than the deadline!")
            )

        if (end_date - now_date).days > 0:
            raise Warning(
                _("Please note: that and ending date should not be greater than the current date! "))

    def query_sql(self, start_date, end_date, warehouse, location):
        """
        查询库存SQl:
            期初 ：所选日期期间发生记录时之前的库存
            入库： 所选日期期间的入库记录
            出库: 所选日期期间的出库记录
            结存：所选日期期间的入库-出库记录

        :param start_date: 开始日期
        :param end_date: 截止日期
        :param location: 库位
        :return:
        """

        return """
                select row_number() OVER () as id,
                product_id,location_id,product_uom,
                sum(qty_start) qty_start,sum(qty_in) qty_in,sum(qty_out) qty_out,
                sum(qty_balance)+sum(qty_start) qty_balance from (
                ---inventory incoming outgoing and balance start
                SELECT product_id,warehouse_id,location_id,product_uom,0 price_start,
                sum(qty_start) qty_start,sum(qty_in) qty_in,sum(qty_out) qty_out,
                qty_in-qty_out as qty_balance
                from(
                select * from (
                select product_id,warehouse_id,location_id,product_uom,
                0 as qty_start,qty_in,0 as qty_out,0 as qty_balance,
                ('%s') as start_date,('%s') as end_date
                from (
                select product_id,warehouse_id,location_dest_id as location_id,product_uom, 
                sum(product_uom_qty) qty_in from stock_move 
                where picking_type_id in (select id from stock_picking_type where code = 'incoming') 
                and date <= '%s' and date >= '%s' and warehouse_id = %s and location_dest_id = %s  and state= 'done'
                group by product_id, warehouse_id, location_dest_id, product_uom) as stock_incoming
                union 
                select product_id,warehouse_id,location_id,product_uom,
                0 as qty_start,0 as qty_in,qty_out,0 as qty_balance,
                ('%s') as start_date,('%s') as end_date from(
                select product_id,warehouse_id,location_id,product_uom,
                sum(product_uom_qty) qty_out from stock_move 
                where picking_type_id in (select id from stock_picking_type where code = 'outgoing') 
                and date <= '%s' and date >= '%s' and warehouse_id=%s and location_id = %s and state = 'done'
                group by product_id, warehouse_id, location_id, product_uom) as stock_outgoing
                ) as balance
                --inventory incoming outgoing and balance end
                union
                --beginning inventory start
                select product_id,warehouse_id, location_id,product_uom,
                sum(qty_start) qty_start,0 as qty_in,0 as qty_out,0 as qty_balance, 
                ('%s') as start_date,('%s') as end_date from (
                select product_id,warehouse_id, location_id,product_uom,
                sum(qty_start_in-qty_start_out) as qty_start,
                0 as qty_in,0 as qty_out,0 as qty_balance, 
                ('%s') as start_date,('%s') as end_date from(
                select product_id,warehouse_id,location_id,product_uom,
                sum(qty_start_in) qty_start_in,sum(qty_start_out)  qty_start_out
                 from(
                select * from(
                select product_id,warehouse_id, location_dest_id as location_id,product_uom,
                sum(product_uom_qty) qty_start_in,0 qty_start_out
                 from 
                stock_move 
                where 
                picking_type_id in (select id from stock_picking_type where code = 'incoming') and warehouse_id=%s and location_dest_id=%s and
                date < '%s' and state = 'done'
                group by product_id, warehouse_id, location_dest_id,product_uom
                ) as stock_income
                union
                select product_id, warehouse_id, location_id,product_uom,
                0 qty_start_in,sum(product_uom_qty) qty_start_out from 
                stock_move 
                where 
                picking_type_id in (select id from stock_picking_type where code = 'outgoing') and warehouse_id=%s and location_id =%s and
                date < '%s' and state = 'done'
                group by product_id,warehouse_id, location_id,product_uom
                ) as stock_a 
                group by product_id,warehouse_id, location_id,product_uom
                ) as b group by product_id,warehouse_id, location_id,product_uom,qty_start_in,
                qty_start_out
                ) as stock
                group by product_id,warehouse_id, location_id,product_uom,qty_start
                ) as stock_group group by product_id,warehouse_id, location_id,product_uom,
                qty_start,qty_in,qty_out
                -- beginning inventory end
                ) as stock_start
                group by product_id,warehouse_id,location_id,product_uom
                order by product_id,product_uom
                        """ % (start_date, end_date,
                               end_date, start_date, warehouse, location,
                               start_date, end_date,
                               end_date, start_date, warehouse, location,
                               start_date, end_date,
                               start_date, end_date,
                               warehouse, location, start_date,
                               warehouse, location, start_date
                               )

    def insert_sql(self, sql):
        """
        把库存收发查询结果存入表
        :param sql:
        :return:
        """

        tools.drop_view_if_exists(self._cr, 'ps_stock_price_dispatch')
        sql = """ CREATE OR REPLACE VIEW ps_stock_price_dispatch AS (%s) """ % sql
        self._cr.execute(sql)

    def local2utc(self, local_st):
        """本地时间转UTC时间（-8:00）"""
        utc_st = datetime.datetime.utcfromtimestamp(local_st.timestamp())
        return utc_st

    @api.multi
    def do_inventory_dispatch(self):
        self.check_date(self.start_date, self.end_date)

        location = self.location_id.id
        warehouse = self.warehouse_id.id
        tz = self.env.context.get('tz')
        end_date = datetime.datetime.strptime(self.end_date.strftime("%Y-%m-%d 23:59:59")
                                              , "%Y-%m-%d %H:%M:%S")
        utc_start_date = self.local2utc(self.start_date.replace(tzinfo=gettz(tz)))
        utc_end_date = self.local2utc(end_date.replace(tzinfo=gettz(tz)))

        start_date = utc_start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date = utc_end_date.strftime("%Y-%m-%d %H:%M:%S")
        sql = " %s" % (
            self.query_sql(start_date, end_date, warehouse, location)
        )

        self.insert_sql(sql)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Price Dispatch') + ' : %s : %s  - %s ~ %s' % (
                self.warehouse_id.name, self.location_id.display_name,
                self.start_date.strftime("%Y-%m-%d"),
                self.end_date.strftime("%Y-%m-%d")
            ),  # 库存分析
            'view_mode': 'pivot,tree',
            'res_model': 'ps.stock.price.dispatch',
        }
