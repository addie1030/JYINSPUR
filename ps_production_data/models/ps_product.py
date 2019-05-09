# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ps_production_uom = fields.Many2one('uom.uom', string='Production unit of measurement', default=lambda self: self._get_default_uom_id(), required=True)  # 生产计量单位
    ps_is_purchase = fields.Boolean("Purchasing", require=True, default=True)  # 采购
    ps_is_homemade = fields.Boolean("Homemade", require=True, default=False)  # 自制
    ps_is_outsource = fields.Boolean("Outsourcing", require=True, default=False)  # 委外
    ps_ratio_purchase = fields.Float(string='Purchasing') # 采购
    ps_ratio_homemade = fields.Float(string='Homemade')  # 自制
    ps_ratio_outsource = fields.Float(string='Outsourcing')  # 委外
    ps_is_mps = fields.Boolean("Whether to participate in MPS operations", require=True, default=False)  # 是否参与MPS运算
    ps_is_limit = fields.Boolean("Whether to limit control", require=True, default=False)  # 是否限额控制
    ps_rejection_rate = fields.Float(string='Rejection rate%')  # 废品率%
    ps_bom_id = fields.Many2one('mrp.bom', 'Parent Id', index=True, ondelete='cascade')
    ps_product_tmpl_id = fields.Many2one('product.template', 'Parent Id', index=True, ondelete='cascade')

    @api.multi
    @api.constrains('ps_is_purchase', 'ps_is_homemade', 'ps_is_outsource', 'ps_ratio_purchase', 'ps_ratio_homemade', 'ps_ratio_outsource', 'ps_rejection_rate')
    def check_data(self):
        for item in self:
            if (item.ps_is_purchase and item.ps_ratio_purchase < 0) or (item.ps_is_homemade and item.ps_ratio_homemade < 0) or (item.ps_is_outsource and item.ps_ratio_outsource < 0):
                raise ValidationError(_('The ratio of purchasing, homemade and Outsourcing cannot be negative.')) # 采购，自制和委外比例不能为负数
            if item.ps_rejection_rate < 0 or item.ps_rejection_rate >= 100:
                raise ValidationError(_('Rejection rate must be less than 100 and cannot be negative')) # 废品率必须小于100并且不能为负数

    @api.onchange('uom_id')
    def ps_onchange_uom_id(self):
        if self.uom_id:
            self.ps_production_uom = self.uom_id.id


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('uom_id')
    def ps_onchange_uom_id(self):
        if self.uom_id:
            self.ps_production_uom = self.uom_id.id