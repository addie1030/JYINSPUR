# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource


class TestCamtFile(TransactionCase):
    """ Tests for import bank statement CAMT file format (account.bank.statement.import) """

    def test_camt_file_import(self):
        # Get CAMT file content
        camt_file_path = get_module_resource('account_bank_statement_import_camt', 'test_camt_file', 'test_camt.xml')
        camt_file = base64.b64encode(open(camt_file_path, 'rb').read())

        # Create a bank account and journal corresponding to the CAMT file (same currency and account number)
        bank_journal = self.env['account.journal'].create({'name': 'Bank 123456', 'code': 'BNK67', 'type': 'bank',
                                                              'bank_acc_number': '123456'})
        bank_journal_id = bank_journal.id
        if bank_journal.company_id.currency_id != self.env.ref("base.USD"):
            bank_journal.write({'currency_id': self.env.ref("base.USD").id})

        # Use an import wizard to process the file
        import_wizard = self.env['account.bank.statement.import'].with_context(journal_id=bank_journal_id).create({'data_file': camt_file})
        import_wizard.import_file()

        # Check the imported bank statement
        bank_st_record = self.env['account.bank.statement'].search([('name', '=', '0574908765.2015-12-05')], limit=1)
        self.assertEqual(bank_st_record.balance_start, 8998.20, "Start balance not matched.")
        self.assertEqual(bank_st_record.balance_end_real, 2661.49, "End balance not matched.")

        # Check an imported bank statement line
        line = bank_st_record.line_ids.filtered(lambda r: r.ref == 'INNDNL2U20150105000217200000708')
        self.assertEqual(line.partner_name, 'Deco Addict')
        self.assertEqual(line.amount, 1636.88)
        self.assertEqual(line.partner_id.id, self.ref('base.res_partner_2'))

    def test_minimal_camt_file_import(self):
        # Create a bank account and journal corresponding to the CAMT
        # file (same currency and account number)
        bank_journal = self.env['account.journal'].create(
            {
                'name': "Bank 112233",
                'code': 'BNK68',
                'type': 'bank',
                'bank_acc_number': '112233',
            }
        )
        if bank_journal.company_id.currency_id != self.env.ref('base.USD'):
            bank_journal.write({'currency_id': self.env.ref('base.USD').id})

        # Use an import wizard to process the file
        camt_file_path = get_module_resource(
            'account_bank_statement_import_camt',
            'test_camt_file',
            'camt_053_minimal.xml',
        )
        with open(camt_file_path, 'rb') as fd:
            camt_file = base64.b64encode(fd.read())
        self.env['account.bank.statement.import'].with_context(
            journal_id=bank_journal.id
        ).create({'data_file': camt_file}).import_file()

        # Check the imported bank statement
        bank_st_record = self.env['account.bank.statement'].search(
            [('name', '=', '2514988305.2019-02-13')]
        ).ensure_one()
        self.assertEqual(
            bank_st_record.balance_start, 1000.00, "Start balance not matched"
        )
        self.assertEqual(
            bank_st_record.balance_end_real, 1500.00, "End balance not matched"
        )

        # Check the imported bank statement line
        line = bank_st_record.line_ids.ensure_one()
        self.assertEqual(line.amount, 500.00, "Transaction not matched")
