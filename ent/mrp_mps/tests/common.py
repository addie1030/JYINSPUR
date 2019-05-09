# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil.relativedelta import relativedelta

from odoo.tests import common


class TestMpsCommon(common.TransactionCase):

    def setUp(self):
        super(TestMpsCommon, self).setUp()

        category_id = self.ref('product.product_category_5')
        uom_id = self.ref('uom.product_uom_unit')
        # Create product computer desk and computer desk head.
        # ----------------------------------------------------
        self.computerdesk = self.env['product.product'].create({
            'name': 'Computer Desk',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
            })
        self.deskhead = self.env['product.product'].create({
            'name': 'Computer Desk Head',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
            })

        # Create bom for computer desk with computer desk head raw material.
        # ------------------------------------------------------------------
        computer_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.computerdesk.product_tmpl_id.id,
            'product_id': self.computerdesk.id,
        })
        self.env['mrp.bom.line'].create({
            'product_id': self.deskhead.id,
            'product_qty': 1,
            'product_uom_id': uom_id,
            'bom_id': computer_bom.id,
        })
        self.SaleForecast = self.env['sale.forecast']

        # Create Mps report data.
        # -----------------------
        self.Mps = self.env['mrp.mps.report'].create({
            'company_id': self.env.user.company_id.id,
            'product_id': self.computerdesk.id,
            'period': 'month'
        })

        current_date = datetime.datetime.now()
        def create_forecast(month, product_id, forecast_qty=0, to_supply=0, mode='auto'):
            self.SaleForecast.create({
                'date': (current_date + relativedelta(months=month)).strftime('%Y-%m-%d'),
                'product_id': product_id,
                'forecast_qty': forecast_qty,
                'to_supply': to_supply,
                'mode': mode
            })

        # Create sale forecast for computer desk.
        # ---------------------------------------
        create_forecast(0, product_id=self.computerdesk.id, forecast_qty=25)
        create_forecast(1, product_id=self.computerdesk.id, forecast_qty=20)
        create_forecast(2, product_id=self.computerdesk.id, forecast_qty=30)
        create_forecast(3, product_id=self.computerdesk.id, forecast_qty=25, to_supply=15)
        create_forecast(4, product_id=self.computerdesk.id, forecast_qty=10)

        # Create sale forecast for computer desk head.
        # --------------------------------------------
        create_forecast(0, product_id=self.deskhead.id, forecast_qty=40, to_supply=20)
        create_forecast(1, product_id=self.deskhead.id, forecast_qty=20)
        create_forecast(2, product_id=self.deskhead.id, forecast_qty=40)
        create_forecast(3, product_id=self.deskhead.id, forecast_qty=30, to_supply=10, mode='manual')
        create_forecast(4, product_id=self.deskhead.id, forecast_qty=70, to_supply=20, mode='manual')

        #TODO FIXME QDP: no assert ???
