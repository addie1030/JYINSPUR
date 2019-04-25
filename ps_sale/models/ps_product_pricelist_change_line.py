from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError


class ProductPricelistChangeLine(models.Model):
    _name = 'ps.product.pricelist.change.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product PriceList ChangeLine'

    lines_id = fields.Many2one('ps.product.pricelist.change', string='Price Change')
    type = fields.Selection([('add', 'Add'), ('adjust', 'Adjust')], string='Price Change Type', default='add',
                            required=True)
    product_id = fields.Many2one('product.product', string='Product')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    uom_id = fields.Many2one('uom.uom', string='Uom')
    method = fields.Selection([('fixed', 'Fixed'), ('percentage', 'Percentage')], string='Price Change Method', default='fixed')
    factor = fields.Float(string='Factor')
    price_old = fields.Float(string='Old Price')
    price_new = fields.Float(string='New Price')
    min_qty_old = fields.Integer(string='Old Minimum Number')
    min_qty_new = fields.Integer(string='New Minimum Number')
    start_date_old = fields.Date(string='Old Start Date')
    start_date_new = fields.Date(string='New Start Date')
    end_date_old = fields.Date(string='Old End Date')
    end_date_new = fields.Date(string='New End Date')

    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('assigned', 'Assigned'), ('close', 'Close'),
         ('cancer', 'Cancer')],
        string='State', related="lines_id.state")

    @api.onchange('factor', 'method')
    def _onchange_price_new(self):
        if self.method == 'fixed':
            self.price_new = self.factor + self.price_old

        if self.method == 'percentage':
            if self.price_old:
                self.price_new = self.price_old * (1 + self.factor / 100)

        if self.price_new < 0:
            self.factor = 0
            self.price_new = 0
            raise UserError(_("price_new cannot be less than 0"))

    @api.onchange('price_new')
    def _onchange_price_factor(self):
        if self.method == 'fixed':
            self.factor = self.price_new - self.price_old
        if self.method == 'percentage':
            if self.price_old:
                self.factor = (self.price_new / self.price_old - 1) * 100

        if self.price_new < 0:
            self.factor = 0
            self.price_new = 0
            raise UserError(_("price_new cannot be less than 0"))

    @api.onchange('min_qty_new')
    def _onchange_min_qty_new(self):
        if self.min_qty_new < 0:
            self.min_qty_new = 0
            raise UserError(_("min_qty_new cannot be less than 0"))

    @api.onchange('start_date_new','end_date_new')
    def _onchange_date(self):
        if self.start_date_new  and self.end_date_new:
            delta = (self.end_date_new - self.start_date_new).days
            if delta < 0:
                self.start_date_new = self.start_date_old
                self.end_date_new = self.end_date_old
                raise UserError(_("end_date_new cannot be less than start_date_new"))

        if  self.end_date_new and not self.start_date_new:
            if self.start_date_old:
                self.start_date_new = self.start_date_old
                delta = (self.end_date_new - self.start_date_new).days
                if delta < 0:
                    self.start_date_new = self.start_date_old
                    self.end_date_new = self.end_date_old
                    raise UserError(_("end_date_new cannot be less than start_date_new"))


        if self.start_date_new and not self.end_date_new:
            if self.end_date_old:
                self.end_date_new = self.end_date_old
                delta = (self.end_date_new - self.start_date_new).days
                if delta < 0:
                    self.start_date_new = self.start_date_old
                    self.end_date_new = self.end_date_old
                    raise UserError(_("end_date_new cannot be less than start_date_new"))
