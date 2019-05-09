# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError,Warning
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)

class PsAccountTaxbill(models.Model):
    _name = 'ps.account.taxbill'
    _sql_constraints = [
        ('document_no_unique', 'unique(name)', 'Document number cannot be repeated')]

    @api.depends('apply_line_ids')
    def _compute_taxbill_amount_available(self):
        for taxbill in self:
            taxbill.taxbill_amount_available = sum([line.price_total for line in taxbill.apply_line_ids])

    taxbill_amount_available = fields.Float(digits=dp.get_precision('Product Price'), string='Available Tax Bill Amount',
                                         compute='_compute_taxbill_amount_available')  # 申请开票金额
    taxbill_amount_actual = fields.Float(digits=dp.get_precision('Product Price'), string='Actual Tax Bill Amount')  # 实际开票金额
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, domain=[('customer','=',True)]) #客户
    name = fields.Char(string='Document No', requird=True, copy=False, default=lambda self: _('New')) #单据编号
    date = fields.Date(string='Document Date', required=True, default=fields.Date.context_today)  #单据日期
    state = fields.Selection([('draft', 'Draft'), ('checked', 'Confirmed'), ('opening','Opening'), ('done', 'Done')], string='Status',
                             required=True, readonly=True, copy=False, default='draft')  #状态
    invoice_date = fields.Date(string='Invoice Date', required=True, default=fields.Date.context_today)  #开票日期
    user_id = fields.Many2one('res.users', string='Applicant', required=True, default=lambda self: self.env.user)  #申请人
    taxbill_type = fields.Selection([('1', 'Common VAT Invoice'), ('2', 'Special VAT Invoice'), ('3','E-invoice')],
                                    string='Taxbill Type', required=True, default='1') #税票类型
    reviewer_id = fields.Many2one('res.users', string='Reviewer')  # 复核人
    payee_id = fields.Many2one('res.users', string='Payee')  # 收款人
    drawer_id = fields.Many2one('res.users', string='Drawer')  # 开票人
    mobile = fields.Char(string='Mobile')  # 手机号码
    email = fields.Char(string='Email')  # Email地址
    notes = fields.Text(string='Notes')  # 自定义备注
    taxbill_number = fields.Char(string='Taxbill Number')  # 税票号码
    is_discard_zero = fields.Boolean(string='Invoice entries without regard to the amount of 0', default=True)  # 不考虑金额为0的发票分录
    company_id = fields.Many2one('res.company', string='Company', required=True)  # 公司
    apply_line_ids = fields.One2many('ps.account.taxbill.line', 'taxbill_id', string='Tax bill Lines') # 明细
    invoice_bill_ids = fields.One2many('ps.account.invoice.taxbill', 'taxbill_id', string='VAT Information') # 税控发票
    invoice_count = fields.Integer(string='VAT Receipts', compute='_compute_invoice_ids')
    invoice_ids = fields.Many2many('account.invoice', string='Customer Invoice',domain=[('state','not in',['draft','cancel'])])  # 客户发票

    @api.model
    def create(self, vals):
        """
        按规则生成单据号
        :param vals:
        :return: name
        """
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.account.taxbill') or _('New')
        if not vals.get('apply_line_ids'):
            raise UserError(_('This invoice is unavailable!')) # 本发票不可开具发票
        #FIXME copy false
        return super(PsAccountTaxbill, self).create(vals)

    @api.multi
    def unlink(self):
        for bill in self:
            if bill.state != 'draft':
                raise ValidationError(_('Tax Bill ') + bill.name + _(' state is not draft, can not delete.'))
            else:
                for bill_line in bill.apply_line_ids:
                    inv_obj = self.env['account.invoice'].search([('id', '=', bill_line.invoice_id.id)])
                    inv_line_obj = self.env['account.invoice.line'].search([('id', '=', bill_line.invoice_line_id.id)])
                    if bill_line.quantity != 0:
                        inv_line_obj.update({'ps_taxbill_line_qty': inv_line_obj.ps_taxbill_line_qty - bill_line.quantity})
                        inv_obj.update({'ps_is_taxbill_down': False})

        return super(PsAccountTaxbill, self).unlink()

    @api.multi
    def write(self, vals):
        if vals.get('apply_line_ids'):
            for line in vals.get('apply_line_ids'):
                 if line[2]:
                     if line[2].get('quantity'):
                         bill_line_obj = self.env['ps.account.taxbill.line'].search([('id', '=', line[1])])
                         inv_line_obj = self.env['account.invoice.line'].search([('id', '=', bill_line_obj.invoice_line_id.id)])
                         for origin_line in self.apply_line_ids:
                             if origin_line.id == line[1]:
                                 new_qty = inv_line_obj.ps_taxbill_line_qty - origin_line.quantity + line[2].get('quantity')
                                 inv_line_obj.update({'ps_taxbill_line_qty': new_qty})
                                 inv_obj = self.env['account.invoice'].search([('id', '=', inv_line_obj.invoice_id.id)])
                                 if new_qty >= inv_line_obj.quantity:
                                     for inv_line in inv_obj.invoice_line_ids:
                                         if inv_line.ps_taxbill_line_qty < inv_line.quantity:
                                             inv_obj.update({'ps_is_taxbill_down': False})
                                             break
                                     else:
                                         inv_obj.update({'ps_is_taxbill_down': True})
                                 else:
                                     inv_obj.update({'ps_is_taxbill_down': False})
        return super(PsAccountTaxbill, self).write(vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        选择partner后给invoice加domain
        :return: domain
        """
        invoice_objs = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),('state','not in',['draft','cancel']),('ps_is_taxbill_down','=',False)])
        return {
            'domain': {'invoice_ids': [('id', 'in', [x.id for x in invoice_objs])]},
        }

    @api.onchange('invoice_ids')
    def _onchange_invoice_ids(self):
        """
        带出明细的内容
        """
        if self.invoice_ids:
            if not self.partner_id:
                raise UserError(_("You must first select a partner."))
        line_values = []
        for inv in self.invoice_ids:
            if inv.id not in [tbl.invoice_id.id for tbl in self.apply_line_ids]:
                invoice_obj = self.env['account.invoice'].search([('id','=',inv.id)])
                line_values = []
                for inv_line in invoice_obj.invoice_line_ids:
                    taxbill_line_objs = self.env['ps.account.taxbill.line'].search([('invoice_line_id','=',inv_line.id)])
                    # line_quantity = 0
                    # for line_obj in taxbill_line_objs:
                    #     line_quantity =line_quantity + line_obj.quantity
                    line_quantity = sum([line_obj.quantity for line_obj in taxbill_line_objs])
                    if line_quantity < inv_line.quantity and inv_line.price_subtotal!=0:
                        remaining_quantity = inv_line.quantity - line_quantity
                        line_value={
                            'invoice_id': inv_line.invoice_id.id,
                            'invoice_line_id': inv_line.id,
                            'product_id': inv_line.product_id.id,
                            'name': inv_line.name,
                            'discount': inv_line.discount,
                            'price_unit': inv_line.price_unit,
                            'trade_name': inv_line.product_id.ps_trade_name if inv_line.product_id.ps_trade_name else inv_line.product_id.name,
                            'specification': inv_line.product_id.ps_specification,
                            'uom_id': inv_line.uom_id.id,
                            'invoice_line_tax_ids': inv_line.invoice_line_tax_ids.ids,
                            'quantity': remaining_quantity,
                            'invoices_available_quantity': remaining_quantity,
                        }
                        line_values.append((0,0,line_value))
                if not self.apply_line_ids:
                    self.apply_line_ids = line_values
                else:
                    for origin_line in self.apply_line_ids:
                        origin_line_value = {
                            'invoice_id': origin_line.invoice_id.id,
                            'invoice_line_id': origin_line.invoice_line_id.id,
                            'product_id': origin_line.product_id.id,
                            'name': origin_line.name,
                            'discount': origin_line.discount,
                            'price_unit': origin_line.price_unit,
                            'trade_name': origin_line.trade_name if origin_line.trade_name else origin_line.product_id.name,
                            'specification': origin_line.specification,
                            'uom_id': origin_line.uom_id.id,
                            'invoice_line_tax_ids': origin_line.invoice_line_tax_ids.ids,
                            'quantity': origin_line.quantity,
                            'invoices_available_quantity': origin_line.quantity,
                        }
                        line_values.append((0, 0, origin_line_value))
                    self.apply_line_ids = line_values
        self.apply_line_ids = self.apply_line_ids.filtered(lambda t: t.invoice_id in self.invoice_ids)

    @api.multi
    def button_confirm(self):
        self.ensure_one()
        self.write({'state': 'checked'})

    @api.multi
    def action_view_receipts(self):
        '''
        This function returns an action that display invoiced vat receipts
        of given tax bill application ids. It can either be a in a list or in a form
        view, if there is only one invoiced vat receipt to show.
        '''
        action = self.env.ref('ps_account_taxbill_wanhong.ps_account_taxbill_invoice_action_display_tree').read()[0]
        receipts = self.mapped('invoice_bill_ids')
        if len(receipts) > 1:
            action['domain'] = [('id', 'in', receipts.ids)]
        elif receipts:
            action['views'] = [(self.env.ref('ps_account_taxbill_wanhong.ps_account_taxbill_invoice_form').id, 'form')]
            action['res_id'] = receipts.id
        return action

    @api.depends('invoice_bill_ids')
    def _compute_invoice_ids(self):
        for order in self:
            order.invoice_count = len(order.invoice_bill_ids)

class PsAccountTaxbillLine(models.Model):
    _name = 'ps.account.taxbill.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
                 'invoice_id.date_invoice', 'invoice_id.date')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = taxes['total_excluded'] if taxes else self.quantity * price
        self.price_total = taxes['total_included'] if taxes else self.price_subtotal

    def _get_price_tax(self):
        for l in self:
            l.price_tax = l.price_total - l.price_subtotal

    taxbill_id = fields.Many2one('ps.account.taxbill', string='Tax bill',ondelete="cascade", required=True) # 开票申请
    invoice_id = fields.Many2one('account.invoice', string='Customer Invoice')  # 客户发票
    invoice_line_id = fields.Many2one('account.invoice.line', string='Customer Invoice Details')  # 客户发票明细
    product_id = fields.Many2one('product.product', string='Product', required=True)  # 产品
    name = fields.Char(string='name')  # 说明
    trade_name = fields.Char(string='Trade Name')  # 商品名称
    specification = fields.Char(string='Specification')  # 规格型号
    uom_id = fields.Many2one('uom.uom', string='UOM', required=True)  # 计量单位
    quantity = fields.Float(digits=dp.get_precision('Product Price'), string='Quantity', required=True) # 数量
    price_unit = fields.Float(digits=dp.get_precision('Product Price'), string='Unit Price', required=True)  # 单价
    invoice_line_tax_ids = fields.Many2many('account.tax', string='Tax Rate')  # 税率
    price_subtotal = fields.Float('No tax included in the amount', digits=dp.get_precision('Product Price'),compute='_compute_price', required=True) # 金额（不含税）
    price_total = fields.Float('Tax included in the amount', digits=dp.get_precision('Product Price'),compute='_compute_price', required=True) # 金额(含税）
    price_tax = fields.Float('Amount of tax', digits=dp.get_precision('Product Price'),compute='_get_price_tax') # 税额
    partner_id = fields.Many2one('res.partner', string='Customer')  # 客户
    currency_id = fields.Many2one('res.currency', string='Currency')  # 币种
    company_id = fields.Many2one('res.company', string='Company')  # 公司
    company_currency_id = fields.Many2one('res.currency', string='Company Currency')  # 公司币种
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0) # 折扣%
    invoices_available_quantity = fields.Float(digits=dp.get_precision('Product Price'), string='Invoices Available Quantity', required=True)  # 数量
    #TODO invoice_taxbill_ids
    # invoice_taxbill_ids = fields.One2many('ps.account.invoice.taxbill', 'id', string='Taxbill Lines')  # 明细

    @api.constrains('invoices_available_quantity', 'quantity')
    def _check_income_expense(self):
        """
        保存时实际数量不能大于可开票数量
        """
        for line in self:
            if line.quantity > line.invoices_available_quantity:
                    raise ValidationError(_('Invoices Available Quantity cannot be greater than Quantity!'))

    @api.model
    def create(self, vals):
        res = super(PsAccountTaxbillLine, self).create(vals)
        inv_line_obj = self.env['account.invoice.line'].search([('id','=',vals.get('invoice_line_id'))])
        bill_qty = inv_line_obj.ps_taxbill_line_qty + vals.get('quantity')
        inv_line_obj.update({'ps_taxbill_line_qty': bill_qty})
        if bill_qty >= inv_line_obj.quantity:
            inv_obj = self.env['account.invoice'].search([('id', '=', inv_line_obj.invoice_id.id)])
            for inv_line in inv_obj.invoice_line_ids:
                if inv_line.ps_taxbill_line_qty < inv_line.quantity:
                    break
            else:
                inv_obj.update({'ps_is_taxbill_down': True})
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    ps_is_taxbill_down = fields.Boolean(default=False)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    ps_taxbill_line_qty = fields.Float(digits=dp.get_precision('Product Price'), string='Tax Bill Quantity', default=0.0)  # 已开票数量