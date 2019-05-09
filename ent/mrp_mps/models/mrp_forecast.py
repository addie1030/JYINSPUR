# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

# FIXME QDP TODO need to document all these methods. Please add docstrings

class SaleForecast(models.Model):
    _name = 'sale.forecast'
    _rec_name = 'product_id'
    _order = 'date'
    _description = 'Sales Forecast'

    date = fields.Date('Date', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='product_id.uom_id', readonly=False)
    forecast_qty = fields.Float('Demand Forecast')
    to_supply = fields.Float('To Supply', help="If mode is Manual, this is the forced value")
    group_id = fields.Many2one('procurement.group', 'Procurement Group')
    mode = fields.Selection([('auto','Automatic'),('manual','Manual')], string="Mode", default='auto', required=True)
    state = fields.Selection([('draft','Forecast'), ('done','Done')], 'State', default='draft', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Production Location')

    @api.model
    def generate_procurement_all(self):
        products = self.env['product.product'].search([('mps_active', '=', True)])
        for product in products:
            self.generate_procurement(product_id=product.id, limit=False)
        return True

    @api.model
    def generate_procurement(self, product_id=False, limit=False):
        """ Create procurements related to """
        product = self.env['product.product'].browse(product_id)
        mps_report = self.env['mrp.mps.report'].search([])[0]
        if not limit:
            result = [x for x in mps_report.get_data(product) if x['procurement_enable']]
            for data in result:
                date_cmp = fields.Date.from_string(data['date'])
                if date_cmp < fields.Date.context_today(self):
                    date = fields.Date.context_today(self)
                else:
                    date = date_cmp
                self._action_procurement_create(product, data['to_supply'], date)
                domain = [('date', '<', data['date_to']),
                          ('date', '>=', data['date']),
                          ('product_id', '=', product_id),
                          ('state', '!=', 'done'),]
                forecasts = self.search(domain)
                if forecasts:
                    forecasts.write({'state': 'done'})
                else:
                    self.create({'date': date_cmp, 'product_id': product_id, 'forecast_qty': 0.0,
                                 'state': 'done'})
        else:
            result = [x for x in mps_report.get_data(product) if not x['procurement_done']]
            if result:
                data = result[0]
                date_cmp = fields.Date.from_string(data['date'])
                if date_cmp < fields.Date.context_today(self):
                    date = fields.Date.context_today(self)
                else:
                    date = date_cmp
                self._action_procurement_create(product, data['to_supply'], date)
                domain = [('date', '>=', data['date']),
                          ('date', '<', data['date_to']),
                          ('product_id', '=', product_id),
                          ('state', '!=', 'done')]
                forecasts = self.search(domain)
                if forecasts:
                    forecasts.write({'state': 'done'})
                else:
                    self.create({'date': date_cmp,
                                 'product_id': product_id,
                                 'forecast_qty': 0.0,
                                 'state': 'done'})
        return True

    @api.model
    def _prepare_procurement(self, product, date):
        # TODO currently only work on the main (first) warehouse
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        return {
            'date_planned': date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'company_id': self.env.user.company_id,
            'warehouse_id': warehouse[0] if warehouse else False,
            'add_date_in_domain': True,
        }

    @api.model
    def _action_procurement_create(self, product, to_supply, date):
        if to_supply:
            vals = self._prepare_procurement(product, date)
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            location = warehouse[0].lot_stock_id if warehouse else False
            self.env['procurement.group'].run(product, to_supply, product.uom_id, location, product.name, 'MPS', vals)
        return False

    @api.model
    def save_forecast_data(self, product_id=False, quantity=0, date=False, date_to=False, field=None):
        """When the user changes the quantity on the forecast or on the forced quantity to supply, adapt the existing quantities """
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom']._bom_find(product=product)
        if bom:
            product.apply_active = True
        domain = [('product_id', '=', product_id), ('date', '>=', str(date)), ('date', '<', str(date_to))]
        if field == 'forecast_qty':
            domain += [('mode', '=', 'auto')]
        else:
            domain += [('mode', '=', 'manual')]
        forecasts = self.search(domain, order="date")
        if field == 'forecast_qty':
            qty_period = sum(forecasts.mapped('forecast_qty'))
            new_quantity = quantity - qty_period
            if forecasts:
                forecasts[0].write({'forecast_qty': forecasts[0].forecast_qty + new_quantity})
            else:
                self.create({'date': date, 'product_id': product_id, 'forecast_qty': new_quantity})
        if field == 'to_supply':
            if quantity is False:
                # If you put it back to manual, then delete the to_supply
                forecasts.filtered(lambda x: x.state != 'done').unlink()
            else:
                qty_supply = sum(forecasts.mapped('to_supply'))
                new_quantity = quantity - qty_supply
                if forecasts and forecasts[0].date == fields.Date.from_string(date):
                    forecasts[0].write({'to_supply': forecasts[0].to_supply + new_quantity})
                else:
                    self.create({'date': date, 'product_id': product_id, 'to_supply': new_quantity, 'mode': 'manual'})

    @api.model
    def change_forecast_mode(self, product_id=False, date=False, date_to=False, quantity=0.0):
        if date and date_to:
            self.search([('date', '>=', date), ('date', '<', date_to), ('mode', '=', 'manual'), ('product_id', '=', product_id)]).unlink()
        self.create({'date': date, 'product_id': product_id, 'to_supply': quantity, 'mode': 'manual'})
        return True


class SaleForecastIndirect(models.Model):
    _name = 'sale.forecast.indirect'
    _rec_name = 'product_id'
    _order = 'date, product_id'
    _description = 'Indirect Sales Forecast'

    date = fields.Date('Date', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Production Location')
    product_origin_id = fields.Many2one('product.product', string='Origin Product', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float('Indirect Quantity')


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, values, partner):
        domain = super(StockRule, self)._make_po_get_domain(values, partner)
        if values.get('add_date_in_domain', False) and values.get('date_planned', False):
            domain += (('date_planned', '=', values['date_planned']),)
        return domain
