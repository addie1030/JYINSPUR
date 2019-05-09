# -*- coding: utf-8 -*-

import logging
import datetime
import time
import requests
import re
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from hashlib import md5

_logger = logging.getLogger(__name__)

class PsAccountTaxbill(models.Model):
    _inherit = "ps.account.taxbill"

    @api.multi
    def invoicing_vat(self):
        self.ensure_one()
        dt = datetime.datetime.now()
        dt = (dt + datetime.timedelta(hours=8))
        timeStamp = int(time.mktime(dt.timetuple()) * 1000)
        addressInfo = (self.partner_id.street or "") + (self.company_id.street2 or "") + (self.partner_id.city or "") \
                      + (self.partner_id.state_id.name or "") + (self.partner_id.zip or "") \
                      + (self.partner_id.country_id.name or "") + (self.partner_id.phone or "")
        bankInfo = (self.partner_id.ps_bank_name.name or "") + (self.partner_id.ps_bank_account or "")
        if not self.company_id.vat:
            raise UserError(_('The vat of the company did not exist, please maintain the vat first'))
        elif not self.partner_id.vat:
            raise UserError(_('The vat of the customer did not exist, please maintain the vat first'))
        sign = "sign:" + self.company_id.vat + str(timeStamp) + "LC"
        md5_sign = md5(sign.encode('ascii')).hexdigest().upper()
        details = []
        totalMoney = 0
        if self.taxbill_type == '1' and (addressInfo or bankInfo) == '':
            raise UserError(_('The customer address or bank information is not enough for current VAT type.'))
        for r in self.apply_line_ids:
            taxrate = round(r.price_tax/r.price_subtotal,2)
            detail = {
                "goodsName": r.product_id.product_tmpl_id.ps_trade_name or r.product_id.product_tmpl_id.name,
                "classCode": "",
                "model": r.specification or "",
                "unit": r.uom_id.name or "",
                "quantity": str(r.quantity) or "",
                "money": str(r.price_total),
                "price": str(r.price_unit),
                "rate": str(taxrate)
            }
            totalMoney += r.price_total
            details.append(detail)
        obj = {
            "dt": str(timeStamp),
            "salt": "LC",
            "sign": md5_sign,
            "taxNo": self.company_id.vat,
            "invoices":[{
                "billNo": str(self.id) + self.name,
                "totalMoney": str(totalMoney),
                "type": self.taxbill_type,
                "title": self.partner_id.name,
                "addressInfo": addressInfo,
                "customerTaxNo": self.partner_id.vat,
                "bankInfo": bankInfo,
                "fileRemark": self.notes or "",
                "customNotes": self.partner_id.comment or "",
                "payee": self.payee_id.login or "",
                "checker": self.reviewer_id.login or "",
                "mail": self.email,
                "mobile": self.mobile,
                "details": details
            }]
        }
        obj = json.dumps(obj)
        ret = requests.post("http://14.23.161.194:8888/platform/lc/sendDataInfo", data={"json": obj}).json()
        if ret.get("errorCode") == "0":
            self.write({'state': 'opening'})
            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoicing VAT'),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'ps.apply.vat.wizard',
                'target': 'new',
            }
        else:
            raise UserError(ret.get("errorMsg"))

    @api.multi
    def download_vat(self):
        self.ensure_one()
        dt = datetime.datetime.now()
        dt = (dt + datetime.timedelta(hours=8))
        timeStamp = int(time.mktime(dt.timetuple()) * 1000)
        sign = "sign:" + self.company_id.vat + str(timeStamp) + "LC"
        md5_sign = md5(sign.encode('ascii')).hexdigest().upper()
        obj = {
            "billNoStr": str(self.id) + self.name,
            "dt": str(timeStamp),
            "salt": "LC",
            "sign": md5_sign,
            "taxNo": self.company_id.vat,
            "status": ""
        }
        obj = json.dumps(obj)
        ret = requests.post("http://14.23.161.194:8888/platform/lc/receiveDataInfo", data={"json": obj}).json()
        totalMoney = 0;
        billNumber = []
        if ret.get("errorCode") == "0":
            pattern = re.compile(r'\d+')
            for i in range(len(ret['invoices'])): #处理多张发票
                if ret['invoices'][i]['billCode'] == '':
                    raise UserError(_('The VAT receipt has not been issued yet and cannot be downloaded.'))
                m = pattern.match(ret['invoices'][i]['billNo'])
                rec = self.env['ps.account.invoice.taxbill']
                vals = []
                totalMoney += ret['invoices'][i]['totalAmount']
                taxbillNumber = ret['invoices'][i]['billNumber'] + '/' + ret['invoices'][i]['billCode']
                billNumber.append(taxbillNumber)
                for j in range(len(ret['invoices'][0]['details'])):#处理多条明细
                    val = {
                        'taxbill_id': int(m.group()),
                        'code_number': ret['invoices'][i]['details'][j]['classCode'],
                        'quantity': ret['invoices'][i]['details'][j]['quantity'],
                        'trade_name': ret['invoices'][i]['details'][j]['goodsName'],
                        'price_unit_tax': ret['invoices'][i]['details'][j]['taxPrice'],
                        'tax_rate': ret['invoices'][i]['details'][j]['taxRate'],
                        'price_tax': ret['invoices'][i]['details'][j]['taxAmount'],
                        'price_unit': ret['invoices'][i]['details'][j]['noTaxPrice'],
                        'uom_name': ret['invoices'][i]['details'][j]['unit'],
                        'price_subtotal': ret['invoices'][i]['details'][j]['totalAmount'] - ret['invoices'][i]['details'][j]['taxAmount'],
                        'specification': ret['invoices'][i]['details'][j]['model'],
                        'price_total': ret['invoices'][i]['details'][j]['totalAmount']
                    }
                    val = (0, 0, val)
                    vals.append(val)
                rec.create({
                    'taxbill_id': int(m.group()),
                    'original_taxbill': ret['invoices'][i]['billNo'][m.end():],
                    'partner_id': self.partner_id.id,
                    'tax_invoice_type': ret['invoices'][i]['type'],
                    'invoice_code': ret['invoices'][i]['billCode'],
                    'invoice_number': ret['invoices'][i]['billNumber'],
                    'taxbill_date': ret['invoices'][i]['invoiceDate'],
                    'taxbill_state': ret['invoices'][i]['status'],
                    'invoice_url': ret['invoices'][i]['pdfUrl'],
                    'notes': ret['errorMsg'],
                    'tax_amount': ret['invoices'][i]['taxAmount'],
                    'amount': ret['invoices'][i]['totalAmount'],
                    'invoice_taxbill_ids': vals
                })
            self.write({
                'taxbill_amount_actual': totalMoney,
                'taxbill_number': str(billNumber),
                'state': 'done'
            })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Download VAT'),
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'ps.download.vat.wizard',
                'target': 'new',
            }
        else:
            raise UserError(ret.get("errorMsg"))