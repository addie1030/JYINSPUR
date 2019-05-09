# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

import time

from odoo import fields

from odoo.addons.account.tests.account_test_classes import AccountingTestCase

from odoo.modules.module import get_module_resource
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class SDDTest(AccountingTestCase):

    def create_user(self):
        return self.env['res.users'].create({
            'company_id': self.env.ref("base.main_company").id,
            'name': "Ruben Rybnik",
            'login': "ruben",
            'email': "ruben.rybnik@sorcerersfortress.com",
            'groups_id': [(6, 0, [self.ref('account.group_account_invoice')])]
        })

    def create_account(self, number, partner, bank):
        return self.env['res.partner.bank'].create({
            'acc_number': number,
            'partner_id': partner.id,
            'bank_id': bank.id
        })

    def create_mandate(self,partner, partner_bank, one_off, company, current_uid, payment_journal):
        return self.env['sdd.mandate'].with_context({'uid': current_uid}).create({
            'name': 'mandate ' + (partner.name or ''),
            'original_doc': '42',
            'partner_bank_id': partner_bank.id,
            'one_off': one_off,
            'start_date': fields.Date.today(),
            'partner_id': partner.id,
            'company_id': company.id,
            'payment_journal_id': payment_journal.id
        })

    def create_invoice(self, partner, current_uid, currency):
        account_receivable = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1)
        product = self.env.ref("product.product_product_4")
        account_revenue = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)], limit=1)

        invoice = self.env['account.invoice'].with_context({'uid': current_uid}).create({
            'partner_id': partner.id,
            'currency_id': currency.id,
            'name': 'invoice to client',
            'account_id': account_receivable.id,
            'type': 'out_invoice',
        })

        self.env['account.invoice.line'].create({
            'product_id': product.id,
            'quantity': 1,
            'price_unit': 42,
            'invoice_id': invoice.id,
            'name': 'something',
            'account_id': account_revenue.id,
        })

        invoice.action_invoice_open()

        return invoice

    def test_sdd(self):
        # We generate the user whose the test will simulate the actions.
        user = self.create_user()

        # We setup our test company
        company = user.company_id
        company.sdd_creditor_identifier = 'BE30ZZZ300D000000042'
        company_bank_journal = self.env['account.journal'].search([('company_id', '=', company.id), ('type', '=', 'bank')], limit=1)
        company_bank_journal.bank_acc_number = 'CH9300762011623852957'
        company_bank_journal.bank_account_id.bank_id = self.env.ref('base.bank_ing')

        # Then we setup the banking data and mandates of two customers (one with a one-off mandate, the other with a recurrent one)
        partner_agrolait = self.env.ref("base.res_partner_2")
        partner_bank_agrolait = self.create_account('DE44500105175407324931', partner_agrolait, self.env.ref('base.bank_ing'))
        mandate_agrolait = self.create_mandate(partner_agrolait, partner_bank_agrolait, False, company, user.id, company_bank_journal)
        mandate_agrolait.action_validate_mandate()

        partner_china_export = self.env.ref("base.res_partner_3")
        partner_bank_china_export = self.create_account('SA0380000000608010167519', partner_china_export, self.env.ref('base.bank_bnp'))
        mandate_china_export = self.create_mandate(partner_china_export, partner_bank_china_export, True, company, user.id, company_bank_journal)
        mandate_china_export.action_validate_mandate()

        # We create one invoice for each of our test customers ...
        invoice_agrolait = self.create_invoice(partner_agrolait, user.id, company.currency_id)
        invoice_china_export = self.create_invoice(partner_china_export, user.id, company.currency_id)

        #These invoice should have been paid automatically thanks to the mandate
        self.assertEqual(invoice_agrolait.state, 'paid', 'This invoice should have been paid thanks to the mandate')
        self.assertEqual(invoice_china_export.state, 'paid', 'This invoice should have been paid thanks to the mandate')

        #The 'one-off' mandate should now be closed
        self.assertEqual(mandate_agrolait.state, 'active', 'A recurrent mandate should stay confirmed after accepting a payment')
        self.assertEqual(mandate_china_export.state, 'closed', 'A one-off mandate should be closed after accepting a payment')

        #Let us check the conformity of XML generation :
        xml_file = etree.fromstring(invoice_agrolait.payment_ids.generate_xml(company, fields.Date.today()))

        schema_file_path = get_module_resource('account_sepa_direct_debit', 'schemas', 'pain.008.001.02.xsd')
        xml_schema = etree.XMLSchema(etree.parse(open(schema_file_path)))

        self.assertTrue(xml_schema.validate(xml_file), xml_schema.error_log.last_error)
