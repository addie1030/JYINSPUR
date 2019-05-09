# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import Warning


class res_company(models.Model):

    _inherit = 'res.company'

    rule_type = fields.Selection([('so_and_po', 'Synchronize Sales & Purchase Orders'),
        ('invoice_and_refund', 'Synchronize Invoices & Bills')],
        help='Select the type to setup inter company rules in selected company.', default='so_and_po')
    applicable_on = fields.Selection([('sale', 'Sale Order'), ('purchase', 'Purchase Order'),
          ('sale_purchase', 'Sale and Purchase Order')])
    auto_validation = fields.Selection([('draft', 'draft'), ('validated', 'validated')])
    intercompany_user_id = fields.Many2one("res.users", string="Inter Company User", default=SUPERUSER_ID,
        help="Responsible user for creation of documents triggered by intercompany rules.")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse",
        help="Default value to set on Purchase(Sales) Orders that will be created based on Sale(Purchase) Orders made to this company")

    @api.model
    def _find_company_from_partner(self, partner_id):
        company = self.sudo().search([('partner_id', '=', partner_id)], limit=1)
        return company or False

    @api.onchange('rule_type')
    def onchange_rule_type(self):
        if self.rule_type == 'invoice_and_refund':
            self.applicable_on = False
            self.auto_validation = False
            self.warehouse_id = False

    @api.one
    @api.constrains('applicable_on', 'rule_type')
    def _check_intercompany_missmatch_selection(self):
        if self.applicable_on and self.rule_type == 'invoice_and_refund':
            raise Warning(_('''You cannot select to create invoices based on other invoices
                    simultaneously with another option ('Create Sales Orders when buying to this
                    company' or 'Create Purchase Orders when selling to this company')!'''))

