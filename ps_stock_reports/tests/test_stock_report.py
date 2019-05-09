# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo import fields
import datetime
import logging
from dateutil.tz import gettz
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestStockReport(TransactionCase):
    def setUp(self):
        super(TestStockReport, self).setUp()
        self.warehouse_id = self.env.ref('stock.warehouse0').id
        self.location_id = self.env.ref('stock.stock_location_stock').id
        start_date = fields.datetime.now() + datetime.timedelta(days=-3)
        end_date = fields.datetime.now()
        self.start_date, self.end_date = self.datetime_change(start_date, end_date)

        self.incoming_id = self.env.ref('stock.picking_type_in').id
        self.outgoing_id = self.env.ref('stock.picking_type_out').id
        self.product_id = self.env.ref('ps_stock_reports.product_product_sugar').id

    def datetime_change(self, start_date, end_date):
        tz = self.env.context.get('tz')
        end_date = datetime.datetime.strptime(end_date.strftime("%Y-%m-%d 23:59:59")
                                              , "%Y-%m-%d %H:%M:%S")
        utc_start_date = self.local2utc(start_date.replace(tzinfo=gettz(tz))).strftime("%Y-%m-%d %H:%M:%S")
        utc_end_date = self.local2utc(end_date.replace(tzinfo=gettz(tz))).strftime("%Y-%m-%d %H:%M:%S")

        return utc_start_date, utc_end_date

    def local2utc(self, local_st):
        """本地时间转UTC时间（-8:00）"""
        utc_st = datetime.datetime.utcfromtimestamp(local_st.timestamp())
        return utc_st

    def create_wizard(self, start_date, end_date):
        return self.env['ps.wizard.stock.price.dispatch'].create({
            'warehouse_id': self.warehouse_id,
            'location_id': self.location_id,
            'start_date': start_date,
            'end_date': end_date,
        })

    def test_date_onchange_except(self):
        """
        Start Date > End date
        End Date > Now Date
        :return:
        """

        start_date = fields.datetime.now() + datetime.timedelta(days=-3)
        start_date_except = fields.datetime.now() + datetime.timedelta(days=3)
        end_date = fields.datetime.now()
        end_date_except = fields.datetime.now() + datetime.timedelta(days=3)
        self.start_date_except, self.end_date = self.datetime_change(start_date_except, end_date)
        self.create_wizard = self.create_wizard(self.start_date_except, self.end_date)
        with self.assertRaises(UserError):
            self.create_wizard.onchange_date()
        self.start_date, self.end_date_except = self.datetime_change(start_date, end_date_except)
        with self.assertRaises(UserError):
            self.create_wizard.onchange_date()

    def test_check_report(self):
        """
        check values  of  stock report
        the demo data at demo files
        """

        self.warehouse_id = self.env.ref('stock.warehouse0').id
        self.location_id = self.env.ref('stock.stock_location_stock').id
        start_date = fields.datetime.now() + datetime.timedelta(days=-3)
        end_date = fields.datetime.now()
        self.start_date, self.end_date = self.datetime_change(start_date, end_date)

        self.incoming_id = self.env.ref('stock.picking_type_in').id
        self.outgoing_id = self.env.ref('stock.picking_type_out').id
        self.product_id = self.env.ref('ps_stock_reports.product_product_sugar').id

        self.report_wizard = self.create_wizard(start_date, end_date)
        # self.report_wizard.onchange_location_id()
        self.report_wizard.do_inventory_dispatch()
        domain = [
            ('warehouse_id', '=', self.warehouse_id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('state', '=', 'done'),
            ('product_id', '=', self.product_id),
        ]

        incoming_domain = domain + [('location_dest_id', '=', self.location_id),
                                    ('picking_type_id', '=', self.incoming_id)]
        outgoing_domain = domain + [('location_id', '=', self.location_id),
                                    ('picking_type_id', '=', self.outgoing_id)]

        self.stock_in_qty = sum([
            qty.product_uom_qty for qty in self.env['stock.move'].search(incoming_domain)])

        self.stock_out_qty = sum([
            qty.product_uom_qty for qty in self.env['stock.move'].search(outgoing_domain)])

        res_report = self.env['ps.stock.price.dispatch'].search(
            [('product_id', '=', self.product_id)])
        self.in_qty = res_report.qty_in
        self.out_qty = res_report.qty_out
        self.assertEqual(self.stock_in_qty, self.in_qty, "values of incoming qty was difference ")
        self.assertEqual(self.stock_out_qty, self.out_qty, "values of outgoing qty was difference ")
