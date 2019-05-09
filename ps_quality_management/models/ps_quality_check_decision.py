# -*- coding:utf-8 -*-
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class QualityCheckDecision(models.Model):
    _name = "ps.quality.check.decision"
    _description = "ps quality check decision"

    status = fields.Selection(string='Status', required=True, selection=[('qualified', 'Qualified'),
                                                                         ('failed', 'Failed '),
                                                                         ('hold', 'Hold'),
                                                                         ], default='failed')
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
    decision_id = fields.Many2one('ps.quality.decision', string='Decision', required=True)
    description = fields.Char(string='Description')
    disposal = fields.Boolean(string='Disposal')
    check_id = fields.Many2one('ps.quality.check.order', string='Check')
    accept = fields.Boolean(string='Accept', related="decision_id.accept")
    is_bad = fields.Boolean(string="Is bad")

    @api.onchange('disposal')
    def onchange_decision(self):
        if self.disposal:
            self.decision_id = self.env.ref('ps_quality_management.ps_quality_decision_receipt_is_bad').id
        else:
            self.decision_id = self.env.ref('ps_quality_management.ps_quality_decision_rejection').id


class QualityDecision(models.Model):
    _name = 'ps.quality.decision'
    _description = 'ps quality decision'
    _rec_name = 'decision'

    type_id = fields.Many2many('stock.picking.type', string='Type', required=True)
    decision = fields.Char(string='Decision', required=True, translate=True)
    accept = fields.Boolean(string='Accept', required=True)
