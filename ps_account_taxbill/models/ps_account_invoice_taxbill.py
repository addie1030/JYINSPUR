# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.addons import decimal_precision as dp

class PsAccountInvoiceTaxbill(models.Model):
    _name = 'ps.account.invoice.taxbill'
    _description = "VAT Information"

    taxbill_id = fields.Many2one('ps.account.taxbill', string='Customer Taxbill Application',
                                 ondelete="cascade") #客户开票申请
    original_taxbill = fields.Char(string="Customer Taxbill Document No") #客户开票申请单据编号
    partner_id = fields.Many2one('res.partner', string='Customer') #客户
    tax_invoice_type = fields.Selection([('1', 'Common VAT Invoice'), ('2', 'Special VAT Invoice'), ('3','E-invoice')],
                                    string='Taxbill Type') #税票类型
    invoice_code = fields.Char(string='Taxbill Code') #税票代码
    invoice_number = fields.Char(string='Taxbill Number') #税票号码
    taxbill_date = fields.Date(string='Taxbill Date') #开票日期
    taxbill_state = fields.Selection([('1', 'Obsolete'), ('0', 'Normal')], string='Taxbill State') #发票状态
    tax_amount = fields.Float(string='Tax Amount', digits=dp.get_precision('Product Price')) #税额
    amount = fields.Float(string='Amount', digits=dp.get_precision('Product Price')) #金额
    invoice_url = fields.Html(string='E-invoice Address') #电子发票地址
    notes = fields.Char(string='Note') #备注
    invoice_taxbill_ids = fields.One2many('ps.account.invoice.taxbill.line', 'invoice_taxbill_id',
                                          string='Taxbill Information Line')


class PsAccountInvoiceTaxbillLine(models.Model):
    _name = 'ps.account.invoice.taxbill.line'
    _description = "VAT Information Lines"

    invoice_taxbill_id = fields.Many2one('ps.account.invoice.taxbill', string='Download Tax bill',
                                         ondelete="cascade") # 税票信息表头
    taxbill_id = fields.Many2one('ps.account.taxbill', string='Tax Bill',
                                 ondelete="cascade")  # 开票申请
    trade_name = fields.Char(string='Trade Name')  # 商品名称
    specification = fields.Char(string='Specification')  # 规格型号
    uom_name = fields.Char(string='UOM')  # 计量单位
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'), string='Quantity') # 数量
    tax_rate = fields.Float(string='Tax Rate', digits=dp.get_precision('Product Price'))  # 税率
    price_unit = fields.Float(digits=dp.get_precision('Product Price'), string='Unit Price (tax excluded)')  # 单价(不含税)
    price_unit_tax = fields.Float(digits=dp.get_precision('Product Price'), string='Unit Price (tax included)')  # 单价(含税)
    price_subtotal = fields.Float(string='Subtotal', digits=dp.get_precision('Product Price')) # 金额（不含税）
    price_total = fields.Float(string='Total', digits=dp.get_precision('Product Price')) # 金额(含税）
    price_tax = fields.Float(string='Amount of Tax', digits=dp.get_precision('Product Price')) # 税额
    code_number = fields.Char(string='Sorting Code No') #分类编码
