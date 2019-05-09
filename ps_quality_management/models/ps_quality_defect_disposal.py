# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QualityDefectDisposal(models.Model):
    _name = "ps.quality.defect.disposal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = """Disposal of defect quality 
    """

    name = fields.Char(string="Name", required=True, default=lambda self: _('New'))
    type_id = fields.Many2one('stock.picking.type', string="Type")
    document = fields.Reference(selection=[('stock.picking', 'Stock Picking'),
                                           ], string="Document")
    comments = fields.Char(string="Comment")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    lot_id = fields.Many2one("stock.production.lot", string="Lot")
    quality_defect_disposal_line_ids = fields.One2many("ps.quality.defect.disposal.line", "quality_defect_disposal_id",
                                                       string="Quality Defect Disposal Line")
    state = fields.Selection([
        ("draft", 'Draft'),
        ("confirmed", 'Confirmed'),
        ("validated", 'Validated'),
        ("cancel", 'Cancel'),
    ], default="draft", string="State")
    quality_check_id = fields.Many2one("ps.quality.check.order", string='Quality Check Order')
    picking_count = fields.Integer(string='Picking Count', compute='_compute_picking_count')

    def action_approve(self):
        return self.write({'state': 'confirmed'})

    def _stock_move(self, type=None, qty=None):

        picking_id = self.env["stock.picking"].search([('id', '=', self.document.id)])
        warehouse_id = self.env["stock.warehouse"].search(
            [("id", '=', picking_id.picking_type_id.warehouse_id.id)])

        vals = {}
        location_id = None
        location_dest_id = None
        ps_pending_wh_id = self.env['stock.warehouse'].search(
            [('id', '=', self.warehouse_id.id), ('active', '=', True)]).ps_pending_wh_id
        if type == 'out':
            vals.update({'picking_type_id': self.document.picking_type_id.return_picking_type_id.id, })
            location_id = ps_pending_wh_id.id,
            location_dest_id = picking_id.location_id.id,
        else:
            location_id = ps_pending_wh_id.id,
            location_dest_id = picking_id.location_dest_id.id,
            vals.update({'picking_type_id': warehouse_id.bad_return_type_id.id, })

        vals.update({
            'partner_id': self.quality_defect_disposal_line_ids[0].partner_id.id,
            'origin': self.document.name,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        })
        new_picking_id = self.env['stock.picking'].create(vals)
        move_vals = {
            'name': self.name,
            'picking_id': new_picking_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'product_id': self.quality_defect_disposal_line_ids.product_id.id,
            'product_uom': self.quality_defect_disposal_line_ids.uom_id.id,
            'product_uom_qty': qty,
            'quantity_done': qty,
            'date': fields.datetime.now(),
            'move_line_ids': [(0, 0, {
                'picking_id': new_picking_id.id,
                'product_id': self.quality_defect_disposal_line_ids.product_id.id,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'product_uom_id': self.quality_defect_disposal_line_ids.uom_id.id,
                'lot_id': self.lot_id.id,
            })]
        }
        self.env['stock.move'].create(move_vals)
        new_picking_id.action_confirm()
        # new_picking_id.button_validate()

    def action_validated(self):
        """
          # 当不良处置接受为完全时，分两种情况：
        # 1、接收部分，剩余默认退货
        # 1、退货部分，剩余默认接受
        :return:
        """
        decision_obj = self.quality_defect_disposal_line_ids.decision_id
        qty = 0
        if decision_obj.accept:
            # update stock move quantity_done
            picking_id = self.env["stock.picking"].search([('id', '=', self.document.id)])
            qty_in = self.quality_defect_disposal_line_ids.qty
            if qty_in > 0:
                self._stock_move(qty=qty_in)
            if self.quality_defect_disposal_line_ids.qty_ng > self.quality_defect_disposal_line_ids.qty:
                qty_out = self.quality_defect_disposal_line_ids.qty_ng - self.quality_defect_disposal_line_ids.qty
                self._stock_move(type='out', qty=qty_out)

        if not decision_obj.accept:
            # update stock
            qty_out = self.quality_defect_disposal_line_ids.qty
            if qty_out > 0:
                self._stock_move(type='out', qty=qty_out)
            if self.quality_defect_disposal_line_ids.qty_ng > self.quality_defect_disposal_line_ids.qty:
                qty_in = self.quality_defect_disposal_line_ids.qty_ng - self.quality_defect_disposal_line_ids.qty
                self._stock_move(qty=qty_in)

        return self.write({'state': 'validated'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_draft(self):
        return self.write({'state': 'draft'})

    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("Don't delete contracts."))
        return super(QualityDefectDisposal, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.quality.defect.disposal') or '/'
        return super(QualityDefectDisposal, self).create(vals)

    @api.multi
    def action_view_stock_move(self):
        ids = self.env['stock.picking'].sudo().search(
            [('origin', '=', self.document.name)]).ids
        if ids:
            return {'type': 'ir.actions.act_window',
                    'name': _('Stock Picking'),
                    'view_mode': 'tree,form',
                    'res_model': 'stock.picking',
                    'domain': [('id', 'in', ids)]
                    }
        return {'type': 'ir.actions.act_window_close'}

    def _compute_picking_count(self):
        self.picking_count = self.env['stock.picking'].sudo().search_count(
            [('origin', '=', self.document.name)])


class QualityDefectDisposalLine(models.Model):
    _name = "ps.quality.defect.disposal.line"
    _description = """Defective disposal details
    """

    product_id = fields.Many2one("product.product", string="Product")
    partner_id = fields.Many2one("res.partner", string="Partner")
    # workshop_id = fields.Many2one("mrp.workcenter", string="Work Shop")
    # operation_id = fields.Many2one("mrp.routing.workcenter", string="Operation")
    uom_id = fields.Many2one("uom.uom", string="Uom")
    decision_check_id = fields.Many2one("ps.quality.check.decision", string="Decision")
    qty_ng = fields.Float(string="check bad number")
    decision_id = fields.Many2one("ps.quality.decision", string="Disposal")
    qty = fields.Float(string="bad number")
    quality_defect_disposal_id = fields.Many2one('ps.quality.defect.disposal', string="Quality Defect Disposal")

    @api.constrains('qty')
    def _qty_limit(self):
        if self.qty > self.qty_ng:
            raise UserError(_("qty can't greater than qty_ng"))
        if self.qty < 0:
            raise UserError(_("qty can't less than qty_ng"))


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    defect_disposal_id = fields.Many2one('ps.quality.defect.disposal', string="Defect Disposal")
