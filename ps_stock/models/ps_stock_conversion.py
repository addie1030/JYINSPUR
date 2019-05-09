# -*- coding: utf-8 -*-
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class StockProductionConversion(models.Model):
    _name = "ps.stock.production.conversion"
    _description = "ps.stock.production.conversion"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_warehouse(self):
        warehouse = self.env['stock.warehouse'].search([('partner_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse.id

    @api.onchange('warehouse_id')
    def _on_change_location_id(self):
        self.location_id = self.warehouse_id.lot_stock_id

    name = fields.Char(string="Number", copy=False, readonly=True,
                       states={'draft': [('readonly', False)]},
                       required=True, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string=" Main Product", required=True)
    uom_id = fields.Many2one('uom.uom', string="Uom", required=True)
    category_id = fields.Many2one(
        'uom.category', string='Category', ondelete='cascade', related='product_id.product_tmpl_id.uom_id.category_id')

    qty = fields.Float(string="Quantity", required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True,
                                   default=_get_default_warehouse)
    package_id = fields.Many2one('stock.quant.package', string="Package")
    lot_stock_id = fields.Many2one('stock.location',
                                   string='Lot Stock Id', required=1, related='warehouse_id.lot_stock_id')
    location_id = fields.Many2one('stock.location', string="Location", required=True)

    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    lot_id = fields.Many2one('stock.production.lot', string="Lot")
    lot_name = fields.Char(string="Lot Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('converted', 'Converted'),
        ('cancelled', 'Cancelled'),
    ], string="State", default="draft", track_visibility='onchange')

    raw_product_ids = fields.One2many('ps.stock.production.conversion.line', 'conversion_id',
                                      string="Raw Production", domain=[('type', '=', 'raw_product')],
                                      ondelete='cascade')
    by_product_ids = fields.One2many('ps.stock.production.conversion.line', 'conversion_id',
                                     string="By Production", domain=[('type', '=', 'by_product')],
                                     ondelete='cascade')

    converted_count = fields.Integer(string='Converted Count', compute='_compute_converted_count', readonly=True)

    @api.onchange('product_id')
    def onchange_product(self):
        self.uom_id = self.product_id.uom_id.id

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(_("You can't delete no-draft's Order!"))
        return super(StockProductionConversion, self).unlink()

    @api.constrains('qty')
    def check_qty(self):
        if int(self.qty) <= 0:
            raise ValidationError(
                _("The number of main production (%s) cannot be less than or equal to zero.") % (self.product_id.name))
        if self.by_product_ids:
            for line in self.by_product_ids:
                if int(line.qty) <= 0:
                    raise ValidationError(
                        _("The number of by production (%s) cannot be less than or equal to zero.") % (
                            line.product_id.name))
        for line in self.raw_product_ids:
            if int(line.qty) <= 0:
                raise ValidationError(_("The number of raw production (%s) cannot be less than or equal to zero.") % (
                    line.product_id.name))
            if line.product_id.with_context(location=line.location_id.id, lot_id=line.lot_id.id,
                                            package_id=line.package_id.id).qty_available < line.qty:
                raise UserError(_('%s Insufficient stock') % (line.product_id.name))

    def check_raw_product_ids(self, vals, type=None):
        if 'raw_product_ids' in vals:
            if type == 'write':
                if not vals['raw_product_ids'][0][2] and vals['raw_product_ids'][0][0] == 2:
                    raise UserError(_("Must add some raw-production!"))
        else:
            if type == 'create':
                raise UserError(_("Must add some raw-production!"))

    @api.multi
    def write(self, vals):
        self.check_raw_product_ids(vals, type='write')
        return super(StockProductionConversion, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'product.conversion') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('product.conversion') or _('New')

        self.check_raw_product_ids(vals, type='create')
        return super(StockProductionConversion, self).create(vals)

    @api.multi
    def action_confirm(self):
        if self.state == 'draft':
            self.state = 'confirmed'

    @api.multi
    def action_cancel(self):
        if self.state == 'cancelled' or self.state == 'confirmed':
            self.state = 'draft'

    @api.multi
    def action_convert(self):
        if self.state == 'confirmed':

            if self.lot_name:
                self.lot_id = self._converted_lot(self)
            move1 = self.env['stock.move'].create({
                'name': self.name,
                'reference': self.name,
                'location_id': self.env.ref('stock.location_production').id,
                'location_dest_id': self.location_id.id,
                'product_id': self.product_id.id,
                'product_uom': self.uom_id.id,
                'product_uom_qty': self._compute_quantity(self.qty, self.uom_id),
                'price_unit': 0,
                'quantity_done': self._compute_quantity(self.qty, self.uom_id),
                'date': fields.datetime.now(),
                'move_line_ids': [(0, 0, {
                    'product_id': self.product_id.id,
                    'location_id': self.env.ref('stock.location_production').id,
                    'location_dest_id': self.location_id.id,
                    'product_uom_id': self.uom_id.id,
                    'lot_id': self.lot_id.id,
                    'lot_name': self.lot_name,
                    'result_package_id': self.package_id.id,
                })]
            })
            move1._action_confirm()
            move1._action_done()

            if self.raw_product_ids:
                for raw_product_ids in self.raw_product_ids:
                    if raw_product_ids.lot_name:
                        raw_product_ids.lot_id = self._converted_lot(raw_product_ids)
                    move2 = self.env['stock.move'].create({
                        'name': self.name,
                        'reference': self.name,
                        'location_id': raw_product_ids.location_id.id,
                        'location_dest_id': self.env.ref('stock.location_production').id,
                        'product_id': raw_product_ids.product_id.id,
                        'product_uom': raw_product_ids.uom_id.id,
                        'product_uom_qty': self._compute_quantity(raw_product_ids.qty, raw_product_ids.uom_id),
                        'price_unit': 0,
                        'quantity_done': self._compute_quantity(raw_product_ids.qty, raw_product_ids.uom_id),
                        'date': fields.datetime.now(),
                        'move_line_ids': [(0, 0, {
                            'product_id': raw_product_ids.product_id.id,
                            'location_id': raw_product_ids.location_id.id,
                            'location_dest_id': self.env.ref('stock.location_production').id,
                            'product_uom_id': raw_product_ids.uom_id.id,
                            'lot_id': raw_product_ids.lot_id.id,
                            'lot_name': raw_product_ids.lot_name,
                            'package_id': raw_product_ids.package_id.id,
                        })]
                    })
                    move2._action_confirm()
                    move2._action_done()

            if self.by_product_ids:
                for by_product_ids in self.by_product_ids:
                    if by_product_ids.lot_name:
                        by_product_ids.lot_id = self._converted_lot(by_product_ids)
                    move3 = self.env['stock.move'].create({
                        'name': self.name,
                        'reference': self.name,
                        'location_id': self.env.ref('stock.location_production').id,
                        'location_dest_id': by_product_ids.location_id.id,
                        'product_id': by_product_ids.product_id.id,
                        'product_uom': by_product_ids.uom_id.id,
                        'product_uom_qty': self._compute_quantity(by_product_ids.qty, by_product_ids.uom_id),
                        'price_unit': 0,
                        'quantity_done': self._compute_quantity(by_product_ids.qty, by_product_ids.uom_id),
                        'date': fields.datetime.now(),
                        'move_line_ids': [(0, 0, {
                            'product_id': by_product_ids.product_id.id,
                            'location_id': self.env.ref('stock.location_production').id,
                            'location_dest_id': by_product_ids.location_id.id,
                            'product_uom_id': by_product_ids.uom_id.id,
                            'lot_id': by_product_ids.lot_id.id,
                            'lot_name': by_product_ids.lot_name,
                            'result_package_id': by_product_ids.package_id.id,
                        })]
                    })
                    move3._action_confirm()
                    move3._action_done()
            self.date = fields.datetime.now()
            self.state = 'converted'

    @api.multi
    def action_set_draft(self):
        if self.state == 'cancelled':
            self.state = 'draft'

    @api.multi
    def _compute_converted_count(self):
        self.converted_count = self.env['stock.move'].search_count([('reference', '=', self.name)])

    @api.multi
    def action_view_move(self):
        ids = self.env['stock.move'].search([('reference', '=', self.name)]).ids
        if ids:
            return {'type': 'ir.actions.act_window',
                    'name': _('Stock Move'),
                    'view_mode': 'tree',
                    'res_model': 'stock.move',
                    'domain': [('id', 'in', ids)]
                    }
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP'):
        if not self:
            return qty
        self.ensure_one()
        if self.category_id.id != to_unit.category_id.id:
            if self._context.get('raise-exception', True):
                raise UserError(_(
                    'Conversion from Product UoM %s to Default UoM %s is not possible as they both belong to different Category!.') % (
                                    self.name, self.uom_id.name))
            else:
                return qty
        amount = qty / to_unit.factor
        if to_unit:
            amount = amount * to_unit.factor
            if round:
                amount = tools.float_round(amount, precision_rounding=to_unit.rounding, rounding_method=rounding_method)
        return amount

    def _converted_lot(self, line_id):
        lot = self.env['stock.production.lot'].search(
            [('name', '=', line_id.lot_name), ('product_id', '=', line_id.product_id.id)])
        if not lot:
            lot = self.env['stock.production.lot'].create({
                'name': line_id.lot_name,
                'product_id': line_id.product_id.id,
            })
        return lot


class StockProductionConversionLine(models.Model):
    _name = "ps.stock.production.conversion.line"
    _description = "ps.stock.production.conversion.line"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', required=True, string="Product")
    uom_id = fields.Many2one('uom.uom', required=True, string="Uom")
    category_id = fields.Many2one(
        'uom.category', string='Category', required=True, ondelete='cascade', related='uom_id.category_id')
    qty = fields.Float(string="Quantity", required=True)
    location_id = fields.Many2one('stock.location', string="Location")
    lot_stock_id = fields.Many2one('stock.location',
                                   string='Lot Stock Id', required=1, related='conversion_id.warehouse_id.lot_stock_id')
    lot_id = fields.Many2one('stock.production.lot', string="Lot")
    lot_name = fields.Char(string="Lot Name")
    package_id = fields.Many2one('stock.quant.package', string="Package")
    type = fields.Selection([
        ('raw_product', 'Raw Production'),
        ('by_product', 'By Production')
    ], string="Type", default=lambda self: self._context.get('type'))

    conversion_id = fields.Many2one('ps.stock.production.conversion')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('converted', 'Converted'),
        ('cancelled', 'Cancelled'),
    ], string="State", default="draft", related='conversion_id.state')

    date = fields.Datetime(string="Date", default=fields.Datetime.now)

    package_ids = fields.Many2many('stock.quant.package', string="Package Ids")

    @api.onchange('product_id', 'lot_stock_id')
    def onchange_product(self):
        self.uom_id = self.product_id.uom_id.id
        self.location_id = self.lot_stock_id

    @api.onchange('product_id', 'lot_id', 'location_id')
    def _get_package_ids(self):
        domain = []
        if self.product_id:
            domain += [('product_id', '=', self.product_id.id)]
        if self.location_id:
            domain += [('location_id', '=', self.location_id.id)]
        if self.lot_id:
            domain += [('lot_id', '=', self.lot_id.id)]
        res = self.env['stock.quant'].search(domain)
        package_ids = []
        for l in res:
            if l.package_id.id:
                package_ids.append(l.package_id.id)
        if res and domain:
            self.package_ids = [(6, 0, package_ids)]
        else:
            self.package_ids = False
