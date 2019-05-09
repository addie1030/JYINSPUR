# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from .dhl_request import DHLProvider

from odoo import models, fields, _


class Providerdhl(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('dhl', "DHL")])

    dhl_SiteID = fields.Char(string="DHL SiteID", groups="base.group_system")
    dhl_password = fields.Char(string="DHL Password", groups="base.group_system")
    dhl_account_number = fields.Char(string="DHL Account Number", groups="base.group_system")
    dhl_package_dimension_unit = fields.Selection([('IN', 'Inches'),
                                                   ('CM', 'Centimeters')],
                                                  default='CM',
                                                  string='Package Dimension Unit')
    dhl_package_weight_unit = fields.Selection([('LB', 'Pounds'),
                                                ('KG', 'Kilograms')],
                                               default='KG',
                                               string="Package Weight Unit")
    dhl_default_packaging_id = fields.Many2one('product.packaging', string='DHL Default Packaging Type')
    dhl_region_code = fields.Selection([('AP', 'Asia Pacific'),
                                        ('AM', 'America'),
                                        ('EU', 'Europe')],
                                       default='AM',
                                       string='Region')
    # Nowadays hidden, by default it's the D, couldn't find any documentation on other services
    dhl_product_code = fields.Selection([('0', '0 - Logistics Services'),
                                         ('1', '1 - Domestic Express 12:00'),
                                         ('2', '2 - B2C'),
                                         ('3', '3 - B2C'),
                                         ('4', '4 - Jetline'),
                                         ('5', '5 - Sprintline'),
                                         ('6', '6 - Secureline'),
                                         ('7', '7 - Express Easy'),
                                         ('8', '8 - Express Easy'),
                                         ('9', '9 - Europack'),
                                         ('A', 'A - Auto Reversals'),
                                         ('B', 'B - Break Bulk Express'),
                                         ('C', 'C - Medical Express'),
                                         ('D', 'D - Express Worldwide'),
                                         ('E', 'E - Express 9:00'),
                                         ('F', 'F - Freight Worldwide'),
                                         ('G', 'G - Domestic Economy Select'),
                                         ('H', 'H - Economy Select'),
                                         ('I', 'I - Break Bulk Economy'),
                                         ('J', 'J - Jumbo Box'),
                                         ('K', 'K - Express 9:00'),
                                         ('L', 'L - Express 10:30'),
                                         ('M', 'M - Express 10:30'),
                                         ('N', 'N - Domestic Express'),
                                         ('O', 'O - DOM Express 10:30'),
                                         ('P', 'P - Express Worldwide'),
                                         ('Q', 'Q - Medical Express'),
                                         ('R', 'R - GlobalMail Business'),
                                         ('S', 'S - Same Day'),
                                         ('T', 'T - Express 12:00'),
                                         ('U', 'U - Express Worldwide'),
                                         ('V', 'V - Europack'),
                                         ('W', 'W - Economy Select'),
                                         ('X', 'X - Express Envelope'),
                                         ('Y', 'Y - Express 12:00'),
                                         ('Z', 'Z - Destination Charges'),
                                         ],
                                        default='D',
                                        string='DHL Product')
    dhl_dutiable = fields.Boolean(string="Dutiable Material", help="Check this if your package is dutiable.")
    dhl_label_image_format = fields.Selection([
        ('EPL2', 'EPL2'),
        ('PDF', 'PDF'),
        ('ZPL2', 'ZPL2'),
    ], string="Label Image Format", default='PDF')
    dhl_label_template = fields.Selection([
        ('8X4_A4_PDF', '8X4_A4_PDF'),
        ('8X4_thermal', '8X4_thermal'),
        ('8X4_A4_TC_PDF', '8X4_A4_TC_PDF'),
        ('6X4_thermal', '6X4_thermal'),
        ('6X4_A4_PDF', '6X4_A4_PDF'),
        ('8X4_CI_PDF', '8X4_CI_PDF'),
        ('8X4_CI_thermal', '8X4_CI_thermal'),
        ('8X4_RU_A4_PDF', '8X4_RU_A4_PDF'),
        ('6X4_PDF', '6X4_PDF'),
        ('8X4_PDF', '8X4_PDF')
    ], string="Label Template", default='8X4_A4_PDF')

    def dhl_rate_shipment(self, order):
        srm = DHLProvider(self.prod_environment, self.log_xml)
        check_value = srm.check_required_value(self, order.partner_shipping_id, order.warehouse_id.partner_id, order=order)
        if check_value:
            return {'success': False,
                    'price': 0.0,
                    'error_message': check_value,
                    'warning_message': False}

        result = srm.rate_request(order, self)
        if result['error_found']:
            return {'success': False,
                    'price': 0.0,
                    'error_message': result['error_found'],
                    'warning_message': False}

        if order.currency_id.name == result['currency']:
            price = float(result['price'])
        else:
            quote_currency = self.env['res.currency'].search([('name', '=', result['currency'])], limit=1)
            price = quote_currency._convert(float(result['price']), order.currency_id, order.company_id, order.date_order or fields.Date.today())

        return {'success': True,
                'price': price,
                'error_message': False,
                'warning_message': False}

    def dhl_send_shipping(self, pickings):
        res = []

        srm = DHLProvider(self.prod_environment, self.log_xml)
        for picking in pickings:
            shipping = srm.send_shipping(picking, self)
            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.user.company_id
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            if order_currency.name == shipping['currency']:
                carrier_price = float(shipping['price'])
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', shipping['currency'])], limit=1)
                carrier_price = quote_currency._convert(float(shipping['price']), order_currency, company, order.date_order or fields.Date.today())
            carrier_tracking_ref = shipping['tracking_number']
            logmessage = (_("Shipment created into DHL <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))
            picking.message_post(body=logmessage, attachments=[('LabelDHL-%s.%s' % (carrier_tracking_ref, self.dhl_label_image_format), srm.save_label())])
            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref
            }
            res = res + [shipping_data]

        return res

    def dhl_get_tracking_link(self, picking):
        return 'http://www.dhl.com/en/express/tracking.html?AWB=%s' % picking.carrier_tracking_ref

    def dhl_cancel_shipment(self, picking):
        # Obviously you need a pick up date to delete SHIPMENT by DHL. So you can't do it if you didn't schedule a pick-up.
        picking.message_post(body=_(u"You can't cancel DHL shipping without pickup date."))
        picking.write({'carrier_tracking_ref': '',
                       'carrier_price': 0.0})

    def _dhl_convert_weight(self, weight, unit):
        weight_uom_id = self.env['product.template']._get_weight_uom_id_from_ir_config_parameter()
        if unit == 'LB':
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_lb'), round=False)
        else:
            return weight_uom_id._compute_quantity(weight, self.env.ref('uom.product_uom_kgm'), round=False)
