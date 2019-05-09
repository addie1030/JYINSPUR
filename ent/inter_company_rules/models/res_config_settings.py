# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rule_type = fields.Selection([('so_and_po', 'Synchronize Sales & Purchase Orders'),
        ('invoice_and_refund', 'Synchronize Invoices & Bills')],
         help='Select the type to setup inter company rules in selected company.')
    applicable_on = fields.Selection([('sale', 'Sale Order'), ('purchase', 'Purchase Order'),
        ('sale_purchase', 'Sale and Purchase Order')])
    auto_validation = fields.Selection([('draft', 'draft'), ('validated', 'validated')])
    rules_company_id = fields.Many2one('res.company', string='Select Company',
        help='Select company to setup Inter company rules.', default=lambda self: self.env.user.company_id, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse For Purchase Orders',
        help='Default value to set on Purchase Orders that will be created based on Sales Orders made to this company.')

    @api.onchange('rule_type')
    def onchange_rule_type(self):
        if self.rule_type == 'invoice_and_refund':
            self.auto_validation = False
            self.warehouse_id = False
            self.applicable_on = False

    @api.onchange('rules_company_id')
    def onchange_rules_company_id(self):
        if self.rules_company_id:
            self.rule_type = self.rules_company_id.rule_type
            self.applicable_on = self.rules_company_id.applicable_on
            self.auto_validation = self.rules_company_id.auto_validation
            self.warehouse_id = self.rules_company_id.warehouse_id.id

    # YTI FIXME: Could define related fields instead
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.rules_company_id:
            vals = {
                'applicable_on': self.applicable_on,
                'auto_validation': self.auto_validation,
                'rule_type': self.rule_type,
                'warehouse_id': self.warehouse_id.id
            }
            self.rules_company_id.write(vals)
