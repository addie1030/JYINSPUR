# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import time
from math import ceil
from xml.etree import ElementTree as etree
import unicodedata

import requests

from odoo import _
from odoo.exceptions import UserError


class DHLProvider():

    def __init__(self, prod_environment, debug_logger):
        self.debug_logger = debug_logger
        if not prod_environment:
            self.url = 'https://xmlpitest-ea.dhl.com/XMLShippingServlet?isUTF8Support=true'
        else:
            self.url = 'https://xmlpi-ea.dhl.com/XMLShippingServlet?isUTF8Support=true'

    def _get_rate_param(self, order, carrier):
        res = {}
        total_weight = carrier._dhl_convert_weight(sum([(line.product_id.weight * line.product_qty) for line in order.order_line]), carrier.dhl_package_weight_unit)
        max_weight = carrier._dhl_convert_weight(carrier.dhl_default_packaging_id.max_weight, carrier.dhl_package_weight_unit)

        res = {
            'carrier': carrier,
            'shipper_partner': order.warehouse_id.partner_id,
            'Date': time.strftime('%Y-%m-%d'),
            'ReadyTime': time.strftime('PT%HH%MM'),
            'recipient_partner': order.partner_shipping_id,
            'total_weight': total_weight,
            'currency_name': order.currency_id.name,
            'total_value': str(sum([(line.price_unit * line.product_uom_qty) for line in order.order_line.filtered(lambda line: not line.is_delivery)])),
            'is_dutiable': carrier.dhl_dutiable,
            'package_ids': False,
        }
        if max_weight and total_weight > max_weight:
            total_package = int(ceil(total_weight / max_weight))
            last_package_weight = total_weight % max_weight
            res['total_packages'] = total_package
            res['last_package_weight'] = last_package_weight
            res['package_ids'] = carrier.dhl_default_packaging_id
        return res

    def rate_request(self, order, carrier):
        dict_response = {'price': 0.0,
                         'currency': False,
                         'error_found': False}

        param = self._get_rate_param(order, carrier)
        request_text = self._create_rate_xml(param)
        try:
            root = self._send_request(request_text)
        except UserError as e:
            dict_response['error_found'] = e.message
            return dict_response

        if root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition')
            dict_response['error_found'] = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            return dict_response

        elif root.tag == '{http://www.dhl.com}DCTResponse':
            condition = root.findall('GetQuoteResponse/Note/Condition')
            if condition:
                dict_response['error_found'] = "%s: %s" % (condition[0][0].text, condition[0][1].text)
                return dict_response

            products = root.findall('GetQuoteResponse/BkgDetails/QtdShp')
            found = False
            for product in products:
                if product.findtext('GlobalProductCode') == carrier.dhl_product_code\
                        and product.findall('ShippingCharge'):
                    dict_response['price'] = product.findall('ShippingCharge')[0].text
                    dict_response['currency'] = product.findall('QtdSInAdCur/CurrencyCode')[0].text
                    found = True
            if not found:
                dict_response['error_found'] = _("No shipping available for the selected DHL product")
            return dict_response

    def _get_send_param(self, picking, carrier):
        return {
            # it's if you want to track the message numbers
            'MessageTime': '2001-12-17T09:30:47-05:00',
            'MessageReference': '1234567890123456789012345678901',
            'carrier': carrier,
            'RegionCode': carrier.dhl_region_code,
            'lang': 'en',
            'recipient_partner': picking.partner_id,
            'PiecesEnabled': 'Y',
            # Hard coded, S for Shipper, R for Recipient and T for Third Party
            'ShippingPaymentType': 'S',
            'recipient_streetLines': ('%s%s') % (picking.partner_id.street or '',
                                                 picking.partner_id.street2 or ''),
            'NumberOfPieces': len(picking.package_ids) or 1,
            'weight_bulk': carrier._dhl_convert_weight(picking.weight_bulk, carrier.dhl_package_weight_unit),
            'package_ids': picking.package_ids,
            'total_weight': carrier._dhl_convert_weight(picking.shipping_weight, carrier.dhl_package_weight_unit),
            'weight_unit': carrier.dhl_package_weight_unit[:1],
            'dimension_unit': carrier.dhl_package_dimension_unit[0],
            # For the rating API waits for CM and IN here for C and I...
            'GlobalProductCode': carrier.dhl_product_code,
            'Date': time.strftime('%Y-%m-%d'),
            'shipper_partner': picking.picking_type_id.warehouse_id.partner_id,
            'shipper_company': picking.company_id,
            'shipper_streetLines': ('%s%s') % (picking.picking_type_id.warehouse_id.partner_id.street or '',
                                               picking.picking_type_id.warehouse_id.partner_id.street2 or ''),
            'LabelImageFormat': carrier.dhl_label_image_format,
            'LabelTemplate': carrier.dhl_label_template,
            'is_dutiable': carrier.dhl_dutiable,
            'currency_name': picking.sale_id.currency_id.name or picking.company_id.currency_id.name,
            'total_value': str(sum([line.product_id.lst_price * int(line.product_uom_qty) for line in picking.move_lines]))
        }

    def _get_send_param_final_rating(self, picking, carrier):
        return {
            'carrier': carrier,
            'shipper_partner': picking.picking_type_id.warehouse_id.partner_id,
            'Date': time.strftime('%Y-%m-%d'),
            'ReadyTime': time.strftime('PT%HH%MM'),
            'recipient_partner': picking.partner_id,
            'currency_name': picking.sale_id.currency_id.name or picking.company_id.currency_id.name,
            'total_value': str(sum([line.product_id.lst_price * int(line.product_uom_qty) for line in picking.move_lines])),
            'is_dutiable': carrier.dhl_dutiable,
            'package_ids': picking.package_ids,
            'total_weight': carrier._dhl_convert_weight(picking.weight_bulk, carrier.dhl_package_weight_unit),
        }

    def send_shipping(self, picking, carrier):
        dict_response = {'tracking_number': 0.0,
                         'price': 0.0,
                         'currency': False}

        param = self._get_send_param(picking, carrier)
        request_text = self._create_shipping_xml(param)

        root = self._send_request(request_text)
        if root.tag == '{http://www.dhl.com}ShipmentValidateErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            error_msg = "%s: %s" % (condition[1].text, condition[0].text)
            raise UserError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            if isinstance(condition[0], list):
                error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            else:
                error_msg = "%s: %s" % (condition[0].text, condition[1].text)
            raise UserError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}ShipmentResponse':
            label_image = root.findall('LabelImage')
            self.label = label_image[0].findall('OutputImage')[0].text
            dict_response['tracking_number'] = root.findtext('AirwayBillNumber')

        # Warning sometimes the ShipmentRequest returns a shipping rate, not everytime.
        # After discussing by mail with the DHL Help Desk, they said that the correct rate
        # is given by the DCTRequest GetQuote.

        param_final_rating = self._get_send_param_final_rating(picking, carrier)
        request_text = self._create_rate_xml(param_final_rating)
        root = self._send_request(request_text)
        if root.tag == '{http://www.dhl.com}ErrorResponse':
            condition = root.findall('Response/Status/Condition/')
            error_msg = "%s: %s" % (condition[0][0].text, condition[0][1].text)
            raise UserError(_(error_msg))
        elif root.tag == '{http://www.dhl.com}DCTResponse':
            products = root.findall('GetQuoteResponse/BkgDetails/QtdShp')
            found = False
            for product in products:
                if product.findtext('GlobalProductCode') == carrier.dhl_product_code\
                        and product.findall('ShippingCharge'):
                    dict_response['price'] = product.findall('ShippingCharge')[0].text
                    dict_response['currency'] = product.findall('QtdSInAdCur/CurrencyCode')[0].text
                    found = True
            if not found:
                raise UserError(_("No service available for the selected product"))

        return dict_response

    def save_label(self):
        label_binary_data = binascii.a2b_base64(self.label)
        return label_binary_data

    def send_cancelling(self, picking, carrier):
        dict_response = {'tracking_number': 0.0, 'price': 0.0, 'currency': False}
        return dict_response

    def _send_request(self, request_xml):
        try:
            self.debug_logger(request_xml, 'dhl_request')
            req = requests.post(self.url, data=request_xml, headers={'Content-Type': 'application/xml'})
            req.raise_for_status()
            response_text = req.content
            self.debug_logger(response_text, 'dhl_response')
        except IOError:
            raise UserError("DHL Server not found. Check your connectivity.")
        root = etree.fromstring(response_text.decode(encoding="utf-8"))
        return root

    def _create_rate_xml(self, param):
        carrier = param["carrier"].sudo()
        etree.register_namespace("req", "http://www.dhl.com")
        root = etree.Element("{http://www.dhl.com}DCTRequest")
        get_quote_node = etree.SubElement(root, "GetQuote")
        service_header_node = etree.SubElement(get_quote_node, "Request")
        service_header_node = etree.SubElement(service_header_node, "ServiceHeader")
        etree.SubElement(service_header_node, "SiteID").text = carrier.dhl_SiteID
        etree.SubElement(service_header_node, "Password").text = carrier.dhl_password

        from_node = etree.SubElement(get_quote_node, "From")
        etree.SubElement(from_node, "CountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(from_node, "Postalcode").text = param["shipper_partner"].zip
        etree.SubElement(from_node, "City").text = param["shipper_partner"].city

        bkg_details_node = etree.SubElement(get_quote_node, "BkgDetails")
        etree.SubElement(bkg_details_node, "PaymentCountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(bkg_details_node, "Date").text = param["Date"]
        etree.SubElement(bkg_details_node, "ReadyTime").text = param["ReadyTime"]
        etree.SubElement(bkg_details_node, "DimensionUnit").text = carrier.dhl_package_dimension_unit
        etree.SubElement(bkg_details_node, "WeightUnit").text = carrier.dhl_package_weight_unit
        pieces_node = etree.SubElement(bkg_details_node, "Pieces")
        if param["package_ids"] and not param.get('total_packages'):
            for index, package in enumerate(param["package_ids"], start=1):
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(index)
                packaging = package.packaging_id or carrier.dhl_default_packaging_id
                etree.SubElement(piece_node, "PackageTypeCode").text = packaging.shipper_package_code
                etree.SubElement(piece_node, "Height").text = str(packaging.height)
                etree.SubElement(piece_node, "Depth").text = str(packaging.length)
                etree.SubElement(piece_node, "Width").text = str(packaging.width)
                etree.SubElement(piece_node, "Weight").text = str(package.shipping_weight)
        elif param['package_ids'] and param.get('total_packages'):
            package = param['package_ids']
            for seq in range(1, param['total_packages'] + 1):
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(seq)
                etree.SubElement(piece_node, "PackageTypeCode").text = package.shipper_package_code
                etree.SubElement(piece_node, "Height").text = str(package.height)
                etree.SubElement(piece_node, "Depth").text = str(package.length)
                etree.SubElement(piece_node, "Width").text = str(package.width)
                if seq == param['total_packages'] and param['last_package_weight']:
                    etree.SubElement(piece_node, "Weight").text = str(param['last_package_weight'])
                else:
                    etree.SubElement(piece_node, "Weight").text = str(package.max_weight)
        else:
            piece_node = etree.SubElement(pieces_node, "Piece")
            etree.SubElement(piece_node, "PieceID").text = str(1)
            packaging = carrier.dhl_default_packaging_id
            etree.SubElement(piece_node, "PackageTypeCode").text = packaging.shipper_package_code
            etree.SubElement(piece_node, "Height").text = str(packaging.height)
            etree.SubElement(piece_node, "Depth").text = str(packaging.length)
            etree.SubElement(piece_node, "Width").text = str(packaging.width)
            etree.SubElement(piece_node, "Weight").text = str(param["total_weight"])

        etree.SubElement(bkg_details_node, "PaymentAccountNumber").text = carrier.dhl_account_number
        if param["is_dutiable"]:
            etree.SubElement(bkg_details_node, "IsDutiable").text = "Y"
        else:
            etree.SubElement(bkg_details_node, "IsDutiable").text = "N"
        etree.SubElement(bkg_details_node, "NetworkTypeCode").text = 'AL'
        to_node = etree.SubElement(get_quote_node, "To")
        etree.SubElement(to_node, "CountryCode").text = param["recipient_partner"].country_id.code
        etree.SubElement(to_node, "Postalcode").text = param["recipient_partner"].zip
        etree.SubElement(to_node, "City").text = param["recipient_partner"].city

        if param["is_dutiable"]:
            dutiable_node = etree.SubElement(get_quote_node, "Dutiable")
            etree.SubElement(dutiable_node, "DeclaredCurrency").text = param["currency_name"]
            etree.SubElement(dutiable_node, "DeclaredValue").text = param["total_value"]
        return etree.tostring(root)

    def _create_shipping_xml(self, param):
        carrier = param["carrier"].sudo()
        etree.register_namespace("req", "http://www.dhl.com")
        root = etree.Element("{http://www.dhl.com}ShipmentRequest")
        root.attrib['schemaVersion'] = "1.0"
        root.attrib['xsi:schemaLocation'] = "http://www.dhl.com ship-val-global-req.xsd"
        root.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

        request_node = etree.SubElement(root, "Request")
        request_node = etree.SubElement(request_node, "ServiceHeader")
        etree.SubElement(request_node, "MessageTime").text = param["MessageTime"]
        etree.SubElement(request_node, "MessageReference").text = param["MessageReference"]
        etree.SubElement(request_node, "SiteID").text = carrier.dhl_SiteID
        etree.SubElement(request_node, "Password").text = carrier.dhl_password

        etree.SubElement(root, "RegionCode").text = param["RegionCode"]
        etree.SubElement(root, "RequestedPickupTime").text = "Y"

        etree.SubElement(root, "LanguageCode").text = param["lang"]
        etree.SubElement(root, "PiecesEnabled").text = param["PiecesEnabled"]

        billing_node = etree.SubElement(root, "Billing")
        etree.SubElement(billing_node, "ShipperAccountNumber").text = carrier.dhl_account_number
        etree.SubElement(billing_node, "ShippingPaymentType").text = param['ShippingPaymentType']
        if param["is_dutiable"]:
            etree.SubElement(billing_node, "DutyPaymentType").text = "S"

        consignee_node = etree.SubElement(root, "Consignee")
        if param["recipient_partner"].parent_id:
            etree.SubElement(consignee_node, "CompanyName").text = param["recipient_partner"].parent_id.name
        else:
            etree.SubElement(consignee_node, "CompanyName").text = param["recipient_partner"].name
        etree.SubElement(consignee_node, "AddressLine").text = param["recipient_streetLines"]
        etree.SubElement(consignee_node, "City").text = param["recipient_partner"].city

        if param["recipient_partner"].state_id:
            etree.SubElement(consignee_node, "Division").text = param["recipient_partner"].state_id.name
            etree.SubElement(consignee_node, "DivisionCode").text = param["recipient_partner"].state_id.code
        etree.SubElement(consignee_node, "PostalCode").text = param["recipient_partner"].zip
        etree.SubElement(consignee_node, "CountryCode").text = param["recipient_partner"].country_id.code
        etree.SubElement(consignee_node, "CountryName").text = param["recipient_partner"].country_id.name
        contact_node = etree.SubElement(consignee_node, "Contact")
        etree.SubElement(contact_node, "PersonName").text = param["recipient_partner"].name
        etree.SubElement(contact_node, "PhoneNumber").text = param["recipient_partner"].phone
        etree.SubElement(contact_node, "Email").text = param["recipient_partner"].email
        if param["is_dutiable"]:
            dutiable_node = etree.SubElement(root, "Dutiable")
            etree.SubElement(dutiable_node, "DeclaredValue").text = param["total_value"]
            etree.SubElement(dutiable_node, "DeclaredCurrency").text = param["currency_name"]

        shipment_details_node = etree.SubElement(root, "ShipmentDetails")
        etree.SubElement(shipment_details_node, "NumberOfPieces").text = str(param["NumberOfPieces"])
        pieces_node = etree.SubElement(shipment_details_node, "Pieces")
        if param["package_ids"]:
            # Multi-package
            for package in param["package_ids"]:
                piece_node = etree.SubElement(pieces_node, "Piece")
                etree.SubElement(piece_node, "PieceID").text = str(package.name)   # need to be removed
                packaging = package.packaging_id or carrier.dhl_default_packaging_id
                etree.SubElement(piece_node, "Width").text = str(packaging.width)
                etree.SubElement(piece_node, "Height").text = str(packaging.height)
                etree.SubElement(piece_node, "Depth").text = str(packaging.length)
                etree.SubElement(piece_node, "PieceContents").text = str(package.name)
        if param["weight_bulk"]:
            # Monopackage
            packaging = carrier.dhl_default_packaging_id
            piece_node = etree.SubElement(pieces_node, "Piece")
            etree.SubElement(piece_node, "PieceID").text = str(1)   # need to be removed
            etree.SubElement(piece_node, "Width").text = str(packaging.width)
            etree.SubElement(piece_node, "Height").text = str(packaging.height)
            etree.SubElement(piece_node, "Depth").text = str(packaging.length)
        etree.SubElement(shipment_details_node, "Weight").text = str(param["total_weight"])
        etree.SubElement(shipment_details_node, "WeightUnit").text = param["weight_unit"]
        etree.SubElement(shipment_details_node, "GlobalProductCode").text = param["GlobalProductCode"]
        etree.SubElement(shipment_details_node, "LocalProductCode").text = param["GlobalProductCode"]
        etree.SubElement(shipment_details_node, "Date").text = param["Date"]
        etree.SubElement(shipment_details_node, "Contents").text = "MY DESCRIPTION"
        etree.SubElement(shipment_details_node, "DimensionUnit").text = param["dimension_unit"]
        etree.SubElement(shipment_details_node, "CurrencyCode").text = param["currency_name"]

        shipper_node = etree.SubElement(root, "Shipper")
        etree.SubElement(shipper_node, "ShipperID").text = carrier.dhl_account_number
        etree.SubElement(shipper_node, "CompanyName").text = param["shipper_company"].name
        etree.SubElement(shipper_node, "AddressLine").text = param["shipper_streetLines"]
        etree.SubElement(shipper_node, "City").text = param["shipper_partner"].city
        etree.SubElement(shipper_node, "PostalCode").text = param["shipper_partner"].zip
        etree.SubElement(shipper_node, "CountryCode").text = param["shipper_partner"].country_id.code
        etree.SubElement(shipper_node, "CountryName").text = param["shipper_partner"].country_id.name

        contact_node = etree.SubElement(shipper_node, "Contact")
        etree.SubElement(contact_node, "PersonName").text = param["shipper_partner"].name
        etree.SubElement(contact_node, "PhoneNumber").text = param["shipper_partner"].phone

        etree.SubElement(root, "LabelImageFormat").text = param["LabelImageFormat"]

        label_node = etree.SubElement(root, "Label")
        etree.SubElement(label_node, "LabelTemplate").text = param["LabelTemplate"]
        return etree.tostring(root, encoding='utf-8')

    def check_required_value(self, carrier, recipient, shipper, order=False, picking=False):
        carrier = carrier.sudo()
        recipient_required_field = ['city', 'zip', 'country_id']
        if not carrier.dhl_SiteID:
            return _("DHL Site ID is missing, please modify your delivery method settings.")
        if not carrier.dhl_password:
            return _("DHL password is missing, please modify your delivery method settings.")
        if not carrier.dhl_account_number:
            return _("DHL account number is missing, please modify your delivery method settings.")

        if not recipient.street and not recipient.street2:
            recipient_required_field.append('street')
        res = [field for field in recipient_required_field if not recipient[field]]
        if res:
            return _("The address of the customer is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", "")

        shipper_required_field = ['city', 'zip', 'phone', 'country_id']
        if not shipper.street and not shipper.street2:
            shipper_required_field.append('street')

        res = [field for field in shipper_required_field if not shipper[field]]
        if res:
            return _("The address of your company warehouse is missing or wrong (Missing field(s) :\n %s)") % ", ".join(res).replace("_id", "")

        if order:
            if not order.order_line:
                return _("Please provide at least one item to ship.")
            for line in order.order_line.filtered(lambda line: not line.product_id.weight and not line.is_delivery and line.product_id.type not in ['service', 'digital']):
                return _('The estimated price cannot be computed because the weight of your product is missing.')
        return False
