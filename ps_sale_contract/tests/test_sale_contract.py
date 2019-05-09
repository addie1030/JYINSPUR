# -*- coding: utf-8 -*-
import logging


from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleContract(TransactionCase):
    def setUp(self):
        super(TestSaleContract, self).setUp()
        self.customer_id = self.env.ref('ps_sale_contract.partner_demo_1').id
        self.product_id = self.env.ref('product.product_product_1').id

    def test_data(self):

        self.sale_contract = self.env['ps.sale.contract'].search([('customer_id', '=', self.customer_id)])
        self.sale_contract.onchange_customer_id()
        self.sale_contract._compute_valid_to()
        self.sale_contract._compute_amount_all()
        self.sale_contract.compute_amount_deliveried()
        self.sale_contract._compute_paid_amount()
        self.sale_contract.compute_is_expired()

        self.assertEqual(self.sale_contract.pricelist_id.name, 'Public Pricelist', 'The different pricelist')

        self.sale_contract.action_submit()
        self.assertEqual(self.sale_contract.state, 'confirmed', 'The button action_confirmed is not useful')
        self.sale_contract.action_approve()
        self.assertEqual(self.sale_contract.state, 'approved', 'The button action_approved is not useful')
        self.sale_contract.action_draft()
        self.assertEqual(self.sale_contract.state, 'draft', 'The button action_draft is not useful')
        self.sale_contract.unlink()

    def test_data_line(self):
        self.sale_contract = self.env['ps.sale.contract'].search([('customer_id', '=', self.customer_id)])
        self.sale_contract_line = self.env['ps.sale.contract.line'].search([('contract_id', '=', self.sale_contract.id)])[0]
        self.sale_contract_line.product_id_change()
        self.sale_contract_line._get_display_price(self.sale_contract_line.product_id)
        self.sale_contract_line.unlink()
