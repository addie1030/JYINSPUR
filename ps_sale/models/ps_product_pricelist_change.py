from odoo.exceptions import UserError, AccessError
from odoo import fields, models, api, _


class ProductPricelistChange(models.Model):
    _name = 'ps.product.pricelist.change'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = ' Product PriceList Change'

    name = fields.Char(string='Number', readonly=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.today())
    is_add_pricelsit = fields.Boolean()
    pricelist_id = fields.Many2one('product.pricelist', string='Price List')
    currency_id = fields.Many2one('res.currency', string='Currency', related="pricelist_id.currency_id", required=True)
    description = fields.Char(string='Description')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('assigned', 'Assigned'),
         ('close', 'Closed'),
         ('cancer', 'Cancelled')],
        string='State', default='draft', track_visibility='onchange')
    change_lines_ids = fields.One2many('ps.product.pricelist.change.line', 'lines_id', string='Price Change Details')

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].next_by_code('ps.product.pricelist.change')
        return super(ProductPricelistChange, self).create(vals)

    @api.multi
    def submit(self):
        self.state = 'confirmed'

    @api.multi
    def cancer(self):
        self.state = 'cancer'

    @api.multi
    def draft(self):
        self.state = 'draft'

    def _pricelist_update(self, tpricelist_id, record):
        tpricelist_id.write({
            'fixed_price': record.price_old if not record.price_new else record.price_new,
            'min_quantity': record.min_qty_old if not record.min_qty_new else record.min_qty_new,
            'date_start': record.start_date_old if not record.start_date_new else record.start_date_new,
            'date_end': record.end_date_old if not record.end_date_new else record.end_date_new
        })

    def _pricelist_create(self, pricelist, record, product_tmpl_id=None):
        values = {
            'applied_on': '1_product',
            'product_tmpl_id': product_tmpl_id,
            'fixed_price': record.price_new,
            'compute_price': 'fixed',
            'min_quantity': record.min_qty_new,
            'date_start': record.start_date_new,
            'date_end': record.end_date_new
        }
        if product_tmpl_id:
            values.update({'pricelist_id': self.pricelist_id.id})
        else:
            values.update({'product_id': record.product_id.id})
        pricelist.create(values)

    @api.multi
    def review(self):
        for record in self.change_lines_ids:
            product_tmpl_id = self.env['product.product'].search([('id', '=', record.product_id.id)]).product_tmpl_id.id
            pricelist = self.env['product.pricelist.item']
            tem_pricelist_id = pricelist.search(
                [('product_tmpl_id', '=', product_tmpl_id), ('pricelist_id', '=', self.pricelist_id.id)])
            pro_pricelist_id = pricelist.search(
                [('product_id', '=', record.product_id.id), ('pricelist_id', '=', self.pricelist_id.id)])
            if pro_pricelist_id:
                self._pricelist_update(pro_pricelist_id, record)
            elif not tem_pricelist_id:
                self._pricelist_create(pro_pricelist_id, record)
            if tem_pricelist_id:
                self._pricelist_update(tem_pricelist_id, record)
            elif not pro_pricelist_id:
                self._pricelist_create(tem_pricelist_id, record, product_tmpl_id=product_tmpl_id)

        self.state = 'assigned'
        self.is_add_pricelsit = True

    @api.multi
    def close(self):
        self.state = 'close'

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _("You can't delete a non-draft status adjustment plan, please set it to draft status first!"))
        return super(ProductPricelistChange, self).unlink()

    @api.multi
    def load_price_detail(self):
        self.is_add_pricelsit = True
        for item in self.env['product.pricelist.item'].search([('pricelist_id', '=', self.pricelist_id.id)]):
            if item.compute_price == 'fixed':
                product_ids = self.env['product.product'].search(
                    [('product_tmpl_id', '=', item.product_tmpl_id.id)]).ids + item.product_id.ids
                for product_id in product_ids:
                    self.change_lines_ids.create({
                        'lines_id': self.id,
                        'type': 'adjust',
                        'product_id': product_id,
                        'method': item.compute_price,
                        'price_old': item.fixed_price,
                        'price_new': item.fixed_price,
                        'min_qty_old': item.min_quantity,
                        'start_date_old': item.date_start,
                        'start_date_new': item.date_start,
                        'end_date_old': item.date_end,
                        'end_date_new': item.date_end,
                    })
