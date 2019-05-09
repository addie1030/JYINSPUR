# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class purchase_order(models.Model):

    _inherit = "purchase.order"

    auto_generated = fields.Boolean(string='Auto Generated Purchase Order', copy=False)
    auto_sale_order_id = fields.Many2one('sale.order', string='Source Sales Order', readonly=True, copy=False)

    @api.multi
    def button_approve(self, force=False):
        """ Generate inter company sales order base on conditions."""
        res = super(purchase_order, self).button_approve(force=force)
        for order in self:
            # get the company from partner then trigger action of intercompany relation
            company_rec = self.env['res.company']._find_company_from_partner(order.partner_id.id)
            if company_rec and company_rec.applicable_on in ('purchase', 'sale_purchase') and (not order.auto_generated):
                order.inter_company_create_sale_order(company_rec)
        return res


    @api.one
    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id)
        SaleOrder = self.env['sale.order']

        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise Warning(_('Provide at least one user for inter company relation for % ') % company.name)
        # check intercompany user access rights
        if not SaleOrder.sudo(intercompany_uid).check_access_rights('create', raise_exception=False):
            raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)

        # check pricelist currency should be same with SO/PO document
        company_partner = self.company_id.partner_id.sudo(intercompany_uid)
        if self.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
            raise Warning(_('You cannot create SO from PO because sale price list currency is different than purchase price list currency.'))

        # create the SO and generate its lines from the PO lines
        SaleOrderLine = self.env['sale.order.line']
        # read it as sudo, because inter-compagny user can not have the access right on PO
        sale_order_data = self.sudo()._prepare_sale_order_data(self.name, company_partner, company, self.dest_address_id and self.dest_address_id.id or False)
        sale_order = SaleOrder.sudo(intercompany_uid).create(sale_order_data[0])
        # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
        for line in self.order_line.sudo():
            so_line_vals = self._prepare_sale_order_line_data(line, company, sale_order.id)
            SaleOrderLine.sudo(intercompany_uid).create(so_line_vals)

        # write vendor reference field on PO
        if not self.partner_ref:
            self.partner_ref = sale_order.name

        #Validation of sales order
        if company.auto_validation == 'validated':
            sale_order.sudo(intercompany_uid).action_confirm()

    @api.one
    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """ Generate the Sales Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        if not warehouse:
            raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('sale.order') or '/',
            'company_id': company.id,
            'warehouse_id': warehouse.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'payment_term_id': partner.property_payment_term_id.id,
            'user_id': False,
            'auto_generated': True,
            'auto_purchase_order_id': self.id,
            'partner_shipping_id': direct_delivery_address or partner_addr['delivery']
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param sale_id : the id of the SO
        """
        # it may not affected because of parallel company relation
        price = line.price_unit or 0.0
        taxes = line.taxes_id
        if line.product_id:
            taxes = line.product_id.taxes_id
        company_taxes = [tax_rec for tax_rec in taxes if tax_rec.company_id.id == company.id]
        if sale_id:
            so = self.env["sale.order"].sudo(company.intercompany_user_id).browse(sale_id)
            company_taxes = so.fiscal_position_id.map_tax(company_taxes, line.product_id, so.partner_id)
        quantity = line.product_id and line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom._compute_price(price, line.product_id.uom_id) or price
        return {
            'name': line.name,
            'order_id': sale_id,
            'product_uom_qty': quantity,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
            'price_unit': price,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            'tax_id': [(6, 0, company_taxes.ids)],
        }
