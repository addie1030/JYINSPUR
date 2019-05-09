# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _

class RestaurantPrinter(models.Model):

    _inherit = 'restaurant.printer'

    iotbox_id = fields.Many2one('iot.box', 'IoT Box')
    proxy_ip = fields.Char(string='IP Address', size=45, related='iotbox_id.ip', store=True,
        help='The hostname or ip address of the hardware proxy, Will be autodetected if left empty.')
