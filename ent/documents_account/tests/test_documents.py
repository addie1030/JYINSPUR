# -*- coding: utf-8 -*-

import base64
from odoo.tests.common import HttpCase, tagged, SavepointCase, TransactionCase, post_install

GIF = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
TEXT = base64.b64encode(bytes("workflow bridge account", 'utf-8'))


@tagged('post_install', '-at_install')
class TestCaseDocumentsBridgeAccount(TransactionCase):

    def setUp(self):
        super(TestCaseDocumentsBridgeAccount, self).setUp()
        self.folder_a = self.env['documents.folder'].create({
            'name': 'folder A',
        })
        self.folder_a_a = self.env['documents.folder'].create({
            'name': 'folder A - A',
            'parent_folder_id': self.folder_a.id,
        })
        self.attachment_txt = self.env['ir.attachment'].create({
            'datas': TEXT,
            'name': 'Test mimetype txt',
            'datas_fname': 'file.txt',
            'mimetype': 'text/plain',
            'folder_id': self.folder_a_a.id,
        })

        self.attachment_gif = self.env['ir.attachment'].create({
            'datas': GIF,
            'name': 'Test mimetype gif',
            'datas_fname': 'file.gif',
            'mimetype': 'image/gif',
            'folder_id': self.folder_a.id,
        })

        self.workflow_rule_vendor_bill = self.env['documents.workflow.rule'].create({
            'domain_folder_id': self.folder_a.id,
            'name': 'workflow rule create vendor bill on f_a',
            'create_model': 'account.invoice.in_invoice',
        })

    def test_bridge_folder_workflow(self):
        """
        tests the create new business model (vendor bill & credit note).

        """
        self.assertFalse(self.attachment_txt.res_model, "failed at workflow_bridge_dms_account original res model")
        multi_return = self.workflow_rule_vendor_bill.apply_actions([self.attachment_txt.id, self.attachment_gif.id])
        self.assertEqual(multi_return.get('type'), 'ir.actions.act_window',
                         'failed at invoice workflow return value type')
        self.assertEqual(multi_return.get('res_model'), 'account.invoice',
                         'failed at invoice workflow return value res model')
        self.assertEqual(multi_return.get('view_type'), 'list',
                         'failed at invoice workflow return value view type')

        self.assertEqual(self.attachment_txt.res_model, 'account.invoice', "failed at workflow_bridge_dms_account"
                                                                           " new res_model")
        vendor_bill_txt = self.env['account.invoice'].search([('id', '=', self.attachment_txt.res_id)])
        self.assertTrue(vendor_bill_txt.exists(), 'failed at workflow_bridge_dms_account vendor_bill')
        self.assertEqual(self.attachment_txt.res_id, vendor_bill_txt.id, "failed at workflow_bridge_dms_account res_id")
        self.assertEqual(vendor_bill_txt.type, 'in_invoice', "failed at workflow_bridge_dms_account vendor_bill type")
        vendor_bill_gif = self.env['account.invoice'].search([('id', '=', self.attachment_gif.res_id)])
        self.assertEqual(self.attachment_gif.res_id, vendor_bill_gif.id, "failed at workflow_bridge_dms_account res_id")

        single_return = self.workflow_rule_vendor_bill.apply_actions([self.attachment_txt.id])
        self.assertEqual(single_return.get('view_type'), 'form',
                         'failed at invoice workflow return value view type for single file')

