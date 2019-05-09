# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
import time


class QualityCheckOrder(models.Model):
    _name = "ps.quality.check.order"
    _description = "Quality Check Order"

    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    ref = fields.Char(string="Ref")
    name = fields.Char(string="Name", default=lambda self: _('New'), copy=False)
    type_id = fields.Many2one('stock.picking.type', string="Type")
    description = fields.Char(string="Description")
    document = fields.Reference(selection=[('stock.picking', 'Stock Picking')], string="Document")
    product_ids = fields.Many2many('product.template', string="Products")

    @api.onchange('document')
    def onchange_document(self):
        if self.document:
            self.partner_id = self.document.partner_id.id or False
            self.warehouse_id = self.type_id.warehouse_id.id
            self.location_id = self.document.location_id.id
            self.product_ids = [x.product_id.product_tmpl_id.id for x in self.document.move_lines]

    picking_id = fields.Many2one('stock.picking', string="Picking")
    check_ids = fields.One2many('quality.check', 'ps_quality_id', string="Quality Check")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('validated', 'Validated'),
        ('cancel', 'Cancel'),
    ], string="States", default='draft', copy=False)
    point_id = fields.Many2one('quality.point', string="Quality Point")

    partner_id = fields.Many2one('res.partner', string="Partner")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    lot_stock_id = fields.Many2one('stock.location', string='Location',
                                   related='warehouse_id.lot_stock_id')  # 库位
    location_id = fields.Many2one('stock.location', string="Location")
    check_result = fields.Selection(
        [('qualified', 'Qualified'), ('failed', 'Failed')],
        string="Check Result", compute="_compute_check_result")

    disposal_count = fields.Integer(string='Disposal', compute='_compute_disposal_ids')

    check_quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="Check Quantity")
    qty_ok = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="Qualified Qty",
                          compute="_compute_qty_ng")
    qty_ng = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string="UnQualified Qty",
                          compute="_compute_qty_ng")
    quality_state = fields.Char()
    product_id = fields.Many2one('product.product', 'Product')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    lot_id = fields.Many2one("stock.production.lot", string="Lot")
    lot_name = fields.Char(string="Lot")
    ps_picking_code = fields.Selection(related='type_id.code')
    ps_decision_ids = fields.One2many('ps.quality.check.decision', 'check_id', string="Check Decision")
    ps_inspect_plan_id = fields.Many2one('ps.quality.inspection.plan', string='Inspect Plan', )
    picking_count = fields.Integer(string='Picking Count', compute='_compute_picking_count')

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            self.product_id = self.product_tmpl_id.product_variant_ids[0]
            if self.document:
                self.check_quantity = sum(self.document.move_lines.filtered(
                    lambda x: x.product_id.product_tmpl_id == self.product_tmpl_id).mapped('product_uom_qty'))

    @api.onchange('ps_inspect_plan_id')
    def _onchange_inspect_plan(self):
        if self.ps_inspect_plan_id:
            plan_lines = []
            qty = sum(self.document.move_lines.filtered(
                lambda x: x.product_id.product_tmpl_id == self.product_tmpl_id).mapped('product_uom_qty'))

            for plan in self.ps_inspect_plan_id.inspection_plan_testing_item_ids:
                if not plan.type == 'all':
                    qty, _, _ = self.env['quality.check']._get_sampling_code(qty,
                                                                             plan.check_level.id,
                                                                             plan.testing_item_id.aql.id,
                                                                             plan.testing_item_id.strictness)

                values = (0, 0, {
                    'ps_inspection_plan_id': self.ps_inspect_plan_id.id,
                    'product_id': plan.product_id.id,
                    'product_tmpl_id': plan.product_tmpl_id.id,
                    'testing_item_id': plan.testing_item_id.id,
                    'check_level': plan.check_level,
                    'ps_failed_qty': qty,
                    'ps_check_quantity': qty,
                    'type': plan.type
                })
                plan_lines.append(values)
            self.check_ids = plan_lines

    @api.depends('check_ids')
    def _compute_qty_ng(self):
        for line in self:

            qty_ng = line.check_quantity
            if line.check_ids and not line.check_ids.filtered(
                    lambda x: x.ps_check_result == 'failed' and x.type == 'gb'):
                qty_ng = sum(line.check_ids.filtered(lambda x: x.ps_check_result == 'failed').mapped('ps_qty_ng'))
            line.qty_ng = qty_ng if qty_ng <= line.check_quantity else line.check_quantity
            line.qty_ok = line.check_quantity - line.qty_ng if line.check_quantity >= line.qty_ng else 0.0

    @api.depends('check_ids')
    def _compute_disposal_ids(self):
        for check_order in self:
            disposals = self.env['ps.quality.defect.disposal'].search(
                [('quality_check_id', '=', check_order.id)])
            check_order.disposal_count = len(disposals)

    @api.multi
    def action_view_defect_disposal(self):
        '''
        This function returns an action that display existing defect disposal
        of given quality check order ids. It can either be a in a list or in a form
        view, if there is only one quality defect disposal to show.
        '''
        action = self.env.ref('ps_quality_management.action_disposal_all').read()[0]

        disposals = self.env['ps.quality.defect.disposal'].search(
            [('quality_check_id', '=', self.id)])
        if len(disposals) > 1:
            action['domain'] = [('id', 'in', disposals.ids)]
        elif disposals:
            action['views'] = [(self.env.ref('ps_quality_management.ps_quality_defect_disposal_form_view').id, 'form')]
            action['res_id'] = disposals.id
        return action

    def create_product_lot(self):
        ref_lot = ""
        if self.lot_name:
            ref_lot = self.lot_name
        if self.lot_id:
            ref_lot = self.lot_id.name
        lot_name = ref_lot + "-" + str(int(time.time()))[0:4]
        lot_id = self.env['stock.production.lot'].create(
            {'name': lot_name, 'product_id': self.product_id.id}
        )
        return lot_id

    def create_defect_disposal(self, type_id, check_decision, lot_id):

        line_ids = []
        line_ids.append((0, 0, {
            'product_id': self.product_id.id,
            'partner_id': self.partner_id.id,
            'uom_id': self.product_id.uom_id.id,
            'decision_id': check_decision.decision_id.id,
            'qty_ng': check_decision.quantity,
            'qty': 0,
            'reject': False,
            'discount': False,
            'amount_discount': 0,
            'currency': self.env.user.company_id.currency_id.id,
        }))
        defect_disposal = self.env['ps.quality.defect.disposal'].create({
            'type_id': type_id.id,
            'lot_id': lot_id,
            'document': self.document._name + "," + str(self.document.id),
            'quality_defect_disposal_line_ids': line_ids,
            'warehouse_id': self.warehouse_id.id,
            'quality_check_id': self.id,
            'state': 'confirmed',
        })

        self.env['quality.alert'].create({
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_id': self.product_id.id,
            'partner_id': self.partner_id.id,
            'lot_id': lot_id,
            'defect_disposal_id': defect_disposal.id,
            'picking_id': self.picking_id.id,

        })

    # create and confirm stock move
    def create_stock_move(self, check_decision, lot_id):
        location_id = self.env['stock.warehouse'].search(
            [('id', '=', self.warehouse_id.id), ('active', '=', True)]).ps_pending_wh_id
        warehouse_id = self.env["stock.warehouse"].search(
            [("id", '=', self.picking_id.picking_type_id.warehouse_id.id)])
        # picking_type_id = self.env['stock.picking.type'].search([('id', '=', warehouse_id.id)])

        picking_id = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': warehouse_id.bad_return_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_id.id,
        })

        values = {
            'product_id': self.product_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'lot_id': lot_id,
            'picking_id': picking_id.id,
        }

        self.env['stock.move'].create({
            'picking_id': picking_id.id,
            'name': self.name,
            'reference': self.name,
            'location_id': self.location_id.id,
            'location_dest_id': location_id.id,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': check_decision.quantity,
            'price_unit': 0,
            'quantity_done': check_decision.quantity,
            'date': fields.datetime.now(),
            'move_line_ids': [(0, 0, values)]
        })
        picking_id.action_confirm()
        picking_id.button_validate()
        # move._action_confirm()
        # move._action_done()

    @api.depends('check_ids')
    def _compute_check_result(self):
        for self in self:
            # if self.ps_decision_ids:
            if self.check_ids.filtered(lambda x: x.ps_check_result == 'failed'):
                self.check_result = 'failed'
            else:
                self.check_result = 'qualified'

    def action_approve(self):
        for self in self:
            self.state = 'confirmed'

    def action_validate(self):
        for self in self:
            stock_move = self.env['stock.move'].search([('picking_id', '=', self.document.id),
                                                        ('product_id', '=', self.product_id.id)])
            stock_move.quantity_done = stock_move.product_uom_qty
            # update stock move quantity done
            stock_move_line = self.env['stock.move.line'].search([('move_id', '=', stock_move.id)])
            if self.lot_name:
                stock_move_line.lot_name = self.lot_name
            else:
                stock_move_line.lot_id = self.lot_id.id
            for check_decision in self.ps_decision_ids:
                if check_decision.disposal and check_decision.decision_id.accept:
                    type_id = self.type_id
                    # create quality defect disposal
                    lot_id = None
                    if self.user_has_groups('stock.group_production_lot'):
                        lot_id = self.create_product_lot().id
                    self.create_defect_disposal(type_id, check_decision, lot_id=lot_id)
                    self.create_stock_move(check_decision, lot_id=lot_id)

            # 更新stock picking 完成数量
            check_gb = False
            for check_id in self.check_ids:
                if check_id.type == 'gb':
                    check_gb = True
            if check_gb:
                for decision in self.ps_decision_ids:
                    if decision.status == 'failed' and decision.quantity > 0:
                        stock_move.quantity_done = 0

            else:
                for decision in self.ps_decision_ids:
                    # if decision.decision_id.accept:
                    stock_move.quantity_done -= decision.quantity

        self.state = 'validated'

    def action_cancel(self):
        for self in self:
            self.state = 'cancel'

    def action_draft(self):
        for self in self:
            self.state = 'draft'

    def unlink(self):
        for line in self:
            if line.state in ["confirmed", 'validated']:
                raise UserError(_("you can not delete this order when order state is confirmed"))
        return super(QualityCheckOrder, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.quality.check.order') or _('New')
        return super(QualityCheckOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(QualityCheckOrder, self).write(vals)
        self.check_ng_qty()

        if self.user_has_groups('stock.group_production_lot'):
            if self.lot_name:
                if self.env['stock.production.lot'].search([('name', '=', self.lot_name)]):
                    raise UserError(_("Your lot %s is exited. " % self.lot_name))
            if self.product_id.tracking != 'none':
                if self.ps_picking_code == 'incoming' and not self.lot_name:
                    raise UserError(
                        _('You need to supply a Lot/Serial number for product %s.') % self.product_id.display_name)
                if self.ps_picking_code != 'incoming' and not self.lot_id:
                    raise UserError(
                        _('You need to supply a Lot/Serial number for product %s.') % self.product_id.display_name)
        return res

    def check_ng_qty(self):
        ps_qty_ng = sum(self.ps_decision_ids.filtered(lambda x: x.status == 'failed').mapped('quantity'))
        if self.qty_ng > 0 and ps_qty_ng > self.qty_ng:
            raise UserError(_("Total detail quantity can not bigger than quality ng quantity"))
        if not self.ps_decision_ids and self.qty_ng > 0:
            raise UserError(_("Please input quantity check decision for the quality failed product"))

    @api.onchange('ps_decision_ids')
    def onchange_ps_decision_ids(self):
        self.check_ng_qty()

    # @api.multi
    # def action_view_check_order_stock_picking(self):
    #     ids = self.env['stock.picking'].sudo().search(
    #         ['|', ('id', '=', self.document.id), ('origin', '=', self.document.name)]).ids
    #     if ids:
    #         return {'type': 'ir.actions.act_window',
    #                 'name': _('Stock Picking'),
    #                 'view_mode': 'tree,form',
    #                 'res_model': 'stock.picking',
    #                 'domain': [('id', 'in', ids)]
    #                 }
    #     return {'type': 'ir.actions.act_window_close'}

    def _compute_picking_count(self):
        self.picking_count = self.env['stock.picking'].sudo().search_count(
            ['|', ('id', '=', self.document.id), ('origin', '=', self.document.name)])
