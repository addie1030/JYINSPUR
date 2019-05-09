# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError, Warning


class PsMaintenanceCost(models.TransientModel):
    _name = 'ps.maintenance.cost'
    _description = 'Storage Cost Maintenance'

    @api.multi
    def confirm_set_button(self):
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the records to be set.'))
        selectedList = self.env['stock.move'].browse(context.get('active_ids'))

        if selectedList:
            for rec in selectedList:
                price_single = self.env['product.template'].search([('id', '=', rec.product_id.id)]).ps_incoming_price
                rec.price_unit = price_single
                rec.value = rec.product_qty * price_single
                rec.remaining_value = rec.remaining_qty * price_single
        return {'type': 'ir.actions.act_window_close'}
