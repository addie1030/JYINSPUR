# -*- coding: utf-8 -*-

import datetime
import time
import requests
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from hashlib import md5

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.multi
    def taxbill_register(self):
        res = self.search([], order='id desc', limit=1)
        dt = datetime.datetime.now()
        dt = (dt + datetime.timedelta(hours=8))
        timeStamp = int(time.mktime(dt.timetuple()) * 1000)
        if res:
            if not res.street:
                res.street = ""
            if not res.street2:
                res.street2 = ""
            if not res.city:
                res.city = ""
            if not res.state_id.name:
                state_name = ""
            else:
                state_name = res.state_id.name
            if not res.zip:
                res.zip = ""
            if not res.country_id.name:
                country_name = ""
            else:
                country_name = res.country_id.name
            ps_address = res.street + res.street2 + res.city + state_name + res.zip + country_name
            if (res.vat and (len(res.vat) == 15 or len(res.vat) == 18 or len(res.vat) == 20)) and ps_address and res.phone:
                sign = "sign:" + res.vat + str(timeStamp) + "LC"
                md5_sign = md5(sign.encode('ascii')).hexdigest().upper()
                max_amount = round(float(res.ps_maximum_amount), 2) * 10000

                obj = {
                    "name": res.name,
                    "taxNo": res.vat,
                    "address": ps_address,
                    "tel": res.phone,
                    "bankName": res.ps_bank_id.name,
                    "bankAcount": res.ps_bank_account,
                    "version": res.ps_tax_version,
                    "code": res.ps_tax_disk_number,
                    "maxMoney": str(max_amount),
                    "dt": str(timeStamp),
                    "salt": "LC",
                    "sign": md5_sign
                }
                obj = json.dumps(obj)
                ret = requests.post("http://14.23.161.194:8888/platform/lc/init", data={"json": obj}).json()
                if ret.get("errorCode") == "0":
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Taxbill Register'),
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_model': 'ps.res.company',
                        'target': 'new',
                    }
                else:
                    raise UserError(ret.get("errorMsg"))
            else:
                raise UserError(_("Tax number,tel and address cannot be empty and Tax number must be 15, 18 or 20 digits in length."))#税号,电话和地址不能为空并且税号长度必须为15，18或20位。

