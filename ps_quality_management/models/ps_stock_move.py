# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, models, _, fields
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    check_ids = fields.One2many('ps.quality.check.order', 'picking_id', string="Quality Check Order", copy=False)
    quality_check_todo = fields.Boolean('Pending checks', compute='_compute_check')
    quality_check_count = fields.Integer(compute='_compute_quality_check_count')

    def _compute_quality_check_count(self):
        for self in self:
            self.quality_check_count = len(self.check_ids.ids)

    @api.multi
    def _compute_check(self):
        for picking in self:
            todo = False
            fail = False
            for check in picking.check_ids:
                if check.state == 'confirmed' and check.check_result == 'qualified':
                    todo = True
                elif check.state == 'fail':
                    fail = True
                if fail and todo:
                    break
            picking.quality_check_fail = fail
            picking.quality_check_todo = todo

    @api.multi
    def check_quality(self):
        """
        related quality check order
        :return:
        """
        self.ensure_one()
        action = self.env.ref('quality_control.quality_check_action_main').read()[0]
        action['domain'] = [('picking_id', '=', self.id)]
        return action

    @api.multi
    def button_validate(self):
        # Do the check before transferring

        # product_to_check = self.mapped('move_line_ids').mapped('product_id')
        # if self.mapped('check_ids').filtered(lambda x: x.state != 'validated' and x.product_id in product_to_check):
        #     raise UserError(_('the quality checks result is Failed, Unable to do the next step!'))
        for check_order in self.check_ids:
            # if check_order.state != 'validated':
            #     raise UserError(_('the quality checks result is Failed, Unable to do the next step!'))
            if check_order.state != 'validated':
                raise UserError(_('the quality checks result is Failed, Unable to do the next step!'))
            for check in check_order.check_ids:
                if check.type == 'gb' and check.ps_check_result == 'failed':
                    raise UserError(_('the quality checks result is Failed, Unable to do the next step!'))

        res = super(StockPicking, self).button_validate()
        for move in self.move_line_ids_without_package:
            for check in self.check_ids:
                if move.product_id.id == check.product_id.id:
                    if move.lot_id:
                        move.lot_id.ref = check.ref
        return res

    @api.multi
    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.sudo().check_ids.unlink()
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_check_ids(self, point_id):
        if point_id.type == 'gb':
            qty, _, _ = self.env['quality.check']._get_sampling_code(self.product_uom_qty, point_id.check_level.id,
                                                                     point_id.testing_item_id.aql.id,
                                                                     point_id.testing_item_id.strictness)
        else:
            qty = self.product_uom_qty
        return ((0, 0, {
            'picking_id': self.picking_id.id,
            'point_id': point_id.id,
            'ps_inspection_plan_id': point_id.plan_id.id,
            'ps_sampling_plan_id': point_id.sampling_plan_id.id,
            'testing_item_id': point_id.testing_item_id.id,
            'team_id': point_id.team_id.id,
            'ps_partner_id': self.picking_id.partner_id.id,
            # 'lot_id': self.env['stock.move.line'].search([('move_id', '=', self.id)]).lot_id.id,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'ps_location_id': self.location_id.id,
            'ps_warehouse_id': self._search_warehouse_id(),
            'ps_check_quantity': self.product_uom_qty,
            'company_id': self.picking_id.company_id.id,
            'check_level': point_id.check_level.id,
            'type': point_id.type,
            'ps_failed_qty': qty,
        }))

    # fixed me: the method maybe not used any more
    def _search_warehouse_id(self):
        warehouse_id = self.env.ref('stock.warehouse0')
        if self.location_dest_id.location_id:
            warehouse_id = self.env['stock.warehouse'].search(
                [('lot_stock_id', '=', self.location_dest_id.location_id.id)])
        return warehouse_id.id

    def _create_quality_checks(self):
        """
        create Quality check order when find the quality point
        :return:
        """
        for record in self:
            check_line_id = []
            now_date = datetime.datetime.now() + datetime.timedelta(hours=8)
            point_ids = self.env['quality.point'].sudo().search([
                ('plan_id.state', '=', 'confirmed'),
                ('plan_id.validate_from', '<=', now_date),
                ('plan_id.validate_to', '>=', now_date),
                ('picking_type_id', '=', record.picking_type_id.id),
                ('product_id', '=', record.product_id.id)])
            if not point_ids:
                point_ids = self.env['quality.point'].sudo().search([
                    ('plan_id.state', '=', 'confirmed'),
                    ('plan_id.validate_from', '<=', now_date),
                    ('plan_id.validate_to', '>=', now_date),
                    ('picking_type_id', '=', record.picking_type_id.id),
                    '|', ('product_id', '=', record.product_id.id),
                    ('product_tmpl_id', '=', record.product_id.product_tmpl_id.id)])
            for point_id in point_ids:
                check_line_id.append(self._get_check_ids(point_id))
            if check_line_id:
                type_id = record.picking_type_id
                is_have = record.picking_id.check_ids.filtered(lambda x: x.state == 'validated')

                if not is_have:
                    self.env['ps.quality.check.order'].create({
                        'ps_inspect_plan_id': point_id.plan_id.id,
                        'type_id': type_id.id,
                        'document': record.picking_id._name + "," + str(record.picking_id.id),
                        'check_ids': check_line_id,
                        'picking_id': record.picking_id.id,
                        'partner_id': record.picking_id.partner_id.id,
                        'warehouse_id': record.picking_type_id.warehouse_id.id,
                        'location_id': record.location_id.id,
                        'product_id': record.product_id.id,
                        'product_tmpl_id': record.product_id.product_tmpl_id.id,
                        'check_quantity': record.product_uom_qty,
                        'state': 'confirmed',
                    })


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.onchange('qty_done')
    def onchange_qty_done(self):
        if self._origin.read(['qty_done']) and self.move_id.picking_id.check_ids:
            origin_qty = self._origin.read(['qty_done'])[0]['qty_done']
            if origin_qty != 0 and self.qty_done > origin_qty:
                self.qty_done = origin_qty
                raise UserError(_("The number of modifications should not be greater than the current value"))
#
# class Picking(models.Model):
#     _inherit = "stock.picking"
#     @api.multi
#     def button_validate(self):
#         if self.check_ids:
#             for check_id in self.check_ids:
#                 if check_id.check_result == 'failed':
#                     raise UserError(_("The quality check not pass, you can receive these product!"))
#         super(Picking,self).button_validate()
