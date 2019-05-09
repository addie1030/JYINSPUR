# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class PsAssetState(models.Model):
    _name = 'ps.asset.state'
    _description = 'Asset State'

    name = fields.Char(string='Name', requird=True) #状态名称
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)   #公司
    describe = fields.Char(string='Describe')    #描述
    is_depreciation = fields.Boolean(string='Depreciation', default=False)  #是否计提折旧
    active = fields.Boolean(default=True)   #是否有效

    @api.multi
    def unlink(self):
        for r in self:
            if self.env['account.asset.category'].search([('ps_asset_state_id', '=', r.id)]):
                raise ValidationError(_('Asset State ') + r.name + _(' is using, can not delete.'))
        return super(PsAssetState, self).unlink()

