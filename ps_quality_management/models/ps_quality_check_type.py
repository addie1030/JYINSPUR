# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class QualityCheckType(models.Model):
    _name = "ps.quality.check.type"
    _description = "ps quality check type"

    code_id = fields.Many2one('ir.sequence', string='Coding',readonly=True, translate=True)
    name = fields.Char(required=True, string='Name', translate=True)
    description = fields.Char(required=True, string='Description', translate=True)
    operation_type = fields.Many2one('stock.picking.type', string='Operation Type', required=True)

    @api.model
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new check type"""
        code = self.env['stock.picking.type'].search([('id', '=', vals['operation_type'])]).code
        if code:
            prefix = 'QCT/' + code.upper()
        else:
            prefix = 'QCT/'
        seq_name = vals['name']
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            'prefix': prefix,
            'padding': 4,
            'number_increment': 1,
            'use_date_range': True,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)
        return seq

    @api.model
    def create(self, vals):
        if not vals.get('code_id'):
            vals.update({'code_id': self.sudo()._create_sequence(vals).id})
        quality_type = super(QualityCheckType, self).create(vals)
        return quality_type
