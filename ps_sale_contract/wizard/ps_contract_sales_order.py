# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ContractSales(models.TransientModel):
    _name = "ps_contract_sales_order.wizard"
    _description = 'Wizard contract to add sales order'

    contract_id = fields.Many2one('ps.sale.contract', string='Contract')
    customer_id = fields.Many2one("res.partner", string="Customer")
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse')
    validity_date = fields.Date(string='Expiration Date', copy=False,
                                help="Manually set the expiration date of your quotation (offer), or it will set the date automatically based on the template if online quotation is installed.")
    sale_person_id = fields.Many2one('res.users', string='Sale Person')
    sale_team_id = fields.Many2one('crm.team', string='Sale Team')
    contract_line = fields.One2many('ps.sale.contract.line.wizard', 'wizard_contract_id', string='Order Line')

    @api.onchange('validity_date')
    def date_validate(self):
        currentdate = fields.Date.today()
        if self.validity_date:
            if self.validity_date < currentdate:
                raise UserError(_("arrange date must late than current date"))

    @api.model
    def default_get(self, fields):
        rec = super(ContractSales, self).default_get(fields)
        contract_id = self.env.context.get('active_id')
        contract = self.env['ps.sale.contract'].browse(contract_id)
        rec['customer_id'] = contract.customer_id.id
        rec['sale_team_id'] = contract.sale_team_id.id
        rec['sale_person_id'] = contract.sale_person_id.id
        line_ids = []
        tax_id = []
        for contract_line in contract.line_ids:
            contract_line.qty_remaining = contract_line.quantity - contract_line.qty_ordered
            line_ids.append((0, 0, {'product_id': contract_line.product_id.id,
                                    'show_product_id': contract_line.product_id.id,
                                    'description': contract_line.description,
                                    'show_description': contract_line.description,
                                    'price': contract_line.price,
                                    'tax_id': contract_line.tax_id.id,
                                    'qty_remaining': contract_line.qty_remaining,
                                    'quantity': contract_line.qty_remaining,
                                    'uom_id': contract_line.uom_id.id,
                                    'show_uom_id': contract_line.uom_id.id,
                                    'wizard_line_id': contract_line.id,
                                    }))
        rec['contract_line'] = line_ids
        return rec

    @api.multi
    def confirm_so(self):
        '''
        After clicking ok, create the sales order
        '''
        sale_order = self.env['sale.order']
        contract_id = self.env.context.get('active_id')
        line_ids = []
        for line in self.contract_line:
            if line.quantity > 0:

                line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description,
                    'price_unit': line.price,
                    'tax_id': [(6, 0, line.tax_id.ids)],
                    'product_uom_qty': line.quantity,
                    'product_uom': line.uom_id.id,
                    'contract_id': contract_id,
                    'contract_line_id': line.wizard_line_id,
                }))
        sale_order=sale_order.create({
            "contract_id": contract_id,
            "partner_id": self.customer_id.id,
            "warehouse_id": self.warehouse_id.id,
            "validity_date": self.validity_date,
            "user_id": self.sale_person_id.id,
            "team_id": self.sale_team_id.id,
            "order_line": line_ids,
            "picking_policy":"one",

        })
        sale_order.action_confirm()



class SaleContractLine(models.TransientModel):
    _name = 'ps.sale.contract.line.wizard'
    _description = 'sale contract.line.wizard'

    product_id = fields.Many2one('product.product', string='Product')
    show_product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description', default='Product Description')
    show_description = fields.Char(string='Description', default='Product Description')
    qty_remaining = fields.Float(tring='Qty remaining')
    quantity = fields.Float(tring='Quantity')
    qty_ordered = fields.Float(string='Qty Ordered')
    qty_delivered = fields.Float(string='Qty Delivered')
    qty_invoiced = fields.Float(string='Qty Invoiced')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    show_uom_id = fields.Many2one('uom.uom', string='Uom')
    price = fields.Float(string='Price')
    tax_id = fields.Many2one('account.tax', string='Tax')
    amount_tax = fields.Float(string='Amount Tax')
    subtotal = fields.Float(string='Subtotal')
    wizard_contract_id = fields.Many2one('ps_contract_sales_order.wizard')
    wizard_line_id = fields.Char("line number")

    @api.onchange('quantity')
    def onchange_quantity(self):
        if self.quantity > self.qty_remaining:
            raise UserError(_("Order quantity of %s must less than remaining quantity") % (self.product_id.name))
        if self.quantity < 0:
            raise UserError(_('Product quantity can not less than zero.'))


