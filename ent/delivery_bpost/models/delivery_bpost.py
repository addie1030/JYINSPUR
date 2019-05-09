# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from base64 import b64encode

from odoo import fields, models, _
from odoo.exceptions import UserError

from .bpost_request import BpostRequest


class ProviderBpost(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('bpost', 'bpost')])
    # Fields required to configure
    bpost_account_number = fields.Char(string="Bpost Account Number", groups="base.group_system")
    bpost_developer_password = fields.Char(string="Passphrase", groups="base.group_system")
    bpost_delivery_nature = fields.Selection([('Domestic', 'Domestic'), ('International', 'International')],
                                             default='Domestic', required=True)
    bpost_domestic_deliver_type = fields.Selection([('bpack 24h Pro', 'bpack 24h Pro'),
                                                   ('bpack 24h business', 'bpack 24h business'),
                                                   ('bpack Bus', 'bpack Bus')], default='bpack 24h Pro')
    bpost_international_deliver_type = fields.Selection([('bpack World Express Pro', 'bpack World Express Pro'),
                                                         ('bpack World Business', 'bpack World Business'),
                                                         ('bpack Europe Business', 'bpack Europe Business')], default='bpack World Express Pro')
    bpost_label_stock_type = fields.Selection([('A4', 'A4'), ('A6', 'A6')], default='A6')
    bpost_label_format = fields.Selection([('PDF', 'PDF'), ('PNG', 'PNG')], default='PDF')
    bpost_shipment_type = fields.Selection([('SAMPLE', 'SAMPLE'),
                                            ('GIFT', 'GIFT'),
                                            ('GOODS', 'GOODS'),
                                            ('DOCUMENTS', 'DOCUMENTS'),
                                            ('OTHER', 'OTHER')], default='SAMPLE')
    bpost_parcel_return_instructions = fields.Selection([('ABANDONED', 'Destroy'),
                                                         ('RTA', 'Return to sender by air'),
                                                         ('RTS', 'Return to sender by road')])
    bpost_saturday = fields.Boolean(string="Delivery on Saturday", help="Allow deliveries on Saturday (extra charges apply)")
    bpost_default_packaging_id = fields.Many2one('product.packaging', string='bpost Default Packaging Type')

    def bpost_rate_shipment(self, order):
        bpost = BpostRequest(self.prod_environment, self.log_xml)
        check_value = bpost.check_required_value(order.partner_shipping_id, order.carrier_id.bpost_delivery_nature, order.warehouse_id.partner_id, order=order)
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}
        try:
            price = bpost.rate(order, self)
        except UserError as e:
            return {'success': False,
                    'price': 0.0,
                    'error_message': e.name,
                    'warning_message': False}
        if order.currency_id.name != 'EUR':
            quote_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
            price = quote_currency._convert(price, order.currency_id, order.company_id, order.date_order or fields.Date.today())
        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False}

    def bpost_send_shipping(self, pickings):
        res = []
        bpost = BpostRequest(self.prod_environment, self.log_xml)
        for picking in pickings:
            check_value = bpost.check_required_value(picking.partner_id, picking.carrier_id.bpost_delivery_nature, picking.picking_type_id.warehouse_id.partner_id, picking=picking)
            if check_value:
                raise UserError(check_value)
            shipping = bpost.send_shipping(picking, self)
            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.user.company_id
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            if order_currency.name == "EUR":
                carrier_price = shipping['price']
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
                carrier_price = quote_currency._convert(shipping['price'], order_currency, company, order.date_order or fields.Date.today())
            carrier_tracking_ref = shipping['tracking_code']
            # bpost does not seem to handle multipackage
            logmessage = (_("Shipment created into bpost <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))
            picking.message_post(body=logmessage, attachments=[('Label-bpost-%s.%s' % (carrier_tracking_ref, "A6"), shipping['label'])])
            shipping_data = {'exact_price': carrier_price,
                             'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
        return res

    def bpost_get_tracking_link(self, picking):
        return 'http://track.bpost.be/btr/web/#/search?itemCode=%s&lang=en' % picking.carrier_tracking_ref

    def bpost_cancel_shipment(self, picking):
        raise UserError(_("You can not cancel a bpost shipment when a shipping label has already been generated."))

    def _bpost_passphrase(self):
        self.ensure_one()
        if any(c.delivery_type != 'bpost' for c in self):
            raise UserError(_("You cannot compute a passphrase for non-bpost carriers."))
        return b64encode(("%s:%s" % (self.bpost_account_number, self.bpost_developer_password)).encode()).decode()

    def _bpost_convert_weight(self, weight):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)
