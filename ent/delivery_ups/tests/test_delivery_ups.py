# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tests.common import TransactionCase, tagged


@tagged('-standard', 'external')
class TestDeliveryUPS(TransactionCase):

    def setUp(self):
        super(TestDeliveryUPS, self).setUp()

        self.iPadMini = self.env.ref('product.product_product_6')
        self.large_desk = self.env.ref('product.product_product_8')
        self.uom_unit = self.env.ref('uom.product_uom_unit')

        # Add a full address to "Your Company" and "Agrolait"
        self.your_company = self.env.ref('base.main_partner')
        self.your_company.write({'country_id': self.env.ref('base.us').id,
                                 'state_id': self.env.ref('base.state_us_5').id,
                                 'city': 'San Francisco',
                                 'street': '51 Federal Street',
                                 'zip': '94107'})
        self.agrolait = self.env.ref('base.res_partner_2')
        self.agrolait.write({'country_id': self.env.ref('base.be').id,
                             'city': 'Auderghem-Ouderghem',
                             'street': 'Avenue Edmond Van Nieuwenhuyse',
                             'zip': '1160'})
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')

    def test_01_ups_basic_flow(self):
        SaleOrder = self.env['sale.order']

        sol_vals = {'product_id': self.iPadMini.id,
                    'name': "[A1232] Large Cabinet",
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                    'price_unit': self.iPadMini.lst_price}

        # Set service type = 'UPS Worldwide Expedited', which is available between US to BE
        carrier = self.env.ref('delivery_ups.delivery_carrier_ups_us')
        carrier.write({'ups_default_service_type': '08',
                       'ups_package_dimension_unit': 'IN'})
        carrier.ups_default_packaging_id.write({'height': '3',
                                                'width': '3',
                                                'length': '3'})

        so_vals = {'partner_id': self.agrolait.id,
                   'carrier_id': carrier.id,
                   'order_line': [(0, None, sol_vals)]}

        sale_order = SaleOrder.create(so_vals)
        sale_order.get_delivery_price()
        self.assertTrue(sale_order.delivery_rating_success, "UPS has not been able to rate this order (%s)" % sale_order.delivery_message)
        self.assertGreater(sale_order.delivery_price, 0.0, "UPS delivery cost for this SO has not been correctly estimated.")
        sale_order.set_delivery_line()

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sales Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        picking.move_lines[0].quantity_done = 1.0
        self.assertGreater(picking.shipping_weight, 0.0, "Picking weight should be positive.")

        picking.action_done()
        self.assertIsNot(picking.carrier_tracking_ref, False, "UPS did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "UPS carrying price is probably incorrect")

        picking.cancel_shipment()
        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

    def test_02_ups_multipackage_flow(self):
        SaleOrder = self.env['sale.order']

        # Set packaging type = 'Pallet' and service type = 'UPS Worldwide Express Freight'
        # so in this case height, width and length required.
        carrier = self.env.ref('delivery_ups.delivery_carrier_ups_us')
        carrier.write({'ups_default_packaging_id': self.env.ref('delivery_ups.ups_packaging_30').id,
                       'ups_default_service_type': '96',
                       'ups_package_dimension_unit': 'IN'})
        carrier.ups_default_packaging_id.write({'height': '3',
                                                'width': '3',
                                                'length': '3'})

        sol_1_vals = {'product_id': self.iPadMini.id,
                      'name': "[A1232] Large Cabinet",
                      'product_uom': self.uom_unit.id,
                      'product_uom_qty': 1.0,
                      'price_unit': self.iPadMini.lst_price}

        sol_2_vals = {'product_id': self.large_desk.id,
                      'name': "[A1090] Large Desk",
                      'product_uom': self.uom_unit.id,
                      'product_uom_qty': 1.0,
                      'price_unit': self.large_desk.lst_price}

        so_vals = {'partner_id': self.agrolait.id,
                   'carrier_id': carrier.id,
                   'order_line': [(0, None, sol_1_vals), (0, None, sol_2_vals)]}

        sale_order = SaleOrder.create(so_vals)
        sale_order.get_delivery_price()
        self.assertTrue(sale_order.delivery_rating_success, "UPS has not been able to rate this order (%s)" % sale_order.delivery_message)
        self.assertGreater(sale_order.delivery_price, 0.0, "UPS delivery cost for this SO has not been correctly estimated.")
        sale_order.set_delivery_line()

        sale_order.action_confirm()
        self.assertEquals(len(sale_order.picking_ids), 1, "The Sales Order did not generate a picking.")

        picking = sale_order.picking_ids[0]
        self.assertEquals(picking.carrier_id.id, sale_order.carrier_id.id, "Carrier is not the same on Picking and on SO.")

        move0 = picking.move_lines[0]
        move0.quantity_done = 1.0
        picking._put_in_pack()
        move1 = picking.move_lines[1]
        move1.quantity_done = 1.0
        picking._put_in_pack()
        self.assertTrue(all([po.result_package_id is not False for po in picking.move_line_ids]), "Some products have not been put in packages")
        for p in picking.package_ids:
            p.shipping_weight = p.with_context({'picking_id': picking.id}).weight  # we mock choose.delivery.package wizard
        self.assertGreater(picking.shipping_weight, 0.0, "Picking weight should be positive.")

        picking.action_done()
        self.assertIsNot(picking.carrier_tracking_ref, False, "UPS did not return any tracking number")
        self.assertGreater(picking.carrier_price, 0.0, "UPS carrying price is probably incorrect")

        picking.cancel_shipment()
        self.assertFalse(picking.carrier_tracking_ref, "Carrier Tracking code has not been properly deleted")
        self.assertEquals(picking.carrier_price, 0.0, "Carrier price has not been properly deleted")

    def test_03_ups_flow_from_delivery_order(self):

        inventory = self.env['stock.inventory'].create({
            'name': '[A1232] iPad Mini',
            'filter': 'product',
            'location_id': self.stock_location.id,
            'product_id': self.iPadMini.id,
        })

        # Set service type = 'UPS Worldwide Expedited', which is available between US to BE
        carrier = self.env.ref('delivery_ups.delivery_carrier_ups_us')
        carrier.write({'ups_default_service_type': '08',
                       'ups_package_dimension_unit': 'IN'})
        carrier.ups_default_packaging_id.write({'height': '3',
                                                'width': '3',
                                                'length': '3'})

        StockPicking = self.env['stock.picking']

        order1_vals = {
                    'product_id': self.iPadMini.id,
                    'name': "[A1232] iPad Mini",
                    'product_uom': self.uom_unit.id,
                    'product_uom_qty': 1.0,
                    'location_id': self.stock_location.id,
                    'location_dest_id': self.customer_location.id}

        do_vals = { 'partner_id': self.agrolait.id,
                    'carrier_id': carrier.id,
                    'location_id': self.stock_location.id,
                    'location_dest_id': self.customer_location.id,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                    'move_ids_without_package': [(0, None, order1_vals)]}

        delivery_order = StockPicking.create(do_vals)
        self.assertEqual(delivery_order.state, 'draft', 'Shipment state should be draft.')

        delivery_order.action_confirm()
        self.assertEqual(delivery_order.state, 'confirmed', 'Shipment state should be waiting(confirmed).')

        delivery_order.action_assign()
        self.assertEqual(delivery_order.state, 'assigned', 'Shipment state should be ready(assigned).')
        delivery_order.move_ids_without_package.quantity_done = 1.0

        delivery_order.button_validate()
        self.assertEqual(delivery_order.state, 'done', 'Shipment state should be done.')
