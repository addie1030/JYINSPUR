# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import tempfile
import subprocess

from odoo.addons.hw_drivers.controllers.driver import event_manager, Driver


class CameraDriver(Driver):
    connection_type = 'video'

    def __init__(self, device):
        super(CameraDriver, self).__init__(device)
        self._device_type = 'camera'
        self._device_connection = 'direct'
        self._device_name = self.dev.card.decode('utf-8')
        self._device_identifier = self.dev.bus_info.decode('utf-8')

    @classmethod
    def supported(cls, device):
        return device.driver.decode('utf-8') == 'uvcvideo'

    def action(self, data):
        try:
            """
            Check the max resolution for webcam.
            Take picture and save it to a tmp file.
            Convert this picture in base 64.
            Release Event with picture in data.
            """
            with tempfile.NamedTemporaryFile() as tmp:
                resolution = subprocess.check_output("v4l2-ctl --list-formats-ext|grep 'Size'|awk '{print $3}'|sort -rn|awk NR==1", shell=True).decode('utf-8')
                subprocess.check_call("fswebcam -d %s %s -r %s" % (self.dev.interface, tmp.name, resolution), shell=True)
                self.data['image'] = subprocess.check_output("cat %s | base64" % tmp.name, shell=True)
                self.data['message'] = 'Image captured'
        except subprocess.CalledProcessError as e:
            self.data['message'] = e.output
        event_manager.device_changed(self)
