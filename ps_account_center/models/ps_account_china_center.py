# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo.addons import decimal_precision as dp


class ResCompany(models.Model):
    _inherit = "res.company"

    industry_id = fields.Many2one('res.partner.industry', 'Industry.')


# 批量设置产品对应科目
class ProductVolumeSetting(models.TransientModel):
    _name = 'ps.product.account.bulk.setting.wizard'
    _description = 'Product Volume Setting'
    taxes_id = fields.Many2many('account.tax', string='Customer Taxes', domain=[('type_tax_use', '=', 'sale')])
    property_account_income_id = fields.Many2one('account.account',
                                                 string="Income Account", oldname="property_account_income",
                                                 help="Keep this field empty to use the default value from the product category.)")

    property_account_expense_id = fields.Many2one('account.account',
                                                  string="Expense Account", oldname="property_account_expense",
                                                  help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account is recognized at the customer invoice validation. If the field is empty, it uses the one defined in the product category.")
    supplier_taxes_id = fields.Many2many('account.tax', string='Vendor Taxes',domain=[('type_tax_use', '=', 'purchase')])

    # asset_category_id = fields.Many2one('account.asset.category', string=_('Asset Type'),
    #                                     ondelete="restrict")

    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Policy",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")
    invoice_policy = fields.Selection(
        [('order', 'Ordered quantities'),
         ('delivery', 'Delivered quantities'),
         ], string='Invoicing Policy',
        help='Ordered Quantity: Invoice based on the quantity the customer ordered.\n'
             'Delivered Quantity: Invoiced based on the quantity the vendor delivered (time or deliveries).',
        default='order')

    @api.multi
    def product_volume_setting(self):
        context = dict(self._context or {})

        if not context.get('active_ids'):
            raise UserError(_('Please select the records to be set.'))
        customerlist = self.env['product.template'].browse(context.get('active_ids'))
        for r in customerlist:
            if self.taxes_id:
                r.taxes_id = self.taxes_id
            if self.property_account_income_id:
                r.property_account_income_id = self.property_account_income_id
            if self.supplier_taxes_id:
                r.supplier_taxes_id = self.supplier_taxes_id
            if self.property_account_expense_id:
                r.property_account_expense_id = self.property_account_expense_id
        return {'type': 'ir.actions.act_window_close'}


# 批量设置客户对应科目
class CustomerVolumeSetting(models.TransientModel):
    # _name = 'ps.partner.account.bulk.setting.wizard'
    _name = 'ps.partner.account.bulk.setting.wizard'
    _description = 'Customer Volume Setting'

    property_account_payable_id = fields.Many2one('account.account',
                                                  string="Account Payable",
                                                  required=True,
                                                  help="This account will be used instead of the default one as the payable account for the current partner")
    property_account_receivable_id = fields.Many2one('account.account',
                                                     string="Account Receivable",
                                                     required=True,
                                                     help="This account will be used instead of the default one as the receivable account for the current partner")

    @api.multi
    def customer_volume_setting(self):
        context = dict(self._context or {})

        if not context.get('active_ids'):
            raise UserError(_('Please select the records to be set.'))
        customerlist = self.env['res.partner'].browse(context.get('active_ids'))
        for r in customerlist:
            r.property_account_receivable_id = self.property_account_receivable_id
            r.property_account_payable_id = self.property_account_payable_id
        return {'type': 'ir.actions.act_window_close'}


    @api.multi
    def confirm_set_button(self):
        context = dict(self._context or {})

        if not context.get('active_ids'):
            raise UserError(_('Please select the journal records to be set.'))
        journallist = self.env['account.journal'].browse(context.get('active_ids'))
        for r in journallist:
            if self.default_credit_account_id:
                r.default_credit_account_id = self.default_credit_account_id
            if self.default_debit_account_id:
                r.default_debit_account_id = self.default_debit_account_id
        return {'type': 'ir.actions.act_window_close'}


# 产品类别科目对应
class ProductCategoryAccountBatchSetting(models.TransientModel):
    _name = "ps.product.category.account.bulk.setting.wizard"
    _description = "Product Category Setting"

    property_account_income_categ_id = fields.Many2one('account.account',
                             string="Income Account", oldname="property_account_income_categ",
                             domain=[('deprecated', '=', False)],
                             help="This account will be used when validating a customer invoice.")
    property_account_expense_categ_id = fields.Many2one('account.account',
                              string="Expense Account", oldname="property_account_expense_categ",
                              domain=[('deprecated', '=', False)],
                              help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")
    property_stock_account_input_categ_id = fields.Many2one(
        'account.account', 'Stock Input Account',
        domain=[('deprecated', '=', False)], oldname="property_stock_account_input_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_account_output_categ_id = fields.Many2one(
        'account.account', 'Stock Output Account',
        domain=[('deprecated', '=', False)], oldname="property_stock_account_output_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the destination location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account',
        domain=[('deprecated', '=', False)],
        help="When real-time inventory valuation is enabled on a product, this account will hold the current value of the products.", )

    property_stock_journal = fields.Many2one(
        'account.journal', 'Stock Journal',
        help="When doing real-time inventory valuation, this is the Accounting Journal in which entries will be automatically posted when stock moves are processed.")


    @api.multi
    def product_category_batch_setting(self):
        context = dict(self._context or {})
        if not context.get('active_ids'):
            raise UserError(_('Please select the content to be operated in bulk.'))
        for i in self.env['product.category'].browse(context.get("active_ids")):
            if self.property_account_income_categ_id:
                i.property_account_income_categ_id = self.property_account_income_categ_id
            if self.property_account_expense_categ_id:
                i.property_account_expense_categ_id = self.property_account_expense_categ_id
            if self.property_stock_account_input_categ_id:
                i.property_stock_account_input_categ_id = self.property_stock_account_input_categ_id
            if self.property_stock_account_output_categ_id:
                i.property_stock_account_output_categ_id = self.property_stock_account_output_categ_id
            if self.property_stock_valuation_account_id:
                i.property_stock_valuation_account_id = self.property_stock_valuation_account_id
            if self.property_stock_journal:
                i.property_stock_journal = self.property_stock_journal


# 卸载会计中心之前提示有未处理数据，需要处理之后才能卸载
class module(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def module_uninstall(self):
        for module_to_remove in self:
            if module_to_remove.name == "ps_account_center":
                sql = """
                                 SELECT * 
                                 FROM PRODUCT_TEMPLATE LEFT JOIN IR_PROPERTY ON ''||PRODUCT_TEMPLATE.ID = SUBSTRING(IR_PROPERTY.RES_ID,18)
                                 WHERE IR_PROPERTY.VALUE_TEXT = 'onemonth'
                                 """
                self.env.cr.execute(sql)
                stock_incoming_ids = self.env.cr.fetchall()
                if stock_incoming_ids:
                    raise UserError(_("Inventory valuation uses 'One Monthly Weighted Averaging' method. It is not allowed to be deleted. Please process the data before uninstalling it."))
        return super(module, self).module_uninstall()


