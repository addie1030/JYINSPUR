# -*- coding: utf-8 -*-

import base64
from odoo.tests.common import HttpCase, tagged, SavepointCase, TransactionCase

GIF = b"R0lGODdhAQABAIAAAP///////ywAAAAAAQABAAACAkQBADs="
TEXT = base64.b64encode(bytes("workflow bridge sign", 'utf-8'))


class TestCaseDocumentsBridgeSign(TransactionCase):
    """

    """
    def setUp(self):
        super(TestCaseDocumentsBridgeSign, self).setUp()

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
        self.workflow_rule_template = self.env['documents.workflow.rule'].create({
            'domain_folder_id': self.folder_a.id,
            'name': 'workflow rule create template on f_a',
            'create_model': 'sign.template',
        })

    def test_bridge_folder_workflow(self):
        """
        tests the create new business model (sign).
    
        """
        self.assertFalse(self.attachment_txt.res_model, "failed at workflow_bridge_dms_sign original res model")
        self.workflow_rule_template.apply_actions([self.attachment_txt.id])
    
        self.assertEqual(self.attachment_txt.res_model, 'sign.template', "failed at workflow_bridge_dms_sign"
                                                                         " new res_model")
        template = self.env['sign.template'].search([('id', '=', self.attachment_txt.res_id)])
        self.assertTrue(template.exists(), 'failed at workflow_bridge_dms_account template')
        self.assertEqual(self.attachment_txt.res_id, template.id, "failed at workflow_bridge_dms_account res_id")
