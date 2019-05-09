# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import suds
import re
import requests

from suds.client import Client

from odoo import modules

_logger = logging.getLogger(__name__)


class TaxCloudRequest(object):
    """ Low-level object intended to interface Odoo recordsets with TaxCloud,
        through appropriate SOAP requests """

    def __init__(self, api_id, api_key):
        wsdl_path = modules.get_module_path('account_taxcloud') + '/api/taxcloud.wsdl'
        self.client = Client('file:///%s' % wsdl_path)
        self.api_login_id = api_id
        self.api_key = api_key

    def verify_address(self, partner):
        # Ensure that the partner address is as accurate as possible (with zip4 field for example)  
        zip_match = re.match(r"^\D*(\d{5})\D*(\d{4})?", partner.zip or '')
        zips = list(zip_match.groups()) if zip_match else []
        address_to_verify = {
            'apiLoginID': self.api_login_id,
            'apiKey': self.api_key,
            'Address1': partner.street or '',
            'Address2': partner.street2 or '',
            'City': partner.city,
            "State": partner.state_id.code,
            "Zip5": zips.pop(0) if zips else '',
            "Zip4": zips.pop(0) if zips else '',
        }
        res = requests.post("https://api.taxcloud.com/1.0/TaxCloud/VerifyAddress", data=address_to_verify).json()
        if int(res.get('ErrNumber', False)):
            # If VerifyAddress fails, use Lookup with the initial address
            res.update(address_to_verify)
        return res

    def set_location_origin_detail(self, shipper):
        address = self.verify_address(shipper)
        self.origin = self.client.factory.create('Address')
        self.origin.Address1 = address['Address1'] or ''
        self.origin.Address2 = address['Address2'] or ''
        self.origin.City = address['City']
        self.origin.State = address['State']
        self.origin.Zip5 = address['Zip5']
        self.origin.Zip4 = address['Zip4']

    def set_location_destination_detail(self, recipient_partner):
        address = self.verify_address(recipient_partner)
        self.destination = self.client.factory.create('Address')
        self.destination.Address1 = address['Address1'] or ''
        self.destination.Address2 = address['Address2'] or ''
        self.destination.City = address['City']
        self.destination.State = address['State']
        self.destination.Zip5 = address['Zip5']
        self.destination.Zip4 = address['Zip4']

    def set_items_detail(self, product_id, tic_code):
        self.cart_items = self.client.factory.create('ArrayOfCartItem')
        self.cart_item = self.client.factory.create('CartItem')
        self.cart_item.Index = 1
        self.cart_item.ItemID = product_id
        if tic_code:
            self.cart_item.TIC = tic_code
        # Send fixed price 100$ and Qty 1 to calculate percentage based on amount returned.
        self.cart_item.Price = 100
        self.cart_item.Qty = 1
        self.cart_items.CartItem = [self.cart_item]

    def set_invoice_items_detail(self, invoice):
        self.customer_id = invoice.partner_id.id
        self.cart_id = invoice.id
        self.cart_items = self.client.factory.create('ArrayOfCartItem')
        cart_items = []
        for index, line in enumerate(invoice.invoice_line_ids):
            if line.price_unit >= 0.0 and line.quantity >= 0.0:
                product_id = line.product_id.id
                tic_code = line.product_id.tic_category_id.code or \
                    line.product_id.categ_id.tic_category_id.code or \
                    line.company_id.tic_category_id.code or \
                    line.env.user.company_id.tic_category_id.code
                qty = line.quantity
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

                cart_item = self.client.factory.create('CartItem')
                cart_item.Index = index
                cart_item.ItemID = product_id
                if tic_code:
                    cart_item.TIC = tic_code
                cart_item.Price = price_unit
                cart_item.Qty = qty
                cart_items.append(cart_item)
        self.cart_items.CartItem = cart_items

    # def authorize_transaction(self, invoice):

    def get_all_taxes_values(self):
        formatted_response = {}
        try:
            response = self.client.service.Lookup(
                self.api_login_id,
                self.api_key,
                hasattr(self, 'customer_id') and self.customer_id or 'NoCustomerID',
                hasattr(self, 'cart_id') and self.cart_id or 'NoCartID',
                self.cart_items,
                self.origin,
                self.destination,
                False
            )
            formatted_response['response'] = response
            if response.ResponseType == 'OK':
                formatted_response['values'] = {}
                for item in response.CartItemsResponse.CartItemResponse:
                    index = item.CartItemIndex
                    tax_amount = item.TaxAmount
                    formatted_response['values'][index] = tax_amount
            elif response.ResponseType == 'Error':
                formatted_response['error_message'] = response.Messages[0][0].Message
        except suds.WebFault as fault:
            formatted_response['error_message'] = fault
        except IOError:
            formatted_response['error_message'] = "TaxCloud Server Not Found"
        return formatted_response

    # Get TIC category on synchronize.
    def get_tic_category(self):
        formatted_response = {}
        try:
            self.response = self.client.service.GetTICs(self.api_login_id, self.api_key)
            if self.response.ResponseType == 'OK':
                formatted_response['data'] = self.response.TICs[0]
            elif self.response.ResponseType == 'Error':
                formatted_response['error_message'] = self.response.Messages[0][0].Message
        except suds.WebFault as fault:
            formatted_response['error_message'] = fault
        except IOError:
            formatted_response['error_message'] = "TaxCloud Server Not Found"

        return formatted_response
