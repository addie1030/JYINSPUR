# -*- coding: utf-8 -*-

from odoo.addons.account_taxcloud.models.taxcloud_request import TaxCloudRequest

class TaxCloudRequest(TaxCloudRequest):

    def set_order_items_detail(self, order):
        self.cart_items = self.client.factory.create('ArrayOfCartItem')
        cart_items = []
        for index, line in enumerate(order.order_line):
            if line.price_unit >= 0.0 and line.product_uom_qty >= 0.0:
                product_id = line.product_id.id
                tic_code = line.product_id.tic_category_id.code or \
                    line.product_id.categ_id.tic_category_id.code or \
                    line.company_id.tic_category_id.code or \
                    line.env.user.company_id.tic_category_id.code
                qty = line.product_uom_qty
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

                cart_item = self.client.factory.create('CartItem')
                cart_item.Index = index
                cart_item.ItemID = product_id
                if tic_code:
                    cart_item.TIC = tic_code
                cart_item.Price = price_unit
                cart_item.Qty = qty
                cart_items.append(cart_item)
        self.cart_items.CartItem = cart_items
