# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    ps_child_version_id = fields.Many2one('ps.product.template.version', string='Version')  # 子项版本号
    @api.onchange('product_id')
    def _onchange_product_id(self):
        return {
            'domain': {'ps_child_version_id': [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)]},
        }


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _get_plm(self):
        return True if self.env['ir.module.module'].search([('name', '=', 'mrp_plm'), ('state', '=', 'installed')]) else False
    ps_is_default_version = fields.Boolean("Whether The Default Version", default=False)  # 是否默认版本

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """
        查询产品之前是否有默认版本
        :return:
        """
        boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
        for bom in boms:
            if bom.ps_is_default_version:
                self.ps_is_default_version = False
                break
        else:
            self.ps_is_default_version = True

    @api.model
    def create(self, vals):
        if vals.get('ps_is_default_version'):
            boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', vals.get('product_tmpl_id')), ('ps_is_default_version', '=', True)])
            for bom in boms:
                bom.write({'ps_is_default_version': False})
        res = super(MrpBom, self).create(vals)
        if vals.get('version'):
            self.env['ps.product.template.version'].create({
                'name' : vals.get('version'),
                'bom_id' : res.id,
                'product_tmpl_id' : vals.get('product_tmpl_id'),
            })
        return res

    @api.multi
    def write(self, vals):
        if vals.get('ps_is_default_version'):
            boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_tmpl_id.id), ('ps_is_default_version', '=', True)])
            for bom in boms:
                bom.write({'ps_is_default_version': False})
        res = super(MrpBom, self).write(vals)
        if vals.get('version'):
            template_version = self.env['ps.product.template.version'].search([('id','=',self.id)])
            template_version.update({
                'name' : vals.get('version'),
            })
        if vals.get('product_tmpl_id') and self.is_mrp_plm_installed:
            print(self.id)
            template_version = self.env['ps.product.template.version'].search([('id', '=', self.id)])
            template_version.update({
                'product_tmpl_id': vals.get('product_tmpl_id'),
            })
        return res
    
    
class PsProductTemplateVersion(models.Model):
    _name = 'ps.product.template.version'

    bom_id = fields.Many2one('mrp.bom', string='Bom', ondelete='cascade')  # 物料
    name = fields.Char(string='Version Number') #版本号
    product_tmpl_id = fields.Many2one('product.template',string='Product Template', ondelete='cascade') #产品模板

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        
        return self.search([
            ( 'name', operator, name),
            ('product_tmpl_id', '=', self.env.context.get('product_tmpl_id'))
            ]).name_get()
    