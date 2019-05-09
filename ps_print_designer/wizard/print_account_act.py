from odoo import models, api


class PrintAccountAct(models.TransientModel):
    _name = "print.account.act"
    _description = "凭证打印"

    @api.multi
    def print_account_act(self):
        context = dict(self._context or {})
        print(context['active_id'])
        print(context['active_model'])
        print(787878)

        return 1