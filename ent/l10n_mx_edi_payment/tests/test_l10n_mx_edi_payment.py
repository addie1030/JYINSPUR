import datetime

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

    def test_l10n_mx_edi_payment(self):
        journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        self.company.partner_id.property_account_position_id = self.fiscal_position.id # noqa
        invoice = self.create_invoice()
        invoice.move_name = 'INV/2017/999'
        today = self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime() # noqa
        invoice.action_invoice_open()
        self.assertEqual(invoice.l10n_mx_edi_pac_status, "signed",
                         invoice.message_ids.mapped("body"))
        ctx = {'active_model': 'account.invoice', 'active_ids': [invoice.id]}
        register_payments = self.env['account.register.payments'].with_context(ctx).create({ # noqa
            'payment_date': today - datetime.timedelta(days=5),
            'l10n_mx_edi_payment_method_id': self.payment_method_cash.id,
            'payment_method_id': self.payment_method_manual_out.id,
            'journal_id': journal.id,
            'communication': invoice.number,
            'amount': invoice.amount_total,
        })
        register_payments.create_payments()
        payment = invoice.payment_ids
        self.assertEqual(
            payment.l10n_mx_edi_pac_status, 'signed',
            payment.message_ids.mapped('body'))
