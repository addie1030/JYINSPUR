# -*- coding: utf-8 -*-
"""
You can find two models in this file.They are ps_quality_inventory_check_request and
ps_quality_inventory_check_request_line.These two models are created for the application
stock request check.
"""
from odoo import models, fields, _
from odoo.exceptions import UserError


class QualityInventoryCheckRequest(models.Model):
    _name = 'ps.quality.inventory.check.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Quality Inventory Check Request'

    name = fields.Char(string='Name', default=lambda self: _('New'))
    date = fields.Date(string='Date', help='Date changes with state.')
    user_id = fields.Many2one('res.users', string='User')
    state = fields.Selection([('draft', "Draft"),
                              ('confirmed', "Confirmed"),
                              ('done', "Done"),
                              ('cancelled', "Cancelled")], string='Status', default='draft',
                             index=True, track_visibility='onchange')
    lot_ids = fields.One2many('ps.quality.inventory.check.request.line', 'ps_lot_id', string='Line')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    def create(self, vals):
        # When you create one record, the field name automatically generate with structure QICR#xxxxxx.
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.quality.inventory.check.request')
        return super(QualityInventoryCheckRequest, self).create(vals)

    def action_draft(self):
        # Change state draft.
        self.env['stock.quant'].sudo().search([('lot_id', '=', self.lot_ids.lot_id.id),
                                               ('location_id', '=', self.lot_ids.location_id.id)]).write(
            {'ps_is_request': True})
        self.date = fields.Date.today()
        return self.write({'state': 'draft'})

    def action_confirm(self):
        # Change state from draft to confirmed.
        if self.env['quality.point'].search([('picking_type_id', '=', self.env['stock.warehouse'].search([
            ('id', '=', self.warehouse_id.id)]).inventory_check_type_id.id)]):
            self.date = fields.Date.today()
            return self.write({'state': 'confirmed'})
        else:
            raise UserError(_('Please ensure that this batch of products have a quality control plan!'))

    def action_done(self):
        """
        Products from the original location to the request check location,
        and then from the request check location to the original location,
        last change the state from confirmed to done.
        """
        if self.env['stock.warehouse'].search([('id', '=', self.warehouse_id.id)]).inventory_check_type_id.id:
            move_to_check = self.env['stock.move'].create({
                'name': self.lot_ids.product_id.name,
                'reference': self.lot_ids.product_id.name,
                'location_id': self.lot_ids.location_id.id,
                'location_dest_id': self.warehouse_id.ps_inspect_wh_id.id,
                'product_id': self.lot_ids.product_id.id,
                'product_uom': self.lot_ids.uom_id.id,
                'product_uom_qty': self.lot_ids.quantity,
                'date': fields.datetime.now(),
                'quantity_done': self.lot_ids.quantity,
                'move_line_ids': [(0, 0, {
                    'product_id': self.lot_ids.product_id.id,
                    'location_id': self.lot_ids.location_id.id,
                    'location_dest_id': self.warehouse_id.ps_inspect_wh_id.id,
                    'product_uom_id': self.lot_ids.uom_id.id,
                    'lot_id': self.lot_ids.lot_id.id,
                })]
            })
            move_to_check._action_confirm()
            move_to_check._action_done()

            # Move products from the request check location to the original location.
            new_picking_id = self.env['stock.picking'].create({
                'location_id': self.warehouse_id.ps_inspect_wh_id.id,
                'location_dest_id': self.lot_ids.location_id.id,
                'picking_type_id': self.env['stock.warehouse'].search(
                    [('id', '=', self.warehouse_id.id)]).inventory_check_type_id.id,
            })
            self.env['stock.move'].create({
                'picking_type_id': self.env['stock.warehouse'].search(
                    [('id', '=', self.warehouse_id.id)]).inventory_check_type_id.id,
                'picking_id': new_picking_id.id,
                'name': self.lot_ids.product_id.name,
                'location_id': self.warehouse_id.ps_inspect_wh_id.id,
                'location_dest_id': self.lot_ids.location_id.id,
                'product_id': self.lot_ids.product_id.id,
                'product_uom': self.lot_ids.uom_id.id,
                'product_uom_qty': self.lot_ids.quantity,
                'quantity_done': self.lot_ids.quantity,
                'date': fields.datetime.now(),
                'move_line_ids': [(0, 0, {
                    'picking_id': new_picking_id.id,
                    'product_id': self.lot_ids.product_id.id,
                    'location_id': self.warehouse_id.ps_inspect_wh_id.id,
                    'location_dest_id': self.lot_ids.location_id.id,
                    'product_uom_id': self.lot_ids.uom_id.id,
                    'lot_id': self.lot_ids.lot_id.id,
                })]
            })

            new_picking_id.action_confirm()

            self.date = fields.Date.today()
            self.env['stock.quant'].sudo().search([('lot_id', '=', self.lot_ids.lot_id.id),
                                                   ('location_id', '=', self.lot_ids.location_id.id)]).write(
                {'ps_is_request': False})
            return self.write({'state': 'done'})
        else:
            raise UserError(_('Please confirm the existence of the warehouse!'))

    def action_cancel(self):
        # Change state cancelled.
        self.env['stock.quant'].sudo().search([('lot_id', '=', self.lot_ids.lot_id.id),
                                               ('location_id', '=', self.lot_ids.location_id.id)]).write(
            {'ps_is_request': False})
        self.date = fields.Date.today()
        return self.write({'state': 'cancelled'})


class QualityInventoryCheckRequestLine(models.Model):
    _name = 'ps.quality.inventory.check.request.line'
    _description = 'quality inventory check request line'

    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id = fields.Many2one('stock.location', string='Location')
    lot_id = fields.Many2one('stock.production.lot', string='Lot')
    ps_lot_id = fields.Many2one('ps.quality.inventory.check.request', string='Lot Line')
