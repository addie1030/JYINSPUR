# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        """Inherit method for add custom information in invoice's line"""
        self.filtered(
            lambda r:
            r.l10n_mx_edi_is_required())._generate_customs_information()
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def _generate_customs_information(self):
        """Search custom information in move type out"""
        landed_obj = self.env['stock.landed.cost']
        for line in self.mapped('invoice_line_ids').filtered('sale_line_ids'):
            moves = line.mapped('sale_line_ids.move_ids').filtered(
                lambda r: r.state == 'done' and not r.scrapped)
            landed = landed_obj.sudo().search(
                [('picking_ids', 'in',
                    moves.mapped('move_orig_fifo_ids.picking_id').ids),
                    ('l10n_mx_edi_customs_number', '!=', False)])
            if not moves or not landed:
                continue
            line.l10n_mx_edi_customs_number = ','.join(
                list(set(landed.mapped('l10n_mx_edi_customs_number'))))
