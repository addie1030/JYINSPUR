from os.path import join
from lxml import objectify
from odoo.tools import misc
from odoo.addons.l10n_mx_edi.tests import common


class TestL10nMxEdiPayment(common.InvoiceTransactionCase):

    def setUp(self):
        super(TestL10nMxEdiPayment, self).setUp()
        self.fiscal_position.l10n_mx_edi_code = '601'
        self.config_parameter = self.env.ref(
            'l10n_mx_edi.l10n_mx_edi_version_cfdi')
        self.config_parameter.value = '3.3'
        self.tax_positive.l10n_mx_cfdi_tax_type = 'Tasa'
        self.tax_negative.l10n_mx_cfdi_tax_type = 'Tasa'
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        self.tax_negative.tag_ids |= isr_tag
        self.product.l10n_mx_edi_code_sat_id = self.ref(
            'l10n_mx_edi.prod_code_sat_01010101')
        self.payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out")
        self.bank = self.env.ref('base.bank_ing')
        self.bank.l10n_mx_edi_vat = 'BBA830831LJ2'
        self.company_bank = self.env['res.partner.bank'].create({
            'acc_number': '1234567890',
            'bank_id': self.bank.id,
            'partner_id': self.company.id,
        })
        self.account_payment.bank_id = self.bank.id
        self.account_payment.acc_number = '0123456789'
        self.transfer = self.ref('l10n_mx_edi.payment_method_transferencia')
        self.xml_expected_str = misc.file_open(join(
            'l10n_mx_edi_payment_bank', 'tests',
            'expected_payment.xml')).read().encode('UTF-8')
        self.xml_expected = objectify.fromstring(self.xml_expected_str)
        self.set_currency_rates(mxn_rate=12.21, usd_rate=1)

    def test_l10n_mx_edi_payment_bank(self):
        journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        journal.bank_account_id = self.company_bank
        self.company.partner_id.property_account_position_id = self.fiscal_position.id # noqa
        invoice = self.create_invoice()
        invoice.move_name = 'INV/2017/999'
        invoice.action_invoice_open()
        invoice.refresh()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped("body"))
        ctx = {'active_model': 'account.invoice', 'active_ids': [invoice.id]}
        register_payments = self.env['account.register.payments'].with_context(ctx).create({ # noqa
            'payment_date': invoice.date,
            'l10n_mx_edi_payment_method_id': self.transfer,
            'payment_method_id': self.payment_method_manual_out.id,
            'journal_id': journal.id,
            'communication': invoice.number,
            'amount': invoice.amount_total,
            'l10n_mx_edi_partner_bank_id': self.account_payment.id,
        })
        register_payments.create_payments()
        payment = invoice.payment_ids
        self.assertEqual(
            payment.l10n_mx_edi_pac_status, 'signed',
            payment.message_ids.mapped('body'))
        cfdi = payment.l10n_mx_edi_get_xml_etree()
        attribute = '//pago10:Pagos'
        namespace = {'pago10': 'http://www.sat.gob.mx/Pagos'}
        payment_xml = cfdi.Complemento.xpath(
            attribute, namespaces=namespace)[0]
        expected_xml = self.xml_expected.Complemento.xpath(
            attribute, namespaces=namespace)[0]
        expected_xml.Pago.attrib['FechaPago'] = payment_xml.Pago.get(
            'FechaPago')
        expected_xml.Pago.DoctoRelacionado.attrib[
            'IdDocumento'] = invoice.l10n_mx_edi_cfdi_uuid
        self.assertEqualXML(payment_xml, expected_xml)
