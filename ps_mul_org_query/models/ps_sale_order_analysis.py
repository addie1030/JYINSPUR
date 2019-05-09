from odoo import fields, models, api, _
from odoo import tools
from odoo.exceptions import UserError, ValidationError


class PsAccountMoveCheck(models.Model):
    _name = 'ps.sale.order.analysis'
    _auto = False

    sale_partner_id = fields.Many2one('res.partner', string='Sale Partner')
    purchase_partner_id = fields.Many2one('res.partner', string='Purchase Partner')
    sale_name = fields.Char(string='Order Name')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom = fields.Many2one('uom.uom', string='Product Uom')
    product_uom_qty = fields.Char(string='Product Uom Qty')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('sale', 'Sales'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase'),
        ], string='Status')
    price_reduce_taxexcl = fields.Float(string='Price Reduce Taxexcl')
    price_tax = fields.Float(string='Price Tax')
    price_reduce_taxinc = fields.Float(string='Price Reduce Taxinc')
    amt_invoiced = fields.Float(string='Amt Invoiced')
    out_name = fields.Char(string='Out Name')
    in_name = fields.Char(string='In Name')

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            create view %s as (  
                select 
                    row_number() over() as id,
                       sale_partner_id,
                       purchase_partner_id,
                       sale_name,
                       product_id,
                       product_uom,
                       product_uom_qty,
                       state,
                       price_reduce_taxexcl,
                       price_tax,
                       price_reduce_taxinc,
                       amt_invoiced,
                       out_name,
                       in_name from (
                           
                select 
                    so.partner_id as sale_partner_id,
                    rc.partner_id as purchase_partner_id,
                    so.name as sale_name,
                    sol.product_id as product_id,
                    sol.product_uom as product_uom,
                    sol.product_uom_qty as product_uom_qty,
                    so.state as state,
                    sol.price_reduce_taxexcl as price_reduce_taxexcl,
		            sol.price_tax as price_tax,
		            sol.price_reduce as price_reduce_taxinc,
		            so.amount_total as amt_invoiced,
		            '' as out_name,
		            '' as in_name
                from sale_order so,sale_order_line sol,res_company rc
                where so.id=sol.order_id and so.state<>'draft' and so.invoice_status='to invoice'
                        and so.company_id=rc.id
                group by 
		            so.partner_id,so.name,sol.product_id,sol.product_uom,sol.product_uom_qty,so.state,
		            sol.price_reduce_taxexcl,sol.price_tax,sol.price_reduce,so.amount_total,rc.partner_id
                union all
                select 
                    so.partner_id as sale_partner_id,
                    rc.partner_id as purchase_partner_id,
                    so.name as sale_name,
                    sol.product_id as product_id,
                    sol.product_uom as product_uom,
                    sol.product_uom_qty as product_uom_qty,
                    so.state as state,
                    sol.price_reduce_taxexcl as price_reduce_taxexcl,
		            sol.price_tax as price_tax,
		            sol.price_reduce as price_reduce_taxinc,
		            so.amount_total as amt_invoiced,
		            '' as out_name,
		            '' as in_name
                from sale_order so,sale_order_line sol,account_invoice ai,res_company rc
                where so.id=sol.order_id and so.state<>'draft' and so.invoice_status='invoiced'
		              and ai.origin=so.name and so.company_id=rc.id
		        group by 
		            so.partner_id,so.name,sol.product_id,sol.product_uom,sol.product_uom_qty,so.state,
		            sol.price_reduce_taxexcl,sol.price_tax,sol.price_reduce,so.amount_total,rc.partner_id
                UNION all 
                
                select 
                    so.partner_id as sale_partner_id,
                    rc.partner_id as purchase_partner_id,
                    so.name as sale_name,
                    sol.product_id as product_id,
                    sol.product_uom as product_uom,
                    sol.product_uom_qty as product_uom_qty,
                    so.state as state,
                    sol.price_reduce_taxexcl as price_reduce_taxexcl,
		            sol.price_tax as price_tax,
		            sol.price_reduce as price_reduce_taxinc,
		            so.amount_total as amt_invoiced,
		            ap.name as out_name,
		            '' as in_name
                from sale_order so,sale_order_line sol,account_invoice ai,account_payment ap,res_company rc
                where so.id=sol.order_id and so.state<>'draft' and so.invoice_status='invoiced'
		              and ai.origin=so.name and ap.communication=ai.number and so.company_id=rc.id
		        group by 
		            so.partner_id,so.name,sol.product_id,sol.product_uom,sol.product_uom_qty,so.state,
		            sol.price_reduce_taxexcl,sol.price_tax,sol.price_reduce,so.amount_total,ap.name,rc.partner_id
                
                union all 
                
                select   
                    rc.partner_id as sale_partner_id,
                    po.partner_id as purchase_partner_id,
                    po.name as sale_name,
                    pol.product_id as product_id,
                    pol.product_uom as product_uom,
                    pol.product_qty as product_uom_qty,
                    pol.state as state,
                    pol.price_unit as price_reduce_taxexcl,
                    pol.price_tax as price_tax,
		            pol.price_total as price_reduce_taxinc,
		            po.amount_total as amt_invoiced,
		            '' as out_name,
		            '' as in_name
                from purchase_order po,purchase_order_line pol,res_company rc
                where 
	                po.id=pol.order_id and po.state<>'draft' and po.invoice_status='no' and po.company_id=rc.id
	            group by 
	                po.partner_id,po.name,pol.product_id,pol.product_uom,pol.product_qty,pol.state,
	                pol.price_unit,pol.price_tax,pol.price_total,po.amount_total,rc.partner_id
	            
	            union all 
	            
	            select   
                    rc.partner_id as sale_partner_id,
                    po.partner_id as purchase_partner_id,
                    po.name as sale_name,
                    pol.product_id as product_id,
                    pol.product_uom as product_uom,
                    pol.product_qty as product_uom_qty,
                    pol.state as state,
                    pol.price_unit as price_reduce_taxexcl,
                    pol.price_tax as price_tax,
		            pol.price_total as price_reduce_taxinc,
		            po.amount_total as amt_invoiced,
		            '' as out_name,
		            '' as in_name
                from purchase_order po,purchase_order_line pol,account_invoice ai,res_company rc
                where 
	                po.id=pol.order_id and po.state<>'draft' and po.invoice_status='invoiced'
					and ai.origin=po.name and po.company_id=rc.id
	            group by 
	                po.partner_id,po.name,pol.product_id,pol.product_uom,pol.product_qty,pol.state,
	                pol.price_unit,pol.price_tax,pol.price_total,po.amount_total,rc.partner_id
	            
                ) as t
                            
        )"""% self._table
        self.env.cr.execute(query)

    # 重写unlink函数
    @api.multi
    def unlink(self):
        raise ValidationError(_('Query data cannot be deleted.'))