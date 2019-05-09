# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    ps_inventory_inspection_date = fields.Datetime(string='Inventory Inspection Date',
                                                   compute='_compute_inspection_date')
    ps_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                      compute='_compute_inspection_date')
    ps_is_request = fields.Boolean(default=False)
    ps_is_date_company = fields.Boolean(default=False)
    location_id = fields.Many2one('stock.location', 'Location')  # inherit this field for changing translation

    @api.multi
    def _compute_inspection_date(self):
        # Compute ps_inventory_inspection_date and ps_warehouse_id.
        for inspection in self:
            record = self.env['stock.production.lot'].search([('id', '=', inspection.lot_id.id)])
            if record:
                move_ids = self.env['stock.move.line'].search(
                    [('lot_id', '=', record.id), ('product_id', '=', record.product_id.id)])
                picking_ids = [move_id.picking_id for move_id in move_ids] if move_ids else None
                if picking_ids:
                    check_date = []
                    for picking_id in picking_ids:
                        if self.env['quality.point'].search(
                                [('product_tmpl_id', '=', record.product_id.product_tmpl_id.id), (
                                        'picking_type_id', '=',
                                        picking_id.picking_type_id.id)]) and picking_id.date_done:
                            check_date.append(picking_id.date_done)
                        else:
                            continue
                    quality_check_date_max = max(check_date) if check_date else None
                    if quality_check_date_max:
                        inventory_inspection_time = self.env['product.template'].search(
                            [('id', '=', record.product_id.id)]).ps_inventory_inspection_time
                        if not inventory_inspection_time:
                            inventory_inspection_time = 0
                        inspection.ps_inventory_inspection_date = quality_check_date_max + relativedelta(
                            days=inventory_inspection_time)
                inspection.ps_warehouse_id = inspection.location_id.get_warehouse().id
                if inspection.ps_warehouse_id and inspection.ps_inventory_inspection_date:
                    self.env['stock.quant'].sudo().search([('id', '=', inspection.id)]).write(
                        {'ps_is_date_company': True})
                else:
                    self.env['stock.quant'].sudo().search([('id', '=', inspection.id)]).write(
                        {'ps_is_date_company': False})
                if inspection.location_id.id == inspection.location_id.get_warehouse().ps_inspect_wh_id.id:
                    self.env['stock.quant'].sudo().search([('id', '=', inspection.id)]).write({'ps_is_request': True})

    @api.multi
    def move_to_inventory_check_request(self):
        # Click 'Inventory Check Request'to add record
        if self.user_has_groups("stock.group_stock_user"):
            for inventory in self:
                check_request_line = self.env['ps.quality.inventory.check.request'].sudo().search([
                    ('lot_ids.location_id', '=', inventory.location_id.id),
                    ('lot_ids.lot_id', '=', inventory.lot_id.id),
                    ('state', '=', 'draft')])
                if inventory.ps_inventory_inspection_date:
                    if check_request_line:
                        raise UserError(_('The record has been requested to check'))
                    self.env['ps.quality.inventory.check.request'].sudo().create({
                        'date': fields.Date.today(),
                        'user_id': inventory.env.user.id,
                        'warehouse_id': inventory.ps_warehouse_id.id,
                        'lot_ids': [(0, 0, {
                            'product_id': inventory.product_id.id,
                            'quantity': inventory.quantity,
                            'uom_id': inventory.product_uom_id.id,
                            'warehouse_id': inventory.ps_warehouse_id.id,
                            'location_id': inventory.location_id.id,
                            'lot_id': inventory.lot_id.id
                        })]
                    })
                    self.env['stock.quant'].sudo().search([('id', '=', inventory.id)]).write({'ps_is_request': True})
                else:
                    raise UserError(_('This product does not require quality control!'))
        else:
            raise UserError(_('limited authority'))

    def action_quality_check_filter(self):
        self.env['stock.quant'].sudo().search([])._compute_inspection_date()
        action = self.env.ref('ps_quality_management.action_quality_inventory_check').read()[0]
        action['domain'] = [('ps_is_date_company', '!=', False), ('quantity', '>', 0), ('ps_is_request', '!=', True)]
        return action
