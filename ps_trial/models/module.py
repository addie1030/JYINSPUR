from odoo import api, models
from odoo.exceptions import AccessError, AccessDenied
from odoo.tools.translate import _

class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def _button_immediate_function(self, function):
        res = super(IrModuleModule, self)._button_immediate_function(function)
        self.env['publisher_warranty.contract'].browse().update_notification(cron_mode=True)
        return res

    # overridden to catch all attempts to uninstall this module
    @api.multi
    def write(self, values):
        for mod in self:
            if mod.name == 'ps_trial' and values.get('state', None) == 'to remove':
                raise AccessError(_("Module 'ps_trial' cannot be uninstalled"))
        return super(IrModuleModule, self).write(values)
