from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    ps_property_account_sales_discount_id = fields.Many2one('account.account', _(
        'Consumption Discount Account'))  # 在公司下增加消费折扣科目,用于设置储值单的贷方科目
