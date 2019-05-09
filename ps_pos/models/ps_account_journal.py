from odoo import fields, models, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    ps_is_member_deposit = fields.Boolean(string=_("Used for membership deposit"))  # 在账簿类型中增加，用于会员储值
