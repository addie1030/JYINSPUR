from odoo import fields, models, api, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError


class PsAccountMoveCheck(models.Model):
    _name = 'ps.sale.invoice.analysis'
    _auto = False

    sale_partner_id = fields.Many2one('res.partner', string='Sale Company')
    purchase_partner_id = fields.Many2one('res.partner', string='Purchase Company')
    number = fields.Char(string='Sale Number')
    purchase_number = fields.Char(string='Purchase Number')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    quantity = fields.Float(string='Quantity')
    currency_id = fields.Many2one('res.currency', string='Currency')
    price_unit = fields.Float(string='Price Unit')
    price_subtotal = fields.Float(string="Price Subtotal")
    type = fields.Selection([('in_invoice', 'Purchase Invoice'), ('out_invoice', 'Sale Invoice')], string='type')
    date = fields.Date(string='Date Invoice')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            create view %s as (
                select 
                    ail.id as id,
                    ai.partner_id as sale_partner_id,
                    rc.partner_id as purchase_partner_id,
                    ai.number as number, 
                    '' as purchase_number,
                    ail.product_id as product_id, 
                    ail.uom_id as uom_id, 
                    ail.quantity as quantity, 
                    ail.currency_id as currency_id, 
                    ail.price_unit as price_unit, 
                    ail.price_subtotal as price_subtotal, 
                    ai.type as type,
                    ai.date_invoice as date
                from account_invoice ai,account_invoice_line ail,res_company rc
                where ai.id = ail.invoice_id and state = 'open' and ai.type = 'out_invoice' and ai.company_id=rc.id
                group by  ail.partner_id,ai.partner_id,ail.id,ai.number,ail.product_id,ail.uom_id,ail.quantity,
                            ail.currency_id,ail.price_unit,ail.price_subtotal,ai.type,ai.date_invoice,rc.partner_id
                
                UNION all 
                
                select 
                    ail.id as id,
                    rc.partner_id as sale_partner_id,
                    ail.partner_id as purchase_partner_id,
                    '' as number, 
                    ai.number as purchase_number,
                    ail.product_id as product_id, 
                    ail.uom_id as uom_id, 
                    ail.quantity as quantity, 
                    ail.currency_id as currency_id, 
                    ail.price_unit as price_unit, 
                    ail.price_subtotal as price_subtotal, 
                    ai.type as type,
                    ai.date_invoice as date
                from account_invoice ai,account_invoice_line ail,res_company rc
                where ai.id = ail.invoice_id and state = 'open' and ai.type = 'in_invoice' and ai.company_id=rc.id
                group by ail.partner_id,ai.partner_id,ail.id,ai.number,ail.product_id,ail.uom_id,ail.quantity,
                            ail.currency_id,ail.price_unit,ail.price_subtotal,ai.type,ai.date_invoice,rc.partner_id
                               
        )"""% self._table
        self.env.cr.execute(query)

    # 重写unlink函数
    @api.multi
    def unlink(self):
        raise ValidationError(_('Query data cannot be deleted.'))