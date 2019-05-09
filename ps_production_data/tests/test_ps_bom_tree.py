# -*- coding: utf-8 -*-

import odoo
from odoo.tests import TransactionCase, tagged

class TestPsBomTree(TransactionCase):

    def setUp(self):
        super(TestPsBomTree, self).setUp()
        self.Bom = self.env['mrp.bom'].browse(1)
        self.ps_bom_tree = self.env['ps.bom.tree']

    def test_table_create(self):
        self.ps_bom_tree.table_create()

    def tearDown(self):
        pass

    def test_tree_parent(self):
        self.ps_bom_tree.tree_parent(self.Bom.id)
