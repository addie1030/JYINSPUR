import odoo
from odoo import api, fields, models, _
from odoo.exceptions import AccessError

class IrCron(models.Model):
    _inherit = 'ir.cron'

    @api.multi
    def write(self, vals):
        ping_cron = self.env.ref('mail.ir_cron_module_update_notification', raise_if_not_found=False)
        if ping_cron and ping_cron in self:
            raise AccessError(_('The Update Notification scheduled action cannot be modified'))
        res = super(IrCron, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        ping_cron = self.env.ref('mail.ir_cron_module_update_notification', raise_if_not_found=False)
        if ping_cron and ping_cron in self:
            raise AccessError(_('The Update Notification scheduled action cannot be deleted'))
        res = super(IrCron, self).unlink()
        return res
