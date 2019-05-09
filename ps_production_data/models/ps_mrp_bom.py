# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

from itertools import groupby

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    ps_attrition_rate = fields.Float(string='Attrition Rate%', default=0) #损耗率%
    ps_is_quantitative = fields.Boolean(string='Quantitative', default=False) #是否定量

    @api.constrains('ps_attrition_rate')
    def _check_ps_attrition_rate(self):
        for line in self:
            if line.ps_attrition_rate >= 100 or (line.ps_attrition_rate < 0):
                raise ValueError(_("Attrition Rate more than 0 less than 100")) #损耗率大于0小于100


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _get_plm(self):
        return True if self.env['ir.module.module'].search([('name', '=', 'mrp_plm'), ('state', '=', 'installed')]) else False
    ps_approval_status = fields.Selection([
        ('unaudited', 'Unaudited'),  # 未审批
        ('approved', 'Approved')],  # 审批通过
        string='Approval Status', default='unaudited')  # 审批状态
    ps_approver = fields.Many2one('res.users', string='Approver', default=lambda self: self.env.user)  # 审批人
    ps_approval_date = fields.Date(string='Approval Date', default=fields.Date.context_today)  # 审批日期
    ps_bom_needs_approval = fields.Boolean(string="BOM needs approval", default=False)  # 是否需要审批
    is_mrp_plm_installed = fields.Boolean(string="PLM Installed State", default=_get_plm)  # PLM模块是否已安装


    @api.model
    def create(self, vals):
        res = super(MrpBom, self).create(vals)
        if vals.get('product_tmpl_id'):
            bom_lines = self.env['mrp.bom.line'].search([('bom_id','=',res.id)])
            if bom_lines:
                for item in bom_lines:
                    if item.product_id:
                        product = self.env['product.template'].search([('id', '=', item.product_id.id)])
                        product.write({"ps_bom_id": res.id, "ps_product_tmpl_id": res.product_tmpl_id.id})
        return res

    @api.multi
    def write(self, vals):
        res = super(MrpBom, self).write(vals)
        if vals.get('bom_line_ids'):
            bom_lines = vals.get('bom_line_ids')
            if bom_lines:
                for item in bom_lines:
                    if item[2]:
                        product = self.env['product.template'].search([('id', '=', item[2].get('product_id'))])
                        product.write({"ps_bom_id": self.id, "ps_product_tmpl_id": self.product_tmpl_id.id})
        return res
    
    def approval(self):
        self.write({'ps_approval_status' :'approved'})

    @api.model
    def search_view_id(self, id, version, child_id):
        form_view_id = self.env.ref('ps_production_data.ps_mrp_bom_form_view').id
        sql = """select * from ps_bom_tree where id = %s""" % (id)
        self.env.cr.execute(sql)
        line = self.env.cr.fetchone()
        product_id = line[1]
        product_tmpl_id = self.env['product.product'].search([('id', '=', product_id)]).product_tmpl_id
        if version:
            line = self.search([('product_tmpl_id', '=', product_tmpl_id.id), ('id', '=', child_id), ('version', '=', version)])
        else:
            line = self.search([('product_tmpl_id', '=', product_tmpl_id.id), ('id', '=', child_id)])
        if line:
            res_id = line.id
            return form_view_id, res_id
        else:
            return False
        
