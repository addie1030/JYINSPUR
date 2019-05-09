# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import serial
import usb

from odoo import _
from odoo.addons.hw_drivers.controllers.driver import event_manager, Driver


class SylvacUSBDriver(Driver):
    connection_type = 'usb'

    def __init__(self, device):
        super(SylvacUSBDriver, self).__init__(device)
        self._device_type = 'device'
        self._device_connection = 'direct'
        self._device_name = self._set_name()
        self._device_identifier = "usb_%04x:%04x_%03d_%03d_" % (self.dev.idVendor, self.dev.idProduct, self.dev.bus, self.dev.address)

    @classmethod
    def supported(cls, device):
        if getattr(device, 'idVendor') == 0x0403 and getattr(device, 'idProduct') == 0x6001:
            return True
        return False

    def _set_name(self):
        try:
            manufacturer = usb.util.get_string(self.dev, 256, self.dev.iManufacturer)
            product = usb.util.get_string(self.dev, 256, self.dev.iProduct)
            return ("%s - %s") % (manufacturer, product)
        except ValueError as e:
            _logger.warning(e)
            return _('Unknow device')

    def run(self):
        connection = serial.Serial('/dev/serial/by-id/usb-Sylvac_Power_USB_A32DV5VM-if00-port0',
                                   baudrate=4800,
                                   bytesize=7,
                                   stopbits=2,
                                   parity=serial.PARITY_EVEN)
        measure = b''
        no_except = True
        while no_except:
            try:
                char = connection.read(1)
                if ord(char) == 13:
                    # Let's send measure
                    self.data['value'] = measure.decode("utf-8")
                    event_manager.device_changed(self)
                    measure = b''
                else:
                    measure += char
            except:
                no_except = False