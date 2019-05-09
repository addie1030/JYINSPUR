# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.partner_id.company_id.rule_type == 'so_and_po' and order.partner_id.company_id.applicable_on == 'sale_purchase' and not order.partner_ref:
                # 判断是否选择交易规则和开放仓库
                count = 0
                for line in order.order_line:
                    partner_product = self.env['product.supplierinfo'].search([('company_id', '=', self.env.user.company_id.id), ('name', '=', order.partner_id.id), ('product_tmpl_id', '=', line.product_id.id)])
                    price = partner_product.price
                    min_qty = partner_product.min_qty
                    date_start = partner_product.date_start
                    date_end = partner_product.date_end
                    count += 1

                    if not partner_product.id:
                        raise ValidationError(
                            _("The") + str(count) + _("line in the document, The supplier's priceless list, please contact the administrator to reconfirm after maintenance."))

                    if line.price_unit != price:
                        raise ValidationError(
                            _("The") + str(count)  + _("line in the document, The order price is not in conformity with the list of items."))

                    if line.product_qty < min_qty:
                        raise ValidationError(
                            _("The") + str(count)  + _("line in the document, The minimun quantity of the order is not consistent with the list of items."))

                    if not date_start or not date_end:
                        raise ValidationError(
                            _("The") + str(count) + _("line in the document, The product is not maintained in the supplier's price list."))

                    if line.order_id.date_order.strftime(DF) < date_start.strftime(DF) or line.order_id.date_order.strftime(DF) > date_end.strftime(DF):
                        raise ValidationError(
                            _("The") + str(count)  + _("line in the document, Document order date should be within the start and end date of the price list."))

                    # 判断对方公司是否维护销向税
                    pt = self.env['product.template'].sudo().search([('id', '=', line.product_id.id)])
                    tax_id = []
                    if pt.taxes_id:
                        for r in pt.taxes_id:
                            tax_id.append(r.id)
                    tax = self.env['account.tax'].sudo().search([('company_id', '=', order.partner_id.company_id.id), ('id', 'in', tax_id)])
                    if not tax and line.taxes_id:
                        raise ValidationError(_("The") + str(count)  + _("line in the document, The other company does not set tax on the product. Please contact the other company to set tax, and then reconfirm the document."))
                    elif tax and not line.taxes_id:
                        raise ValidationError(_("The") + str(count)  + _("line in the document, Our company does not set tax on this product. Please contact our company to set tax, and then reconfirm the document."))
        return super(PurchaseOrder, self).button_confirm()

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.partner_id.company_id.rule_type == 'so_and_po' and order.partner_id.company_id.applicable_on == 'sale_purchase' and not order.client_order_ref:
                # 判断是否选择交易规则和开放仓库
                count = 0
                for line in order.order_line:
                    # 判断对方公司是否维护进向税

                    count += 1
                    pt = self.env['product.template'].sudo().search([('id', '=', line.product_id.id)])
                    tax_id = []
                    if pt.supplier_taxes_id:
                        for r in pt.supplier_taxes_id:
                            tax_id.append(r.id)
                    tax = self.env['account.tax'].sudo().search([('company_id', '=', order.partner_id.company_id.id), ('id', 'in', tax_id)])

                    if not tax and line.tax_id:
                        raise ValidationError(_("The") + str(count) + _("line in the document, The other company does not set tax on the product. Please contact the other company to set tax, and then reconfirm the document."))
                    elif tax and not line.tax_id:
                        raise ValidationError(_("The") + str(count) + _("line in the document, Our company does not set tax on this product. Please contact our company to set tax, and then reconfirm the document."))

        return super(SaleOrder, self).action_confirm()