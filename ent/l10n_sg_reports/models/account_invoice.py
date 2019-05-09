# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _inherit = "account.invoice.line"

    l10n_sg_reports_amount_tax = fields.Monetary(string="Tax amount", store=True, compute="_compute_tax_product", help="Tax amount")
    l10n_sg_reports_amount_tax_no_change = fields.Monetary(string="Tax amount without change", store=True, compute="_compute_tax_product", help="Tax amount without change")
    l10n_sg_reports_tax = fields.Many2one('account.tax', compute="_compute_tax_product")

    @api.depends('invoice_id.state')
    def _compute_tax_product(self):
        for record in self:
            if record.invoice_id.state in ('open', 'in_payment', 'paid'):
                currency = record.invoice_id and record.invoice_id.currency_id or None
                price = record.price_unit * (1 - (record.discount or 0.0) / 100.0)
                taxes = False
                if record.invoice_line_tax_ids:
                    taxes = record.invoice_line_tax_ids.compute_all(price, currency, record.quantity, product=record.product_id, partner=record.invoice_id.partner_id)
                # According to IRAS document, there is only one tax
                amount_tax = taxes['taxes'][0]['amount'] if taxes else 0.0
                amount_tax_no_change = amount_tax
                if record.invoice_id.currency_id and record.invoice_id.company_id and record.invoice_id.currency_id != record.invoice_id.company_id.currency_id:
                    amount_tax = record.invoice_id.currency_id._convert(
                        amount_tax, record.invoice_id.company_id.currency_id, record.invoice_id.company_id, record.invoice_id.date_invoice or fields.Date.today())
                sign = record.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
                amount_tax *= sign
                amount_tax_no_change *= sign
                # Assignation
                record.l10n_sg_reports_amount_tax = amount_tax
                record.l10n_sg_reports_amount_tax_no_change = amount_tax_no_change
                record.l10n_sg_reports_tax = taxes['taxes'][0] if taxes else False
            else:
                record.l10n_sg_reports_amount_tax = 0.0
                record.l10n_sg_reports_amount_tax_no_change = 0.0
                record.l10n_sg_reports_tax = False
