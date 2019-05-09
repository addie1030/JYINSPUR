# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from binascii import a2b_base64
import logging
import re
import requests
from lxml import html
from xml.etree import ElementTree as etree
from werkzeug.urls import url_join


from odoo import _
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


def _grams(kilograms):
    return int(kilograms * 1000)


class BpostRequest():

    def __init__(self, prod_environment, debug_logger):
        self.debug_logger = debug_logger
        if prod_environment:
            self.base_url = 'https://api-parcel.bpost.be/services/shm/'
        else:
            self.base_url = 'https://api-parcel.bpost.be/services/shm/'

    def check_required_value(self, recipient, delivery_nature, shipper, order=False, picking=False):
        recipient_required_fields = ['city', 'zip', 'country_id']
        if not recipient.street and not recipient.street2:
            recipient_required_fields.append('street')
        shipper_required_fields = ['city', 'zip', 'country_id']
        if not shipper.street and not shipper.street2:
            shipper_required_fields.append('street')

        res = [field for field in recipient_required_fields if not recipient[field]]
        if res:
            return _("The recipient address is incomplete or wrong (Missing field(s):  \n %s)") % ", ".join(res).replace("_id", "")
        if recipient.country_id.code == "BE" and delivery_nature == 'International':
            return _("bpost International is used only to ship outside Belgium. Please change the delivery method into bpost Domestic.")
        if recipient.country_id.code != "BE" and delivery_nature == 'Domestic':
            return _("bpost Domestic is used only to ship inside Belgium. Please change the delivery method into bpost International.")

        res = [field for field in shipper_required_fields if not shipper[field]]
        if res:
            return _("The address of your company/warehouse is incomplete or wrong (Missing field(s):  \n %s)") % ", ".join(res).replace("_id", "")
        if shipper.country_id.code != 'BE':
            return _("Your company/warehouse address must be in Belgium to ship with bpost")

        if order:
            if order.order_line and all(order.order_line.mapped(lambda l: l.product_id.type in ['service', 'digital'])):
                return _("The estimated shipping price cannot be computed because all your products are service/digital.")
            if not order.order_line:
                return _("Please provide at least one item to ship.")
            if order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and line.product_id.type not in ['service', 'digital']):
                return _('The estimated shipping cannot be computed because the weight of your product is missing.')
        return False

    def _parse_address(self, partner):
        streetName = None
        number = None
        if partner.country_id.code == 'BE':
            # match the first or the last number of an address
            # for Belgian "boîte/bus", they should be put in street2
            # so that if you live "Rue du 40e régiment 12A", 12A is returned
            # also supports "Rue du 40e régiment 12/3"
            ex = re.compile(r'^\d+|\d+([a-zA-Z]|/\d)?$')
        else:
            # match the first number in street because we don't know other
            # countries rules
            ex = re.compile(r'\d+')
        match = ex.search(partner.street)
        number = match.group(0) if match else '0'
        streetName = u'%s %s' % (partner.street.replace(number, ''), partner.street2 if partner.street2 else '')
        return (streetName, number)

    def rate(self, order, carrier):
        weight = sum([(line.product_id.weight * line.product_qty) for line in order.order_line]) or 0.0
        weight_in_kg = carrier._bpost_convert_weight(weight)
        return self._get_rate(carrier, weight_in_kg, order.partner_shipping_id.country_id)

    def _get_rate(self, carrier, weight, country):
        '''@param carrier: a record of the delivery.carrier
           @param weight: in kilograms
           @param country: a record of the destination res.country'''

        # Surprisingly, bpost does not require to send other data while asking for prices;
        # they simply return a price grid for all activated products for this account.
        code, response = self._send_request('rate', None, carrier)
        if code == 401 and response:
            # If the authentication fails, the server returns plain HTML instead of XML
            error_page = html.fromstring(response)
            error_message = error_page.body.text_content()
            raise UserError(_("Authentication error -- wrong credentials\n(Detailed error: %s)") % error_message)
        else:
            xml_response = etree.fromstring(response)

        # Find price by product and country
        price = 0.0
        ns = {'ns1': 'http://schema.post.be/shm/deepintegration/v3/'}
        bpost_delivery_type = carrier.bpost_domestic_deliver_type if carrier.bpost_delivery_nature == 'Domestic' else carrier.bpost_international_deliver_type
        for delivery_method in xml_response.findall('ns1:deliveryMethod/[@name="home or office"]/ns1:product/[@name="%s"]/ns1:price' % bpost_delivery_type, ns):
            if delivery_method.attrib['countryIso2Code'] == country.code:
                price = float(self._get_price_by_weight(_grams(weight), delivery_method))/100
                sale_price_digits = carrier.env['decimal.precision'].precision_get('Product Price')
                price = float_round(price, precision_digits=sale_price_digits)
        if not price:
            raise UserError(_("bpost did not return prices for this destination country."))

        # If delivery on saturday is enabled, there are additional fees
        additional_fees = 0.0
        if carrier.bpost_saturday is True:
            for option_price in xml_response.findall('ns1:deliveryMethod/[@name="home or office"]/ns1:product/[@name="%s"]/ns1:option/[@name="Saturday"]' % bpost_delivery_type, ns):
                additional_fees = float(option_price.attrib['price'])

        return price + additional_fees

    def _get_price_by_weight(self, weight, price):
        if weight <= 2000:
            return price.attrib['priceLessThan2']
        elif weight <= 5000:
            return price.attrib['price2To5']
        elif weight <= 10000:
            return price.attrib['price5To10']
        elif weight <= 20000:
            return price.attrib['price10To20']
        elif weight <= 30000:
            return price.attrib['price20To30']
        else:
            raise UserError(_("Packages over 30 Kg are not accepted by bpost."))

    def send_shipping(self, picking, carrier):
        # Get price of label
        shipping_weight_in_kg = carrier._bpost_convert_weight(picking.shipping_weight)
        price = self._get_rate(carrier, shipping_weight_in_kg, picking.partner_id.country_id)

        # Announce shipment to bpost
        reference_id = str(picking.name.replace("/", "", 2))[:50]
        ss, sn = self._parse_address(picking.company_id)
        rs, rn = self._parse_address(picking.partner_id)
        values = {'accountId': carrier.sudo().bpost_account_number,
                  'reference': reference_id,
                  'sender': {'_record': picking.company_id,
                             'streetName': ss,
                             'number': sn,
                             },
                  'receiver': {'_record': picking.partner_id,
                               'company': picking.partner_id.commercial_partner_id.name if picking.partner_id.commercial_partner_id != picking.partner_id else '',
                               'streetName': rs,
                               'number': rn,
                               },
                  'is_domestic': carrier.bpost_delivery_nature == 'Domestic',
                  'weight': str(_grams(shipping_weight_in_kg)),
                  # domestic
                  'product': carrier.bpost_domestic_deliver_type,
                  'saturday': carrier.bpost_saturday,
                  # international
                  'international_product': carrier.bpost_international_deliver_type,
                  'parcelValue': max(min(int(picking.sale_id.amount_total), 2500000), 100),           # according to bpost, 100 <= parcelValue <= 2500000
                  'contentDescription': ' '.join([
                     "%d %s" % (line.product_qty, re.sub('[\W_]+', '', line.product_id.name or '')) for line in picking.move_line_ids
                  ])[:50],
                  'shipmentType': carrier.bpost_shipment_type,
                  'parcelReturnInstructions': carrier.bpost_parcel_return_instructions,
                  }
        xml = carrier.env['ir.qweb'].render('delivery_bpost.bpost_shipping_request', values)
        code, response = self._send_request('send', xml, carrier)
        if code != 201 and response:
            try:
                root = etree.fromstring(response)
                ns = {'ns1': 'http://schema.post.be/shm/deepintegration/v3/'}
                for errors_return in root.findall("ns1:error", ns):
                    raise UserError(errors_return.text)
            except etree.ParseError:
                    raise UserError(response)

        # Grab printable label and tracking code
        code, response2 = self._send_request('label', None, carrier, reference=reference_id)
        root = etree.fromstring(response2)
        ns = {'ns1': 'http://schema.post.be/shm/deepintegration/v3/'}
        for labels in root.findall('ns1:label', ns):
            tracking_code = labels.find("ns1:barcode", ns).text
            databytes = labels.find("ns1:bytes", ns).text
            label = databytes

        return {'price': price, 'tracking_code': tracking_code, 'label': a2b_base64(label)}

    def _send_request(self, action, xml, carrier, reference=None):
        supercarrier = carrier.sudo()
        passphrase = supercarrier._bpost_passphrase()
        METHODS = {'rate': 'GET',
                   'send': 'POST',
                   'label': 'GET'}
        HEADERS = {'rate': {'authorization': 'Basic %s' % passphrase,
                            'accept': 'application/vnd.bpost.shm-productConfiguration-v3.1+XML'},
                   'send': {'authorization': 'Basic %s' % passphrase,
                            'content-Type': 'application/vnd.bpost.shm-order-v3.3+XML'},
                   'label': {'authorization': 'Basic %s' % passphrase,
                             'accept': 'application/vnd.bpost.shm-label-%s-v3+XML' % ('pdf' if carrier.bpost_label_format == 'PDF' else 'image'),
                             'content-Type': 'application/vnd.bpost.shm-labelRequest-v3+XML'}}
        URLS = {'rate': url_join(self.base_url, '%s/productconfig' % supercarrier.bpost_account_number),
                'send': url_join(self.base_url, '%s/orders' % supercarrier.bpost_account_number),
                'label': url_join(self.base_url, '%s/orders/%s/labels/%s' % (supercarrier.bpost_account_number, reference, carrier.bpost_label_stock_type))}

        self.debug_logger("%s\n%s\n%s" % (URLS[action], HEADERS[action], xml.decode('utf-8') if xml else None), 'bpost_request_%s' % action)
        response = requests.request(METHODS[action], URLS[action], headers=HEADERS[action], data=xml)
        self.debug_logger("%s\n%s" % (response.status_code, response.text), 'bpost_response_%s' % action)

        return response.status_code, response.text
