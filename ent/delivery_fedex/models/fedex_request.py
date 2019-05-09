# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import binascii
import logging
import os
import suds  # should work with suds or its fork suds-jurko
import re

from datetime import datetime
from suds.client import Client
from suds.plugin import MessagePlugin


_logger = logging.getLogger(__name__)
# uncomment to enable logging of SOAP requests and responses
# logging.getLogger('suds.transport').setLevel(logging.DEBUG)


STATECODE_REQUIRED_COUNTRIES = ['US', 'CA', 'PR ', 'IN']


class LogPlugin(MessagePlugin):
    """ Small plugin for suds that catches out/ingoing XML requests and logs them"""
    def __init__(self, debug_logger):
        self.debug_logger = debug_logger

    def sending(self, context):
        self.debug_logger(context.envelope, 'fedex_request')

    def received(self, context):
        self.debug_logger(context.reply, 'fedex_response')

    def marshalled(self, context):
        context.envelope = context.envelope.prune()


class FedexRequest():
    """ Low-level object intended to interface Odoo recordsets with FedEx,
        through appropriate SOAP requests """

    def __init__(self, debug_logger, request_type="shipping", prod_environment=False, ):
        self.debug_logger = debug_logger
        self.hasCommodities = False
        self.hasOnePackage = False

        if request_type == "shipping":
            if not prod_environment:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/ShipService_v15.wsdl')
            else:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/prod/ShipService_v15.wsdl')
            self.start_shipping_transaction(wsdl_path)

        elif request_type == "rating":
            if not prod_environment:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/test/RateService_v16.wsdl')
            else:
                wsdl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../api/prod/RateService_v16.wsdl')
            self.start_rating_transaction(wsdl_path)

    # Authentification stuff

    def web_authentication_detail(self, key, password):
        WebAuthenticationCredential = self.client.factory.create('WebAuthenticationCredential')
        WebAuthenticationCredential.Key = key
        WebAuthenticationCredential.Password = password
        self.WebAuthenticationDetail = self.client.factory.create('WebAuthenticationDetail')
        self.WebAuthenticationDetail.UserCredential = WebAuthenticationCredential

    def transaction_detail(self, transaction_id):
        self.TransactionDetail = self.client.factory.create('TransactionDetail')
        self.TransactionDetail.CustomerTransactionId = transaction_id

    def client_detail(self, account_number, meter_number):
        self.ClientDetail = self.client.factory.create('ClientDetail')
        self.ClientDetail.AccountNumber = account_number
        self.ClientDetail.MeterNumber = meter_number

    # Common stuff

    def set_shipper(self, company_partner, warehouse_partner):
        Contact = self.client.factory.create('Contact')
        Contact.PersonName = company_partner.name if not company_partner.is_company else ''
        Contact.CompanyName = company_partner.name if company_partner.is_company else ''
        Contact.PhoneNumber = warehouse_partner.phone or ''
        # TODO fedex documentation asks for TIN number, but it seems to work without

        Address = self.client.factory.create('Address')
        Address.StreetLines = [warehouse_partner.street or '', warehouse_partner.street2 or '']
        Address.City = warehouse_partner.city or ''
        if warehouse_partner.country_id.code in STATECODE_REQUIRED_COUNTRIES:
            Address.StateOrProvinceCode = warehouse_partner.state_id.code or ''
        else:
            Address.StateOrProvinceCode = ''
        Address.PostalCode = warehouse_partner.zip or ''
        Address.CountryCode = warehouse_partner.country_id.code or ''

        self.RequestedShipment.Shipper.Contact = Contact
        self.RequestedShipment.Shipper.Address = Address

    def set_recipient(self, recipient_partner):
        Contact = self.client.factory.create('Contact')
        if recipient_partner.is_company:
            Contact.PersonName = ''
            Contact.CompanyName = recipient_partner.name
        else:
            Contact.PersonName = recipient_partner.name
            Contact.CompanyName = recipient_partner.parent_id.name or ''
        Contact.PhoneNumber = recipient_partner.phone or ''

        Address = self.client.factory.create('Address')
        Address.StreetLines = [recipient_partner.street or '', recipient_partner.street2 or '']
        Address.City = recipient_partner.city or ''
        if recipient_partner.country_id.code in STATECODE_REQUIRED_COUNTRIES:
            Address.StateOrProvinceCode = recipient_partner.state_id.code or ''
        else:
            Address.StateOrProvinceCode = ''
        Address.PostalCode = recipient_partner.zip or ''
        Address.CountryCode = recipient_partner.country_id.code or ''

        self.RequestedShipment.Recipient.Contact = Contact
        self.RequestedShipment.Recipient.Address = Address

    def shipment_request(self, dropoff_type, service_type, packaging_type, overall_weight_unit, saturday_delivery):
        self.RequestedShipment = self.client.factory.create('RequestedShipment')
        self.RequestedShipment.ShipTimestamp = datetime.now()
        self.RequestedShipment.DropoffType = dropoff_type
        self.RequestedShipment.ServiceType = service_type
        self.RequestedShipment.PackagingType = packaging_type
        # Resuest estimation of duties and taxes for international shipping
        if service_type in ['INTERNATIONAL_ECONOMY', 'INTERNATIONAL_PRIORITY']:
            self.RequestedShipment.EdtRequestType = 'ALL'
        else:
            self.RequestedShipment.EdtRequestType = 'NONE'
        self.RequestedShipment.PackageCount = 0
        self.RequestedShipment.TotalWeight.Units = overall_weight_unit
        self.RequestedShipment.TotalWeight.Value = 0
        self.listCommodities = []
        if saturday_delivery:
            timestamp_day = self.RequestedShipment.ShipTimestamp.strftime("%A")
            if (service_type == 'FEDEX_2_DAY' and timestamp_day == 'Thursday') or (service_type in ['PRIORITY_OVERNIGHT', 'FIRST_OVERNIGHT', 'INTERNATIONAL_PRIORITY'] and timestamp_day == 'Friday'):
                SpecialServiceTypes = self.client.factory.create('ShipmentSpecialServiceType')
                self.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes = [SpecialServiceTypes.SATURDAY_DELIVERY]

    def set_currency(self, currency):
        self.RequestedShipment.PreferredCurrency = currency
        # self.RequestedShipment.RateRequestTypes = 'PREFERRED'

    def set_master_package(self, total_weight, package_count, master_tracking_id=False):
        self.RequestedShipment.TotalWeight.Value = total_weight
        self.RequestedShipment.PackageCount = package_count
        if master_tracking_id:
            self.RequestedShipment.MasterTrackingId = self.client.factory.create('TrackingId')
            self.RequestedShipment.MasterTrackingId.TrackingIdType = 'FEDEX'
            self.RequestedShipment.MasterTrackingId.TrackingNumber = master_tracking_id

    def add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping'):
        # TODO remove in master and change the signature of a public method
        return self._add_package(weight_value=weight_value, package_code=package_code, package_height=package_height, package_width=package_width,
                                 package_length=package_length, sequence_number=sequence_number, mode=mode, po_number=False, dept_number=False)

    def _add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping', po_number=False, dept_number=False):
        package = self.client.factory.create('RequestedPackageLineItem')
        package_weight = self.client.factory.create('Weight')
        package_weight.Value = weight_value
        package_weight.Units = self.RequestedShipment.TotalWeight.Units

        package.PhysicalPackaging = 'BOX'
        if package_code == 'YOUR_PACKAGING':
            package.Dimensions.Height = package_height
            package.Dimensions.Width = package_width
            package.Dimensions.Length = package_length
            # TODO in master, add unit in product packaging and perform unit conversion
            package.Dimensions.Units = "IN" if self.RequestedShipment.TotalWeight.Units == 'LB' else 'CM'
        if po_number:
            po_reference = self.client.factory.create('CustomerReference')
            po_reference.CustomerReferenceType = 'P_O_NUMBER'
            po_reference.Value = po_number
            package.CustomerReferences.append(po_reference)
        if dept_number:
            dept_reference = self.client.factory.create('CustomerReference')
            dept_reference.CustomerReferenceType = 'DEPARTMENT_NUMBER'
            dept_reference.Value = dept_number
            package.CustomerReferences.append(dept_reference)

        package.Weight = package_weight
        if mode == 'rating':
            package.GroupPackageCount = 1
        if sequence_number:
            package.SequenceNumber = sequence_number
        else:
            self.hasOnePackage = True

        if mode == 'rating':
            self.RequestedShipment.RequestedPackageLineItems.append(package)
        else:
            self.RequestedShipment.RequestedPackageLineItems = package

    # Rating stuff

    def start_rating_transaction(self, wsdl_path):
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[LogPlugin(self.debug_logger)])
        self.VersionId = self.client.factory.create('VersionId')
        self.VersionId.ServiceId = 'crs'
        self.VersionId.Major = '16'
        self.VersionId.Intermediate = '0'
        self.VersionId.Minor = '0'

    def rate(self):
        formatted_response = {'price': {}}
        del self.ClientDetail.Region
        if self.hasCommodities:
            self.RequestedShipment.CustomsClearanceDetail.Commodities = self.listCommodities

        try:
            self.response = self.client.service.getRates(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                         ClientDetail=self.ClientDetail,
                                                         TransactionDetail=self.TransactionDetail,
                                                         Version=self.VersionId,
                                                         RequestedShipment=self.RequestedShipment)
            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                if not getattr(self.response, "RateReplyDetails", False):
                    raise Exception("No rating found")
                for rating in self.response.RateReplyDetails[0].RatedShipmentDetails:
                    formatted_response['price'][rating.ShipmentRateDetail.TotalNetFedExCharge.Currency] = rating.ShipmentRateDetail.TotalNetFedExCharge.Amount
                if len(self.response.RateReplyDetails[0].RatedShipmentDetails) == 1:
                    if 'CurrencyExchangeRate' in self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail:
                        formatted_response['price'][self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.FromCurrency] = self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.TotalNetFedExCharge.Amount / self.response.RateReplyDetails[0].RatedShipmentDetails[0].ShipmentRateDetail.CurrencyExchangeRate.Rate
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"
        except Exception as e:
            formatted_response['errors_message'] = e.args[0]

        return formatted_response

    # Shipping stuff

    def start_shipping_transaction(self, wsdl_path):
        self.client = Client('file:///%s' % wsdl_path.lstrip('/'), plugins=[LogPlugin(self.debug_logger)])
        self.VersionId = self.client.factory.create('VersionId')
        self.VersionId.ServiceId = 'ship'
        self.VersionId.Major = '15'
        self.VersionId.Intermediate = '0'
        self.VersionId.Minor = '0'

    def shipment_label(self, label_format_type, image_type, label_stock_type, label_printing_orientation, label_order):
        LabelSpecification = self.client.factory.create('LabelSpecification')
        LabelSpecification.LabelFormatType = label_format_type
        LabelSpecification.ImageType = image_type
        LabelSpecification.LabelStockType = label_stock_type
        LabelSpecification.LabelPrintingOrientation = label_printing_orientation
        LabelSpecification.LabelOrder = label_order
        self.RequestedShipment.LabelSpecification = LabelSpecification

    def shipping_charges_payment(self, shipping_charges_payment_account):
        self.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'
        Payor = self.client.factory.create('Payor')
        Payor.ResponsibleParty.AccountNumber = shipping_charges_payment_account
        self.RequestedShipment.ShippingChargesPayment.Payor = Payor

    def duties_payment(self, responsible_party_country_code, responsible_account_number):
        self.RequestedShipment.CustomsClearanceDetail.DutiesPayment.PaymentType = 'SENDER'
        Payor = self.client.factory.create('Payor')
        Payor.ResponsibleParty.Address.CountryCode = responsible_party_country_code
        Payor.ResponsibleParty.AccountNumber = responsible_account_number
        self.RequestedShipment.CustomsClearanceDetail.DutiesPayment.Payor = Payor

    def customs_value(self, customs_value_currency, customs_value_amount, document_content):
        self.RequestedShipment.CustomsClearanceDetail = self.client.factory.create('CustomsClearanceDetail')
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency = customs_value_currency
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount = customs_value_amount
        if self.RequestedShipment.Shipper.Address.CountryCode == "IN" and self.RequestedShipment.Recipient.Address.CountryCode == "IN":
            self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.Purpose = 'SOLD'
            del self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.TaxesOrMiscellaneousChargeType

        # Old keys not requested anymore but still in WSDL; not removing them causes crash
        del self.RequestedShipment.CustomsClearanceDetail.ClearanceBrokerage
        del self.RequestedShipment.CustomsClearanceDetail.FreightOnValue

        self.RequestedShipment.CustomsClearanceDetail.DocumentContent = document_content

    def commodities(self, commodity_currency, commodity_amount, commodity_number_of_piece, commodity_weight_units,
                    commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity,
                    commodity_quantity_units):
        return self._commodities(commodity_currency, commodity_amount, commodity_number_of_piece, commodity_weight_units,
                        commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity,
                        commodity_quantity_units, '')

    def _commodities(self, commodity_currency, commodity_amount, commodity_number_of_piece, commodity_weight_units,
                    commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity,
                    commodity_quantity_units, commodity_harmonized_code):
        self.hasCommodities = True
        commodity = self.client.factory.create('Commodity')
        commodity.UnitPrice.Currency = commodity_currency
        commodity.UnitPrice.Amount = commodity_amount
        commodity.NumberOfPieces = commodity_number_of_piece
        commodity.CountryOfManufacture = commodity_country_of_manufacture

        commodity_weight = self.client.factory.create('Weight')
        commodity_weight.Value = commodity_weight_value
        commodity_weight.Units = commodity_weight_units

        commodity.Weight = commodity_weight
        commodity.Description = re.sub(r'[\[\]<>;={}"|]', '', commodity_description)
        commodity.Quantity = commodity_quantity
        commodity.QuantityUnits = commodity_quantity_units
        commodity.CustomsValue.Currency = commodity_currency
        commodity.CustomsValue.Amount = commodity_quantity * commodity_amount

        commodity.HarmonizedCode = commodity_harmonized_code

        self.listCommodities.append(commodity)

    def process_shipment(self):
        if self.hasCommodities:
            self.RequestedShipment.CustomsClearanceDetail.Commodities = self.listCommodities
        formatted_response = {'tracking_number': 0.0,
                              'price': {},
                              'master_tracking_id': None}

        try:
            self.response = self.client.service.processShipment(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                                ClientDetail=self.ClientDetail,
                                                                TransactionDetail=self.TransactionDetail,
                                                                Version=self.VersionId,
                                                                RequestedShipment=self.RequestedShipment)

            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                formatted_response['tracking_number'] = self.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber

                if (self.RequestedShipment.RequestedPackageLineItems.SequenceNumber == self.RequestedShipment.PackageCount) or self.hasOnePackage:
                    if 'ShipmentRating' in self.response.CompletedShipmentDetail:
                        for rating in self.response.CompletedShipmentDetail.ShipmentRating.ShipmentRateDetails:
                            formatted_response['price'][rating.TotalNetFedExCharge.Currency] = rating.TotalNetFedExCharge.Amount
                            if 'CurrencyExchangeRate' in rating:
                                formatted_response['price'][rating.CurrencyExchangeRate.FromCurrency] = rating.TotalNetFedExCharge.Amount / rating.CurrencyExchangeRate.Rate
                    else:
                        formatted_response['price']['USD'] = 0.0
                if 'MasterTrackingId' in self.response.CompletedShipmentDetail:
                    formatted_response['master_tracking_id'] = self.response.CompletedShipmentDetail.MasterTrackingId.TrackingNumber

            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response

    def _get_labels(self, file_type):
        labels = [self.get_label()]
        if file_type.upper() in ['PNG'] and self.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageDocuments:
            for auxiliary in self.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageDocuments[0].Parts:
                labels.append(binascii.a2b_base64(auxiliary.Image))

        return labels

    def get_label(self):
        return binascii.a2b_base64(self.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image)

    # Deletion stuff

    def set_deletion_details(self, tracking_number):
        self.TrackingId = self.client.factory.create('TrackingId')
        self.TrackingId.TrackingIdType = 'FEDEX'
        self.TrackingId.TrackingNumber = tracking_number

        self.DeletionControl = self.client.factory.create('DeletionControlType')
        self.DeletionControl = 'DELETE_ALL_PACKAGES'

    def delete_shipment(self):
        formatted_response = {'delete_success': False}
        try:
            # Here, we send the Order 66
            self.response = self.client.service.deleteShipment(WebAuthenticationDetail=self.WebAuthenticationDetail,
                                                               ClientDetail=self.ClientDetail,
                                                               TransactionDetail=self.TransactionDetail,
                                                               Version=self.VersionId,
                                                               TrackingId=self.TrackingId,
                                                               DeletionControl=self.DeletionControl)

            if (self.response.HighestSeverity != 'ERROR' and self.response.HighestSeverity != 'FAILURE'):
                formatted_response['delete_success'] = True
            else:
                errors_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if (n.Severity == 'ERROR' or n.Severity == 'FAILURE')])
                formatted_response['errors_message'] = errors_message

            if any([n.Severity == 'WARNING' for n in self.response.Notifications]):
                warnings_message = '\n'.join([("%s: %s" % (n.Code, n.Message)) for n in self.response.Notifications if n.Severity == 'WARNING'])
                formatted_response['warnings_message'] = warnings_message

        except suds.WebFault as fault:
            formatted_response['errors_message'] = fault
        except IOError:
            formatted_response['errors_message'] = "Fedex Server Not Found"

        return formatted_response
