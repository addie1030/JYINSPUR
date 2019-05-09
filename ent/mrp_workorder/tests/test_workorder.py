# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import TransactionCase


class TestWorkOrder(TransactionCase):
    def test_workorder_1(self):
        # get the computer sc234 demo data
        prod = self.env.ref('product.product_product_3')
        bom = self.env.ref('mrp.mrp_bom_manufacture')

        # create a manufacturing order for it
        mo = self.env['mrp.production'].create({
            'product_id': prod.id,
            'product_uom_id': prod.uom_id.id,
            'bom_id': bom.id,
            'product_qty': 1,
        })

        # plan the work orders
        mo.button_plan()

