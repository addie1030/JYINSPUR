# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class FollowupSend(models.TransientModel):
    _name = 'followup.send'
    _description = 'Followup Send'

    snailmail_cost = fields.Float(string='Stamp(s)', compute='_snailmail_estimate', readonly=True)
    letter_ids = fields.Many2many('snailmail.letter', 'snailmail_letter_followup_send_rel', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id, string="Currency")
    letters_qty = fields.Integer(compute='_compute_letters_qty')

    @api.multi
    @api.depends('letter_ids')
    def _compute_letters_qty(self):
        for wizard in self:
            wizard.letters_qty = len(wizard.letter_ids)

    @api.multi
    def _fetch_letters(self):
        self.ensure_one()
        if not self.letter_ids:

            res_ids = self._context.get('active_ids')
            partner_ids = self.env['res.partner'].browse(res_ids)
            letters = self.env['snailmail.letter']

            for partner in partner_ids:
                letter = letters.create({
                    'partner_id': partner.id,
                    'model': 'res.partner',
                    'res_id': partner.id,
                    'user_id': self.env.user.id,
                    'report_template': self.env.ref('account_reports.action_report_followup').id,
                    # we will only process partners that are linked to the user current company
                    # TO BE CHECKED
                    'company_id': self.env.user.company_id.id,
                })
                letters |= letter
            self.letter_ids = [(4, l.id) for l in letters]
        return self.letter_ids

    @api.multi
    @api.depends('letter_ids')
    def _snailmail_estimate(self):
        for wizard in self:
            letters = wizard._fetch_letters()
            if letters:
                wizard.snailmail_cost = letters._snailmail_estimate()

    @api.multi
    def snailmail_send_action(self):
        for wizard in self:
            letters = wizard._fetch_letters()
            letters.write({'state': 'pending'})
            if len(letters) == 1:
                letters._snailmail_print()
