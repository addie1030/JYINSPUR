# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestReleaseToPayInvoice(AccountingTestCase):

    def check_release_to_pay_scenario(self, ordered_qty, scenario, invoicing_policy='receive', order_price=500.0):
        """ Generic test function to check that each use scenario behaves properly.
        """
        partner = self.env.ref('base.res_partner_1')
        product = self.env['product.product'].create({
            'name': 'VR Computer',
            'standard_price': 2500.0,
            'list_price': 2899.0,
            'type': 'service',
            'default_code': 'VR-01',
            'weight': 1.0,
            'purchase_method': 'receive',
        })

        product.purchase_method = invoicing_policy

        purchase_order = self.env['purchase.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_qty': ordered_qty,
                    'product_uom': product.uom_po_id.id,
                    'price_unit': order_price,
                    'date_planned': fields.Datetime.now(),
                })]
        })
        purchase_order.button_confirm()

        invoices_list = []
        purchase_line = purchase_order.order_line[-1]
        for (action, params) in scenario:
            if action == 'invoice':
                new_invoice = self.env['account.invoice'].create({
                    'partner_id': partner.id,
                    'purchase_id': purchase_order.id,
                    'account_id': partner.property_account_payable_id.id,
                    'type': 'in_invoice'
                })

                new_invoice.purchase_order_change()

                for invoice_line in new_invoice.invoice_line_ids:
                    if 'price' in params:
                        invoice_line.write({'price_unit': params['price']})
                    invoice_line.write({'quantity': params['qty']})

                invoices_list.append(new_invoice)

                self.assertEquals(new_invoice.release_to_pay, params['rslt'], "Wrong invoice release to pay status for scenario " + str(scenario))

            elif action == 'receive':
                purchase_line.write({'qty_received': params['qty']})  # as the product is a service, its recieved quantity is set manually

                if 'rslt' in params:
                    for (invoice_index, status) in params['rslt']:
                        self.assertEquals(invoices_list[invoice_index].release_to_pay, status, "Wrong invoice release to pay status for scenario " + str(scenario))

    def test_3_way_match(self):
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 5, 'rslt': 'yes'})], invoicing_policy='purchase')
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 10, 'rslt': 'yes'})], invoicing_policy='purchase')
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 10, 'rslt': 'yes'})], invoicing_policy='purchase')
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 5, 'rslt': 'yes'}), ('receive',{'qty': 5}), ('invoice', {'qty': 6, 'rslt': 'exception'})], invoicing_policy='purchase')
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 10, 'rslt': 'yes'}), ('invoice', {'qty': 10, 'rslt': 'no'})], invoicing_policy='purchase')
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 5, 'rslt': 'yes'})])
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 10, 'rslt': 'exception'})])
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 5, 'rslt': 'no'})])
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 5, 'rslt': 'no'}), ('receive', {'qty': 5, 'rslt': [(-1, 'yes')]})])
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 5, 'rslt': 'no'}), ('receive', {'qty': 3, 'rslt': [(-1, 'exception')]})])
        self.check_release_to_pay_scenario(10, [('invoice', {'qty': 5, 'rslt': 'no'}), ('receive', {'qty': 10, 'rslt': [(-1, 'yes')]})])

        # Special use case : a price change between order and invoice should always put the bill in exception
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 5, 'rslt': 'exception', 'price':42})])
        self.check_release_to_pay_scenario(10, [('receive',{'qty': 5}), ('invoice', {'qty': 5, 'rslt': 'exception', 'price':42})], invoicing_policy='purchase')
