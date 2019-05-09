# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import _, api, models, fields
from odoo.exceptions import ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    l10n_mx_edi_customs_number = fields.Char(
        help='Optional field for entering the customs information in the case '
        'of first-hand sales of imported goods or in the case of foreign trade'
        ' operations with goods or services.\n'
        'The format must be:\n'
        ' - 2 digits of the year of validation followed by two spaces.\n'
        ' - 2 digits of customs clearance followed by two spaces.\n'
        ' - 4 digits of the serial number followed by two spaces.\n'
        ' - 1 digit corresponding to the last digit of the current year, '
        'except in case of a consolidated customs initiated in the previous '
        'year of the original request for a rectification.\n'
        ' - 6 digits of the progressive numbering of the custom.',
        string='Customs number',
        copy=False)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        products = []
        pattern = re.compile(r'[0-9]{2}  [0-9]{2}  [0-9]{4}  [0-9]{7}')
        for rec in self.mapped('invoice_line_ids').filtered(
                'l10n_mx_edi_customs_number'):
            for ped in rec.l10n_mx_edi_customs_number.split(','):
                if not pattern.match(ped.strip()):
                    products.append(rec.product_id.name)
        if not products:
            return super(AccountInvoice, self).action_invoice_open()
        products_wrong = '\n'.join(products)
        help_message = self.invoice_line_ids.fields_get().get(
            "l10n_mx_edi_customs_number").get("help").split('\n', 1)[1]
        raise ValidationError(_(
            'Error in the products:\n '
            '%s\n\n The format of the customs number is incorrect. %s \n'
            'For example: 15  48  3009  0001234') % (
                products_wrong, help_message))
