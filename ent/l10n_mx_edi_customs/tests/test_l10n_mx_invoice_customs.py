# coding: utf-8

from lxml import objectify
from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.exceptions import ValidationError


class TestL10nMxInvoiceCustoms(InvoiceTransactionCase):
    def setUp(self):
        super(TestL10nMxInvoiceCustoms, self).setUp()
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        self.tax_negative.tag_ids |= isr_tag
        self.company.partner_id.write({
            'property_account_position_id': self.fiscal_position.id,
        })

    def test_01_l10n_mx_edi_invoice_custom(self):
        """Test Invoice for information custom  with three cases:
        - Information custom wrong for sat
        - Information custom correct for sat
        - Invoice with more the one information custom correct"""

        invoice = self.create_invoice()
        invoice.move_name = 'INV/2017/997'
        customs_num = '15  48  30  001234'
        invoice.invoice_line_ids.l10n_mx_edi_customs_number = customs_num
        msg = ("Error in the products:.*%s.* The format of the customs "
               "number is incorrect.*For example: 15  48  3009  0001234") % (
                   invoice.invoice_line_ids.product_id.name)
        with self.assertRaisesRegexp(ValidationError, msg):
            invoice.action_invoice_open()

        node_expected = '''
        <cfdi:InformacionAduanera xmlns:cfdi="http://www.sat.gob.mx/cfd/3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        NumeroPedimento="15  48  3009  0001234"/>
        '''
        invoice = self.create_invoice()
        invoice.move_name = 'INV/2017/998'
        customs_number = '15  48  3009  0001234'
        invoice.invoice_line_ids.l10n_mx_edi_customs_number = customs_number
        invoice.action_invoice_open()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        xml_expected = objectify.fromstring(node_expected)
        self.assertEqualXML(xml.Conceptos.Concepto.InformacionAduanera,
                            xml_expected)

        node_expected_2 = '''
        <cfdi:InformacionAduanera xmlns:cfdi="http://www.sat.gob.mx/cfd/3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        NumeroPedimento="15  48  3009  0001235"/>
        '''
        invoice = self.create_invoice()
        invoice.move_name = 'INV/2017/999'
        customs_number = '15  48  3009  0001234,15  48  3009  0001235'
        invoice.invoice_line_ids.l10n_mx_edi_customs_number = customs_number
        invoice.action_invoice_open()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped('body'))
        xml = invoice.l10n_mx_edi_get_xml_etree()
        xml_expected = objectify.fromstring(node_expected)
        xml_expected_2 = objectify.fromstring(node_expected_2)
        self.assertEqualXML(xml.Conceptos.Concepto.InformacionAduanera[0],
                            xml_expected)
        self.assertEqualXML(xml.Conceptos.Concepto.InformacionAduanera[1],
                            xml_expected_2)
