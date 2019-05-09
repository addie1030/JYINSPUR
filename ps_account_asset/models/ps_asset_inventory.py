# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class PsAssetInventory(models.Model):
    _name = 'ps.asset.inventory'
    _description = 'Asset Inventory'

    name = fields.Char(string='Document No.', default=lambda self: _('New'), requird=True)     #单据编号
    date = fields.Date(string='Document Date', default=fields.Date.context_today, requird=True)     #单据日期
    inventory_date = fields.Date(string='Inventory Date', default=fields.Date.context_today, requird=True)     # 变动日期
    user_id = fields.Many2one('res.users', default=lambda self: self._uid, string='Inventory Person')  #盘点人
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)   #公司
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
        ], 'Status', default='draft', required=True) #状态
    notes = fields.Char(string='Notes')     # 备注
    line_ids = fields.One2many('ps.asset.inventory.line', 'inventory_id', string='Inventory Line') #盘点明细

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.asset.inventory') or _('New')
        return super(PsAssetInventory, self).create(vals)


    @api.multi
    def refresh_data(self):
        self.ensure_one()

        if self.line_ids:
            self.line_ids.unlink()

        item_ids = self.env['account.asset.asset'].search([('active', '=', '1'),('value_residual', '>', 0),('state','!=','close')])

        item_data = []

        for item in item_ids:
            item_data.append(
                {'asset_id' : item.id,
                'asset_code' : item.code,
                'category_id' : item.category_id,
                'barcode' : item.ps_asset_barcode,
                'count_qty' : item.ps_asset_quantity,
                'inventory_qty' : 0,
                'difference_qty' :item.ps_asset_quantity,
                'real_location_id' :item.ps_location_id,
                'location_id':item.ps_location_id,
                'notes' : ''}
            )
        self.line_ids = item_data
        return True


    @api.multi
    def validate(self):
        self.write({'state': 'confirmed'})
        for r in self.line_ids:
            r.state = 'confirmed'
            if r.count_qty != r.inventory_qty:
                r.asset_id.write({'ps_asset_quantity': r.inventory_qty})
            if r.location_id != r.real_location_id:
                r.asset_id.write({'ps_location_id': r.real_location_id.id})


    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})
        for r in self.line_ids:
            r.state = 'draft'


    @api.multi
    def unlink(self):
        for r in self:
            if r.state == 'confirmed':
                raise ValidationError(_('Asset Inventory ') + r.name + _(' is confirmed, can not delete.'))
        return super(PsAssetInventory, self).unlink()



class PsAssetInventoryLine(models.Model):
    _name = 'ps.asset.inventory.line'
    _description = 'Asset Inventory Line'

    inventory_id = fields.Many2one('ps.asset.inventory', string='Inventory', requird=True) #盘点ID
    asset_id = fields.Many2one('account.asset.asset', string='Asset', requird=True) #资产ID
    asset_code = fields.Char(string='Asset Code', related='asset_id.code') #资产编号
    category_id = fields.Many2one('account.asset.category', string='Asset Category', related='asset_id.category_id') #资产类别
    barcode = fields.Char(string='Asset Barcode', related='asset_id.ps_asset_barcode') #资产条码
    count_qty = fields.Integer(string='Count Quantity', related='asset_id.ps_asset_quantity', requird=True) #账面数量
    inventory_qty = fields.Integer(string='Inventory Quantity', requird=True) #盘点数量
    difference_qty = fields.Integer(string='Difference Quantity', compute='_compute_diff_qty', requird=True) #差异数量
    real_location_id = fields.Many2one('ps.asset.location', string='Inventory Location') #盘点位置
    location_id = fields.Many2one('ps.asset.location', string='Count Location', related='asset_id.ps_location_id') #账面位置
    notes = fields.Char(string='Notes')  # 备注
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], 'Status', default='draft', required=True)  # 状态


    @api.depends('count_qty', 'inventory_qty')
    def _compute_diff_qty(self):
        for r in self:
            r.difference_qty = r.count_qty - r.inventory_qty