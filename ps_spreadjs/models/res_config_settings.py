
from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    ps_statement_calculation_contains_unaccounted = fields.Boolean(string="Statement calculation contains unposted voucher")#"报表计算包含未记账凭证"

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.user.company_id.write({
                'ps_statement_calculation_contains_unaccounted': self.ps_statement_calculation_contains_unaccounted
            })

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            ps_statement_calculation_contains_unaccounted=self.env.user.company_id.ps_statement_calculation_contains_unaccounted,
        )
        return res


class PsResCompany(models.Model):
    _inherit = 'res.company'

    ps_statement_calculation_contains_unaccounted = fields.Boolean()#报表计算包含未记账凭证