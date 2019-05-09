from odoo import models, fields, api


# 价格表应用到客户
class ProductPriceList(models.Model):
    _inherit = 'product.pricelist'

    ps_customer_ids = fields.Many2many('res.partner', string="Customer", domain=[('customer', '=', 'True')])

    @api.model
    def create(self, vals):
        res = super(ProductPriceList, self).create(vals)
        for customer in res.ps_customer_ids:
            # delete customer record
            del_price_list = self.env['product.pricelist'].search(
                [('ps_customer_ids', '=', customer.id), ('id', '!=', res.id)])
            del_price_list.with_context(write_from_partner=True).write({
                'ps_customer_ids': [(3, customer.id)]
            })
            # Add customer records to the price list
            customer.with_context(write_from_pricelist=True).write({
                'property_product_pricelist': res.id,
            })
        return res

    @api.multi
    def write(self, vals):
        if self.user_has_groups("product.group_pricelist_item"):
            write_from_partner = self.env.context.get('write_from_partner', False)
            add_customer_ids = []
            del_customer_ids = []
            if not write_from_partner and 'ps_customer_ids' in vals:
                origin_customer_ids = self.ps_customer_ids.ids
                new_customer_ids = vals['ps_customer_ids'][0][2]
                comm_customer_ids = list(set(origin_customer_ids).intersection(set(new_customer_ids)))
                del_customer_ids = list(set(origin_customer_ids).difference(set(comm_customer_ids)))
                add_customer_ids = list(set(new_customer_ids).difference(set(comm_customer_ids)))
            result = super(ProductPriceList, self).write(vals)
            if write_from_partner:
                return result
            if 'ps_customer_ids' in vals:
                #  删除价格表中的已存在当前的客户
                for new_add_customer in add_customer_ids:
                    del_price_list = self.env['product.pricelist'].search(
                        [('ps_customer_ids', '=', new_add_customer), ('id', '!=', self.id)])
                    customer = self.env['res.partner'].browse(new_add_customer)
                    del_price_list.with_context(write_from_partner=True).write({
                        'ps_customer_ids': [(3, customer.id)]
                    })

                if del_customer_ids:
                    # 当删除价格表中的客户时，设置客户的默认价格表为公共价格表
                    del_customer = self.env['res.partner'].search([('id', 'in', del_customer_ids)])
                    del_customer.with_context(write_from_pricelist=True).write({
                        'property_product_pricelist': self.env.ref('product.list0').id
                    })
                if add_customer_ids:
                    # 当更新价格表中的客户时，更新客户下的价格表
                    add_customer = self.env['res.partner'].search([('id', 'in', add_customer_ids)])
                    add_customer.with_context(write_from_pricelist=True).write({
                        'property_product_pricelist': self.id,
                    })
            return result
        else:
            return super(ProductPriceList, self).write(vals)


# 客户应用到价格表
class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        #  增加价格表中的客户记录
        if res.property_product_pricelist:
            res.property_product_pricelist.with_context(write_from_partner=True).write({
                'ps_customer_ids': [(4, res.id)]
            })
        else:
            pricelist_id = self.env.ref('product.list0').id
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            pricelist.with_context(write_from_partner=True).write({
                'ps_customer_ids': [(4, res.id)]
            })
        return res

    @api.multi
    def write(self, vals):
        """
        先删除旧价格表中的客户，然后在新的价格表中添加客户
        :param vals:
        :return:
        """
        if self.user_has_groups("product.group_pricelist_item"):
            result = super(ResPartner, self).write(vals)
            write_from_pricelist = self.env.context.get('write_from_pricelist', False)
            if write_from_pricelist:
                return result
            if 'property_product_pricelist' in vals:
                for customer in self:
                    #  删除价格表中的客户记录
                    del_pricelist_ids = self.env['product.pricelist'].search([('ps_customer_ids', '=', customer.id)])
                    del_pricelist_ids.with_context(write_from_partner=True).write({
                        'ps_customer_ids': [(3, customer.id)]
                    })
                    #  增加价格表中的客户记录
                    customer.property_product_pricelist.with_context(write_from_partner=True).write({
                        'ps_customer_ids': [(4, customer.id)]
                    })

            return result
        else:
            return super(ResPartner, self).write(vals)
