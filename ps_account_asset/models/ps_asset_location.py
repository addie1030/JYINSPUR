# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning

class PsAssetLocation(models.Model):
    _name = 'ps.asset.location'
    _description = 'Asset Location'

    name = fields.Char(string='Name', requird=True) # 位置名称
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)   # 公司
    position = fields.Char(string='Position')    # 存放位置
    address = fields.Char(string='Address')  # 详细地址

    @api.multi
    def unlink(self):
        for record in self:
            rec = self.env['account.asset.asset'].search([('ps_location_id', '=', record.id)])
            if rec:
                raise ValidationError(_('This asset location has been used by the asset ') + rec.name)
        return super(PsAssetLocation, self).unlink()



