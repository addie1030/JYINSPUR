# -*- coding: utf-8 -*-

import odoo
from odoo.tests import TransactionCase, tagged

class TestPsAccountTaxbill(TransactionCase):

    def setUp(self):
        super(TestPsAccountTaxbill, self).setUp()
        self.Partner = self.env['res.partner'].browse(1)
        self.User = self.env['res.users'].browse(1)
        self.Product = self.env['product.product'].browse(1)
        self.Company = self.env['res.company'].browse(1)
        self.Taxbill_null_obj=self.env['ps.account.taxbill']
        self.Inv_line_value = ({
            'product_id': self.Product.id,
            'quantity': 2,
            'name': self.Product.name,
            'price_unit': 200,
            'display_type': 'line_section',
            'discount': 0,
        })
        self.Invoice = self.env['account.invoice'].create({
            'partner_id': self.Partner.id,
            'name': 'New',
            'invoice_line_ids': [(0,0,self.Inv_line_value)]
        })
        self.Taxbill_line_value = ({
            'product_id': self.Product.id,
            'quantity': 2,
            'invoices_available_quantity': 12,
            'name': self.Product.name,
            'price_unit': 200,
            'uom_id': self.Product.uom_id.id,
            'discount': 0,
            'invoice_id': self.Invoice.id,
            'invoice_line_id': [line.id for line in self.Invoice.invoice_line_ids][0],
        })
        self.Taxbill = self.env['ps.account.taxbill'].create({
            'partner_id': self.Partner.id,
            'user_id': self.User.id,
            'name': 'New',
            'company_id': self.Company.id,
            'taxbill_type': '1',
            'apply_line_ids': [(0, 0, self.Taxbill_line_value)],
            'invoice_ids': (0,0,self.Invoice.id),
        })


    def tearDown(self):
        pass

    def test_data(self):
        self.assertTrue(self.Taxbill.id, 'Cannot create tax bill data!')

    def test_onchange_partner_id(self):
        """
        测试选择partner改变invoice的domain
        :return:
        """
        self.assertTrue(self.Taxbill_null_obj.onchange_partner_id(), 'Onchange partner false!')
        self.Taxbill_null_obj

    def test_create(self):
        """
        测试创建
        """
        vals={
            'partner_id': self.Partner.id,
            'user_id': self.User.id,
            'name': 'New',
            'company_id': self.Company.id,
            'taxbill_type': '1',
            'apply_line_ids': [(0, 0, self.Taxbill_line_value)],
            'invoice_ids': (0,0,self.Invoice.id),
        }
        self.assertTrue(self.Taxbill_null_obj.create(vals), 'Cannot create tax bill data!')

    def test_unlink(self):
        """
        测试删除
        """
        self.assertTrue(self.Taxbill.unlink(), 'Cannot delete tax bill data!')

    def test_onchange_invoice_ids(self):
        self.assertIsNone(self.Taxbill._onchange_invoice_ids(), 'Onchange invoices false!')

    def test_write(self):
        """
        测试更改
        """
        vals = {
            'apply_line_ids': [(0, 0, self.Taxbill_line_value)],
        }
        self.assertTrue(self.Taxbill_null_obj.write(vals), 'Write tax bill Error!')

