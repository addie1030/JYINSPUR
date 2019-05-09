# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil.relativedelta import relativedelta

from .common import TestMpsCommon

class TestMpsReport(TestMpsCommon):

    def test_00_mps_report(self):
        """ Testing master product scheduling """

        # Set value for mps in product computer desk and computer desk head.
        # ------------------------------------------------------------------
        self.computerdesk.write({'mps_active': True, 'mps_min_supply': 0, 'mps_max_supply': 20, 'mps_forecasted': 20})
        self.deskhead.write({'mps_active': True, 'mps_min_supply': 0, 'mps_max_supply': 50, 'mps_forecasted': 70})

        self.Mps.update_indirect(self.deskhead)
        self.Mps.update_indirect(self.computerdesk)

        # Create inventory for computer desk and computer desk head product.
        # ------------------------------------------------------------------
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory For Mps',
            'filter': 'partial',
            'line_ids': [(0, 0, {
                'product_id': self.computerdesk.id,
                'product_uom_id': self.computerdesk.uom_id.id,
                'product_qty': 100,
                'location_id': self.ref('stock.stock_location_14')
            }), (0, 0, {
                'product_id': self.deskhead.id,
                'product_uom_id': self.deskhead.uom_id.id,
                'product_qty': 90,
                'location_id': self.ref('stock.stock_location_14')
            })]
        })
        inventory.action_start()
        inventory.action_validate()


        # ----------------------------------------------------------------------------------------------------
        # Check starting inventory, forecast demand, indirect demand, to supply, and forecast inventory
        # of current month for computer desk head.
        #   Indirect forecast = 40.0
        #   Product forecasted = 55.0
        #   initial Quantity = 90.0
        #   indirect demand = 45.0
        #   To Supply Quantity = 50.0 (product forecasted - initial Quantity + Indirect demand + indirect_total)
        # ------------------------------------------------------------------------------------------------------

        # Testing for all sale forecast product with both mode (auto and manual) ...
        # ------------------------------------------------------------------------
        def mps_calculate_forecast(product):
            now = datetime.datetime.now()
            date = datetime.datetime(now.year, now.month, 1, 23, 59, 59)
            initial = product.with_context(to_date=date).qty_available
            indirect = self.Mps.get_indirect(product)[product.id]
            for data in self.Mps.get_data(product):
                self.assertEqual(data['initial'], initial, 'Wrong calculation of initial demand.')
                forecasts = self.SaleForecast.search([('date', '>=', data['date']),
                    ('date', '<', data['date_to']),
                    ('product_id', '=', product.id)])
                demand = sum(forecasts.filtered(lambda x: x.mode == 'auto').mapped('forecast_qty'))
                indirect_total = 0.0
                for day, qty in indirect.items():
                    if (str(day) >= data['date']) and (str(day) < data['date_to']):
                        indirect_total += qty
                # To supply = product forecasted - initial quantity (available quantity) + forecast demand + indirect quantity.
                to_supply = product.mps_forecasted - initial + demand + indirect_total
                to_supply = max(to_supply, product.mps_min_supply)
                if product.mps_max_supply > 0:
                    to_supply = min(product.mps_max_supply, to_supply)
                if data['mode'] == 'manual':
                    to_supply = sum(forecasts.filtered(lambda x: x.mode == 'manual').mapped('to_supply'))
                # forecasted quantity = to supply quantity - forecast demand + initial quantity - indirect quantity.
                forecasted = to_supply - demand + initial - indirect_total
                self.assertEqual(data['demand'], demand, 'Wrong calculation of demand.')
                self.assertEqual(data['indirect'], indirect_total, 'Wrong calculation of demand.')
                self.assertEqual(data['to_supply'], to_supply, 'Wrong calculation of to supply.')
                self.assertEqual(data['forecasted'], forecasted, 'Wrong calculation of forecast quantity.')
                # assign forecasted quantity for next initial quantity.
                initial = forecasted

        # Check all forecast scheduling for specific products.
        # ----------------------------------------------------
        mps_calculate_forecast(self.deskhead)
        mps_calculate_forecast(self.computerdesk)

        # Change minimum and maximum supply on product.
        # ---------------------------------------------
        self.deskhead.mps_min_supply = 30
        self.deskhead.mps_max_supply = 90
        self.computerdesk.mps_min_supply = 0
        self.computerdesk.mps_max_supply = 200

        # Check forecast scheduling after change minimum and maximun supply.
        # ------------------------------------------------------------------
        mps_calculate_forecast(self.deskhead)
        mps_calculate_forecast(self.computerdesk)

        # Check sale forecast with update forecast quantity , to supply quantity and mode..
        # --------------------------------------------------------------------------------------------------
        current_date = datetime.datetime.now()
        forecasts = self.SaleForecast.search([('product_id', '=', self.computerdesk.id),
                                            ('date', '>=', (current_date + relativedelta(months=0)).strftime('%Y-%m-%d')),
                                            ('date', '<=', (current_date + relativedelta(months=2)).strftime('%Y-%m-%d'))])
        # Update forecast quantity....
        forecasts.write({'forecast_qty': 100})
        # Set indirect quantity for parent bom.
        self.Mps.update_indirect(self.computerdesk.id)
        mps_calculate_forecast(self.computerdesk)
        mps_calculate_forecast(self.deskhead)

        # Test after set forecast target....
        self.computerdesk.mps_forecasted = 75
        result = self.Mps.get_data(self.computerdesk)[-1]
        self.assertEqual(result['forecasted'], 75.0, "Wrong calculation of forecasted.")
