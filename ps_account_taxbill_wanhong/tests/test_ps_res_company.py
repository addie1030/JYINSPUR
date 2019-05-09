# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged

class TestTaxbillRegister(TransactionCase):

    def test_taxbill_register(self):
        self.res_company.taxbill_register()





