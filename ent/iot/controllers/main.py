# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import odoo
import os
import zipfile
import io

class IoTController(http.Controller):

    @http.route('/iot/get_drivers', type='http', auth='public', csrf=False)
    def download_drivers(self, mac):
        # Check mac is of one of the IoT Boxes
        box = request.env['iot.box'].sudo().search([('identifier', '=', mac)], limit=1)
        if not box:
            return ''

        zip_list = []
        for addons_path in odoo.modules.module.ad_paths:
            for module in sorted(os.listdir(str(addons_path))):
                if os.path.isdir(os.path.join(addons_path, module)) and os.path.isdir(os.path.join(addons_path, module, 'drivers')):
                    for file in os.listdir(os.path.join(addons_path, module, 'drivers')):
                        if file.startswith('.') or file.startswith('_'):
                            continue
                        # zip it
                        full_path_file = os.path.join(addons_path, module, 'drivers', file)
                        zip_list.append((full_path_file, file))
        file_like_object = io.BytesIO()
        zipfile_ob = zipfile.ZipFile(file_like_object, 'w')
        for zip in zip_list:
            zipfile_ob.write(zip[0], zip[1]) # In order to remove the absolute path
        zipfile_ob.close()
        return file_like_object.getvalue()

    # Return home screen
    @http.route('/iot/box/<string:identifier>/screen_url', type='http', auth='public')
    def get_url(self, identifier):
        iotbox = request.env['iot.box'].sudo().search([('identifier', '=', identifier)], limit=1)
        if iotbox.screen_url:
            return iotbox.screen_url
        else:
            return 'http://localhost:8069/point_of_sale/display'

    @http.route('/iot/setup', type='json', auth='public')
    def update_box(self, **kwargs):
        if kwargs:
            # Box > V19
            iot_box = kwargs['iot_box']
            devices = kwargs['devices']
        else:
            # Box < V19
            data = request.jsonrequest
            iot_box = data
            devices = data['devices']

         # Update or create box
        box = request.env['iot.box'].sudo().search([('identifier', '=', iot_box['identifier'])], limit=1)
        if box:
            box = box[0]
            box.ip = iot_box['ip']
            box.name = iot_box['name']
        else:
            iot_token = request.env['ir.config_parameter'].sudo().search([('key', '=', 'iot_token')], limit=1)
            if iot_token.value.strip('\n') == iot_box['token']:
                box = request.env['iot.box'].sudo().create({'name': iot_box['name'], 'identifier': iot_box['identifier'], 'ip': iot_box['ip'], })

        # Update or create devices
        if box:
            for device_identifier in devices:
                data_device = devices[device_identifier]
                if data_device['connection'] == 'network':
                    device = request.env['iot.device'].sudo().search([('identifier', '=', device_identifier)])
                else:
                    device = request.env['iot.device'].sudo().search([('iot_id', '=', box.id), ('identifier', '=', device_identifier)])

                if device:
                    device.name = data_device['name']
                else:
                    device = request.env['iot.device'].sudo().create({
                        'iot_id': box.id,
                        'name': data_device['name'],
                        'identifier': device_identifier,
                        'type': data_device['type'],
                        'connection': data_device['connection'],
                    })
