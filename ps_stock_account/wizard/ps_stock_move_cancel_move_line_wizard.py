# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools


class PsUnCheckAccountMove(models.TransientModel):
    _name = "ps.cancel.move"
    _description = _("Stock Cancel Move")

    @api.multi
    def cancel_selected_move(self):
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError('Please select the record records to be cancel.')
        selected_list = self.env['ps.stock.account.china.center.cancel.move'].browse(context.get('active_ids'))
        print(selected_list)
        if selected_list:
            for rec in selected_list:
                res_move = self.env['account.move'].search([('id', '=', rec.account_move_id)])
                if res_move:
                    for i in res_move:
                        if i.state != 'draft':
                            raise UserError(_('Non-order status cannot cancel the voucher.'))
                res_move_line = self.env['account.move.line'].search([('move_id', '=', rec.account_move_id)])
                if res_move_line:
                    res_move_line.unlink()
                res_move = self.env['account.move'].search([('id', '=', rec.account_move_id)])
                if res_move:
                    res_move.unlink()
                stock_move = self.env['stock.move'].search([('id', '=', rec.id)])
                stock_move.write({'account_move_id': 0})
        return {'type': 'ir.actions.act_window_close'}
