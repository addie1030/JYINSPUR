# -*- coding: utf-8 -*-

import odoo
from odoo.tests import TransactionCase, tagged

class TestPsMrpBom(TransactionCase):

    def setUp(self):
        super(TestPsMrpBom, self).setUp()

        category_id = self.ref('product.product_category_5')
        uom_id = self.ref('uom.product_uom_unit')
        self.product = self.env['product.product'].create({
            'name': 'test',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
        })
        self.product_1 = self.env['product.product'].create({
            'name': 'test1',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'test2',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
        })
        self.product_3 = self.env['product.product'].create({
            'name': 'test3',
            'categ_id': category_id,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'type': 'product',
        })
        self.ps_mrp_bom = self.env['mrp.bom'].create({
            'product_id': self.product.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_1.id}),
                (0, 0, {'product_id': self.product_2.id})
            ]
        })

        self.ps_mrp_bom.write({
            'bom_line_ids': [(0, 0, {'product_id': self.product_3.id})]
        })

    def tearDown(self):
        pass

    def test_search_view_id(self):
        sql = """select * from ps_bom_tree where child_id = %s""" % (self.ps_mrp_bom.id)
        self.env.cr.execute(sql)
        self.line = self.env.cr.fetchone()
        self.id = self.line[0]
        self.version = self.line[6]
        self.child_id = self.line[2]
        self.env['mrp.bom'].search_view_id(self.id, self.version, self.child_id)