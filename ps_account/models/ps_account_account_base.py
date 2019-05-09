# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

def single_get_first(unicode):
    str1 = unicode.encode('gbk')
    try:
        ord(str1)
        #return str1
        return unicode
    except:
        asc = str1[0] * 256 + str1[1] - 65536
        if asc >= -20319 and asc <= -20284:
            return 'a'
        if asc >= -20283 and asc <= -19776:
            return 'b'
        if asc >= -19775 and asc <= -19219:
            return 'c'
        if asc >= -19218 and asc <= -18711:
            return 'd'
        if asc >= -18710 and asc <= -18527:
            return 'e'
        if asc >= -18526 and asc <= -18240:
            return 'f'
        if asc >= -18239 and asc <= -17923:
            return 'g'
        if asc >= -17922 and asc <= -17418:
            return 'h'
        if asc >= -17417 and asc <= -16475:
            return 'j'
        if asc >= -16474 and asc <= -16213:
            return 'k'
        if asc >= -16212 and asc <= -15641:
            return 'l'
        if asc >= -15640 and asc <= -15166:
            return 'm'
        if asc >= -15165 and asc <= -14923:
            return 'n'
        if asc >= -14922 and asc <= -14915:
            return 'o'
        if asc >= -14914 and asc <= -14631:
            return 'p'
        if asc >= -14630 and asc <= -14150:
            return 'q'
        if asc >= -14149 and asc <= -14091:
            return 'r'
        if asc >= -14090 and asc <= -13119:
            return 's'
        if asc >= -13118 and asc <= -12839:
            return 't'
        if asc >= -12838 and asc <= -12557:
            return 'w'
        if asc >= -12556 and asc <= -11848:
            return 'x'
        if asc >= -11847 and asc <= -11056:
            return 'y'
        if asc >= -11055 and asc <= -10247:
            return 'z'
        return ''


def getPinyin(string):
    if string == "":
        return ""
    shortname = ""
    lst = list(string)
    charLst = []
    for l in lst:
        charLst.append(single_get_first(l))

    for i in charLst:
        shortname = shortname + i

    return shortname





############################################
# describe：1、增加结算方式，凭证制单录入银行类科目时用到
#           2、自动生成助记码
# date：20180508
# author：sunny
############################################
class PsAccountBankpayments(models.Model):
    _name = "ps.account.bankpayment"
    _description = "Settlement method"

    name = fields.Char(string='name', required=True)
    shortcode = fields.Char(string='Mnemonic code')
    company_id = fields.Many2one('res.company', string='the company', required=True,
                                 default=lambda self: self.env.user.company_id)


    @api.onchange('name')
    def _onchange_name(self):
        # set auto-changing field
        if self.name == "":
            return
        elif self.name is False:
            return
        else:
            self.shortcode = getPinyin(self.name)

############################################
# describe：1、固定汇率
# date：20180508
# author：sunny
############################################
class PsCurrencyFixRate(models.Model):
    _name = "ps.res.currency.fixed.rate"

    _description = _("Fixed Rate")

    name = fields.Char(string=_('Number'), required=True, size=2, help="Two-digit month")
    account_rate = fields.Float(string=_("Posting Rate"), default=0) #记账汇率
    adjust_rate = fields.Float(string=_("Adjustment Rate"), default=0)
    currency_id = fields.Many2one('res.currency', string=_("Currency"), readonly=True)
    company_id = fields.Many2one('res.company', string=_("Company"), required=True,
                                 default=lambda self: self.env.user.company_id, readonly=True)

############################################
# describe：res.currency对象增加“汇率方式”字段
# date：20180509
# author：sunny
############################################
class PsAccountCurrency(models.Model):
    _name = 'res.currency'
    _inherit = 'res.currency'

    ps_rate_style = fields.Selection([('1', _("Fixed Rate")), ('2', _("Floating Rate"))], string=_("Exchange Rate Method"),
                                     default='1', required=True)
    ps_rate_compute_style = fields.Selection([('1', _("Original=Rate*Local")), ('2', _('Original/Rate=Local'))],
                                             string=_("Exchange Rate Conversion Method"), default='1', required=True)

    @api.multi
    @api.depends('rate_ids.rate')
    def _compute_current_rate(self):
        date = self._context.get('date') or fields.Date.today()
        company_id = self._context.get('company_id') or self.env['res.users']._get_company().id
        # the subquery selects the last rate before 'date' for the given currency/company
        for n in self:
            if n.ps_rate_style == '1':
                query = """SELECT c.id, (SELECT r.account_rate FROM ps_res_currency_fixed_rate r
                                                      WHERE r.currency_id = c.id AND r.name <= %s
                                                        AND (r.company_id IS NULL OR r.company_id = %s)
                                                   ORDER BY r.company_id, r.name DESC
                                                      LIMIT 1) AS rate
                                       FROM res_currency c
                                       WHERE c.id IN %s"""
                self._cr.execute(query, (date.strftime(DF), company_id, tuple(self.ids)))
                currency_rates = dict(self._cr.fetchall())
                n.rate = currency_rates.get(n.id) or 1.0
            if n.ps_rate_style == '2':
                query = """SELECT c.id, (SELECT r.rate FROM res_currency_rate r
                                              WHERE r.currency_id = c.id AND r.name <= %s
                                                AND (r.company_id IS NULL OR r.company_id = %s)
                                           ORDER BY r.company_id, r.name DESC
                                              LIMIT 1) AS rate
                               FROM res_currency c
                               WHERE c.id IN %s"""
                self._cr.execute(query, (date.strftime(DF), company_id, tuple(self.ids)))
                currency_rates = dict(self._cr.fetchall())
                n.rate = currency_rates.get(n.id) or 1.0

    # @api.model_cr
    # def init(self):
    #     res = super(PsAccountCurrency, self).init()
    #     self.search([('ps_rate_style', '=', None)]).write({'ps_rate_style': '1','ps_rate_compute_style': '1'})
    #     return res

############################################
# describe：1、PS预置科目表
# date：20180526
# author：sunny
############################################
# class PsAccountAccountTemp(models.Model):
#     _name = 'ps.account.account'
#     _description = "PS Cloud科目表"
#
#     name = fields.Char(required=True, index=True)
#     code = fields.Char(size=64, required=True, index=True)
#     reconcile = fields.Boolean(string='Allow Reconciliation', default=False,
#         help="Check this box if this account allows invoices & payments matching of journal items.")
#     user_type_id = fields.Many2one('account.account.type', string='Type', required=True, oldname="user_type",
#         help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.")
