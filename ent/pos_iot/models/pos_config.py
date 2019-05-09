# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    iotbox_id = fields.Many2one('iot.box', 'Related Box')
    proxy_ip = fields.Char(string='IP Address', size=45, related='iotbox_id.ip', store=True,
        help='The hostname or ip address of the hardware proxy, Will be autodetected if left empty.')