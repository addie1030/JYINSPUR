# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_edi_partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Partner Bank', help='If the payment was made '
        'with a financial institution define the bank account used in this '
        'payment.')

    @api.onchange('partner_id')
    def _l10n_mx_onchange_partner_bank_id(self):
        self.l10n_mx_edi_partner_bank_id = False
        if len(self.partner_id.commercial_partner_id.bank_ids) == 1:
            self.l10n_mx_edi_partner_bank_id = self.partner_id.commercial_partner_id.bank_ids  # noqa

    @api.multi
    def l10n_mx_edi_payment_data(self):
        self.ensure_one()
        res = super(AccountPayment, self).l10n_mx_edi_payment_data()
        partner_bank = self.l10n_mx_edi_partner_bank_id.bank_id
        company_bank = self.journal_id.bank_account_id
        payment_code = self.l10n_mx_edi_payment_method_id.code
        acc_emitter_ok = payment_code in [
            '02', '03', '04', '05', '06', '28', '29', '99']
        acc_receiver_ok = payment_code in [
            '02', '03', '04', '05', '28', '29', '99']
        bank_name_ok = payment_code in ['02', '03', '04', '28', '29', '99']
        vat = 'XEXX010101000' if partner_bank.country and partner_bank.country != self.env.ref(
            'base.mx') else partner_bank.l10n_mx_edi_vat
        res.update({
            'pay_vat_ord': vat if acc_emitter_ok else None,
            'pay_name_ord': partner_bank.name if bank_name_ok else None,
            'pay_account_ord': (self.l10n_mx_edi_partner_bank_id.acc_number or '').replace(
                ' ', '') if acc_emitter_ok else None,
            'pay_vat_receiver': company_bank.bank_id.l10n_mx_edi_vat if acc_receiver_ok else None,
            'pay_account_receiver': (company_bank.acc_number or '').replace(
                ' ', '') if acc_receiver_ok else None,
        })
        return res


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    l10n_mx_edi_partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Partner Bank', help='If the payment was made '
        'with a financial institution define the bank account used in this '
        'payment.')

    @api.onchange('partner_id')
    def _l10n_mx_onchange_partner_bank_id(self):
        self.l10n_mx_edi_partner_bank_id = False
        if len(self.partner_id.commercial_partner_id.bank_ids) == 1:
            self.l10n_mx_edi_partner_bank_id = self.partner_id.commercial_partner_id.bank_ids  # noqa

    @api.multi
    def _prepare_payment_vals(self, invoices):
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices)
        res['l10n_mx_edi_partner_bank_id'] = self.l10n_mx_edi_partner_bank_id.id  # noqa
        return res
