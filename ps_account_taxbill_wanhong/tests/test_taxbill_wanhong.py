# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo import fields
import datetime
import time
import logging
from hashlib import md5
import json
import requests
from dateutil.tz import gettz
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class TestTaxbillWanhong(TransactionCase):
    def setup(self):
        super(TestTaxbillWanhong, self).setUp()

    def test_invoicing_vat(self):
        dt = datetime.datetime.now()
        dt = (dt + datetime.timedelta(hours=8))
        timeStamp = int(time.mktime(dt.timetuple()) * 1000)

        self.partner_id = self.env.ref('ps_account_taxbill_test').partner_id
        self.company_id = self.env.ref('ps_account_taxbill_test').company_id
        self.apply_line_ids = self.env.ref('ps_account_taxbill_test').apply_line_ids
        self.id = self.env.ref('ps_account_taxbill_test').id
        self.taxbill_type = self.env.ref('ps_account_taxbill_test').taxbill_type
        self.notes = self.env.ref('ps_account_taxbill_test').notes
        self.payee_id = self.env.ref('ps_account_taxbill_test').payee_id
        self.reviewer_id = self.env.ref('ps_account_taxbill_test').reviewer_id
        self.email = self.env.ref('ps_account_taxbill_test').email
        self.mobile = self.env.ref('ps_account_taxbill_test').mobile

        addressInfo = (self.company_id.street or "") + (self.company_id.street2 or "") + (self.company_id.city or "") \
                      + (self.company_id.state_id.name or "") + (self.company_id.zip or "") \
                      + (self.company_id.country_id.name or "") + (self.company_id.phone or "")
        bankInfo = (self.partner_id.ps_bank_name or "") + (self.partner_id.ps_bank_account or "")
        sign = "sign:" + self.company_id.vat + str(timeStamp) + "LC"
        md5_sign = md5(sign.encode('ascii')).hexdigest().upper()

        details = []
        totalMoney = 0
        for r in self.apply_line_ids:
            detail = {
                "goodsName": r.product_id.product_tmpl_id.name,
                "classCode": "",
                "model": r.specification or "",
                "unit": r.uom_id.name or "",
                "quantity": str(r.quantity) or "",
                "money": str(r.price_total),
                "price": str(r.price_unit),
                "rate": str(r.price_tax)
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
                "customerTaxNo": self.partner_id.vat or "",
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
        self.assertEqual(ret.get("errorCode"), "0", "success!")
        self.assertNotEqual(ret.get("errorCode"), "0", "failure!")