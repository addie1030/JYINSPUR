# -*- coding: utf-8 -*-
from odoo.addons.account.tests.account_test_classes import AccountingTestCase


class TestSubscriptionCommon(AccountingTestCase):

    def setUp(self):
        super(TestSubscriptionCommon, self).setUp()
        Analytic = self.env['account.analytic.account']
        Subscription = self.env['sale.subscription']
        SubTemplate = self.env['sale.subscription.template']
        SaleOrder = self.env['sale.order']
        Tax = self.env['account.tax']
        Product = self.env['product.product']
        ProductTmpl = self.env['product.template']

        # Test Subscription Template
        self.subscription_tmpl = SubTemplate.create({
            'name': 'TestSubscriptionTemplate',
            'description': 'Test Subscription Template 1',
        })
        self.subscription_tmpl_2 = SubTemplate.create({
            'name': 'TestSubscriptionTemplate2',
            'description': 'Test Subscription Template 2',
        })
        self.subscription_tmpl_3 = SubTemplate.create({
            'name': 'TestSubscriptionTemplate3',
            'description': 'Test Subscription Template 3',
            'recurring_rule_boundary':'limited'
        })

        # Test taxes
        self.percent_tax = Tax.create({
            'name': "Percent tax",
            'amount_type': 'percent',
            'amount': 10,
        })

        # Test products
        self.product_tmpl = ProductTmpl.create({
            'name': 'TestProduct',
            'type': 'service',
            'recurring_invoice': True,
            'subscription_template_id': self.subscription_tmpl.id,
            'uom_id': self.ref('uom.product_uom_unit'),
        })
        self.product = Product.create({
            'product_tmpl_id': self.product_tmpl.id,
            'price': 50.0,
            'taxes_id': [(6, 0, [self.percent_tax.id])],
        })

        self.product_tmpl_2 = ProductTmpl.create({
            'name': 'TestProduct2',
            'type': 'service',
            'recurring_invoice': True,
            'subscription_template_id': self.subscription_tmpl_2.id,
            'uom_id': self.ref('uom.product_uom_unit'),
        })
        self.product2 = Product.create({
            'product_tmpl_id': self.product_tmpl_2.id,
            'price': 20.0,
            'taxes_id': [(6, 0, [self.percent_tax.id])],
        })

        self.product_tmpl_3 = ProductTmpl.create({
            'name': 'TestProduct3',
            'type': 'service',
            'recurring_invoice': True,
            'subscription_template_id': self.subscription_tmpl_2.id,
            'uom_id': self.ref('uom.product_uom_unit'),
        })
        self.product3 = Product.create({
            'product_tmpl_id': self.product_tmpl_3.id,
            'price': 15.0,
            'taxes_id': [(6, 0, [self.percent_tax.id])],
        })

        self.product_tmpl_4 = ProductTmpl.create({
            'name': 'TestProduct4',
            'type': 'service',
            'recurring_invoice': True,
            'subscription_template_id': self.subscription_tmpl_3.id,
            'uom_id': self.ref('uom.product_uom_unit'),
        })
        self.product4 = Product.create({
            'product_tmpl_id': self.product_tmpl_4.id,
            'price': 15.0,
            'taxes_id': [(6, 0, [self.percent_tax.id])],
        })

        # Test user
        TestUsersEnv = self.env['res.users'].with_context({'no_reset_password': True})
        group_portal_id = self.ref('base.group_portal')
        self.user_portal = TestUsersEnv.create({
            'name': 'Beatrice Portal',
            'login': 'Beatrice',
            'email': 'beatrice.employee@example.com',
            'groups_id': [(6, 0, [group_portal_id])]
        })

        # Test analytic account
        self.account_1 = Analytic.create({
            'partner_id': self.user_portal.partner_id.id,
            'name': 'Test Account 1',
        })
        self.account_2 = Analytic.create({
            'partner_id': self.user_portal.partner_id.id,
            'name': 'Test Account 2',
        })

        # Test Subscription
        self.subscription = Subscription.create({
            'name': 'TestSubscription',
            'partner_id': self.user_portal.partner_id.id,
            'pricelist_id': self.ref('product.list0'),
            'template_id': self.subscription_tmpl.id,
        })
        self.sale_order = SaleOrder.create({
            'name': 'TestSO',
            'partner_id': self.user_portal.partner_id.id,
            'partner_invoice_id': self.user_portal.partner_id.id,
            'partner_shipping_id': self.user_portal.partner_id.id,
            'order_line': [(0, 0, {'name': self.product.name, 'product_id': self.product.id, 'subscription_id': self.subscription.id, 'product_uom_qty': 2, 'product_uom': self.product.uom_id.id, 'price_unit': self.product.list_price})],
            'pricelist_id': self.ref('product.list0'),
        })
        self.sale_order_2 = SaleOrder.create({
            'name': 'TestSO2',
            'partner_id': self.user_portal.partner_id.id,
            'order_line': [(0, 0, {'name': self.product.name, 'product_id': self.product.id, 'product_uom_qty': 1.0, 'product_uom': self.product.uom_id.id, 'price_unit': self.product.list_price})]
        })
        self.sale_order_3 = SaleOrder.create({
            'name': 'TestSO3',
            'partner_id': self.user_portal.partner_id.id,
            'order_line': [(0, 0, {'name': self.product.name, 'product_id': self.product.id, 'product_uom_qty': 1.0, 'product_uom': self.product.uom_id.id, 'price_unit': self.product.list_price, }), (0, 0, {'name': self.product2.name, 'product_id': self.product2.id, 'product_uom_qty': 1.0, 'product_uom': self.product2.uom_id.id, 'price_unit': self.product2.list_price})],
        })
        self.sale_order_4 = SaleOrder.create({
            'name': 'TestSO4',
            'partner_id': self.user_portal.partner_id.id,
            'order_line': [(0, 0, {'name': self.product2.name, 'product_id': self.product2.id, 'product_uom_qty': 1.0, 'product_uom': self.product2.uom_id.id, 'price_unit': self.product2.list_price}), (0, 0, {'name': self.product3.name, 'product_id': self.product3.id, 'product_uom_qty': 1.0, 'product_uom': self.product3.uom_id.id, 'price_unit': self.product3.list_price})],
        })
        self.sale_order_5 = SaleOrder.create({
            'name': 'TestSO5',
            'partner_id': self.user_portal.partner_id.id,
            'order_line': [(0, 0, {'name': self.product4.name, 'product_id': self.product4.id, 'product_uom_qty': 1.0, 'product_uom': self.product4.uom_id.id, 'price_unit': self.product4.list_price})]
        })
