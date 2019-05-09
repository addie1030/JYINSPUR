# coding: utf-8

from odoo.tools.pycompat import imap
from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class InvoiceTransactionCase(AccountingTestCase):
    def setUp(self):
        super(InvoiceTransactionCase, self).setUp()
        self.manager_billing = self.env['res.users'].with_context(no_reset_password=True).create({  # noqa
            'name': 'Manager billing mx',
            'login': 'mx_billing_manager',
            'email': 'mx_billing_manager@yourcompany.com',
            'company_id': self.env.ref('base.main_company').id,
            'groups_id': [(6, 0, [
                self.ref('account.group_account_manager'),
                self.ref('account.group_account_user'),
                self.ref('base.group_system'),
                self.ref('base.group_partner_manager')
            ])]
        })

        self.uid = self.manager_billing
        self.invoice_model = self.env['account.invoice']
        self.invoice_line_model = self.env['account.invoice.line']
        self.tax_model = self.env['account.tax']
        self.partner_agrolait = self.env.ref("base.res_partner_address_4")
        self.partner_agrolait.type = 'invoice'
        self.partner_agrolait.parent_id.street_name = 'Street Parent'
        self.product = self.env.ref("product.product_product_3")
        self.company = self.env.user.company_id
        self.account_settings = self.env['res.config.settings']
        self.tax_tag_iva = self.env['account.account.tag'].create({
            'name': 'IVA',
            'applicability': 'taxes',
        })
        self.tax_positive = self.tax_model.create({
            'name': 'IVA(16%) VENTAS TEST',
            'description': 'IVA(16%)',
            'amount': 16,
            'amount_type': 'percent',
            'type_tax_use': 'sale',
        })
        self.tax_positive.tag_ids |= self.tax_tag_iva
        self.tax_positive.l10n_mx_cfdi_tax_type = 'Tasa'
        self.tax_negative = self.tax_model.create({
            'name': 'ISR',
            'amount_type': 'percent',
            'amount': -10,
            'l10n_mx_cfdi_tax_type': 'Tasa',
        })
        self.product.taxes_id = [self.tax_positive.id, self.tax_negative.id]
        self.product.l10n_mx_edi_code_sat_id = self.ref(
            'l10n_mx_edi.prod_code_sat_01010101')
        self.payment_term = self.env.ref('account.account_payment_term_net')
        # force PPD
        self.payment_term.line_ids.days = 90
        self.fiscal_position_model = self.env['account.fiscal.position']
        self.fiscal_position = self.fiscal_position_model.create({
            'name': 'Personas morales del régimen general',
            'l10n_mx_edi_code': '601',
        })
        self.payment_method_cash = self.env.ref(
            'l10n_mx_edi.payment_method_efectivo')
        self.account_payment = self.env['res.partner.bank'].create({
            'acc_number': '123456789',
            'partner_id': self.partner_agrolait.id,
        })
        self.rate_model = self.env['res.currency.rate']
        self.mxn = self.env.ref('base.MXN')
        self.usd = self.env.ref('base.USD')
        self.ova = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref(
                'account.data_account_type_current_assets').id)], limit=1)
        self.user_billing = self.env['res.users'].with_context(no_reset_password=True).create({  # noqa
            'name': 'User billing mx',
            'login': 'mx_billing_user',
            'email': 'mx_billing_user@yourcompany.com',
            'company_id': self.env.ref('base.main_company').id,
            'groups_id': [(6, 0, [self.ref('account.group_account_invoice')])]
        })

    def set_currency_rates(self, mxn_rate, usd_rate):
        date = (self.env['l10n_mx_edi.certificate'].sudo().
                get_mx_current_datetime().date())
        self.mxn.rate_ids.filtered(
            lambda r: r.name == date).unlink()
        self.mxn.rate_ids = self.rate_model.create({
            'rate': mxn_rate, 'name': date})
        self.usd.rate_ids.filtered(
            lambda r: r.name == date).unlink()
        self.usd.rate_ids = self.rate_model.create({
            'rate': usd_rate, 'name': date})

    def create_invoice(self, inv_type='out_invoice', currency_id=None):
        if currency_id is None:
            currency_id = self.usd.id
        self.partner_agrolait.lang = None
        invoice = self.invoice_model.with_env(self.env(user=self.user_billing)).create({
            'partner_id': self.partner_agrolait.id,
            'type': inv_type,
            'currency_id': currency_id,
            'l10n_mx_edi_payment_method_id': self.payment_method_cash.id,
            'l10n_mx_edi_partner_bank_id': self.account_payment.id,
        })
        self.create_invoice_line(invoice)
        invoice.compute_taxes()
        # I manually assign a tax on invoice
        self.env['account.invoice.tax'].create({
            'name': 'Test Tax for Customer Invoice',
            'manual': 1,
            'amount': 0,
            'account_id': self.ova.id,
            'invoice_id': invoice.id,
        })
        return invoice

    def create_invoice_line(self, invoice_id):
        invoice_line = self.invoice_line_model.new({
            'product_id': self.product.id,
            'invoice_id': invoice_id,
            'quantity': 1,
        })
        invoice_line._onchange_product_id()
        invoice_line_dict = invoice_line._convert_to_write({
            name: invoice_line[name] for name in invoice_line._cache})
        invoice_line_dict['price_unit'] = 450
        self.invoice_line_model.create(invoice_line_dict)

    def xml_merge_dynamic_items(self, xml, xml_expected):
        xml_expected.attrib['Fecha'] = xml.attrib['Fecha']
        xml_expected.attrib['Sello'] = xml.attrib['Sello']
        xml_expected.attrib['Serie'] = xml.attrib['Serie']
        xml_expected.Complemento = xml.Complemento

    def xml2dict(self, xml):
        """Receive 1 lxml etree object and return a dict string.
        This method allow us have a precise diff output"""
        def recursive_dict(element):
            return (element.tag,
                    dict((recursive_dict(e) for e in element.getchildren()),
                         ____text=(element.text or '').strip(), **element.attrib))
        return dict([recursive_dict(xml)])

    def assertEqualXML(self, xml_real, xml_expected):
        """Receive 2 objectify objects and show a diff assert if exists."""
        xml_expected = self.xml2dict(xml_expected)
        xml_real = self.xml2dict(xml_real)
        # "self.maxDiff = None" is used to get a full diff from assertEqual method
        # This allow us get a precise and large log message of where is failing
        # expected xml vs real xml More info:
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.assertEqual(xml_real, xml_expected)
