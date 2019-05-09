# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.osv import expression


class AccountIntrastatCode(models.Model):
    '''
    Codes used for the intrastat reporting.

    The list of commodity codes is available on:
    https://www.cbs.nl/en-gb/deelnemers%20enquetes/overzicht/bedrijven/onderzoek/lopend/international-trade-in-goods/idep-code-lists
    '''
    _name = 'account.intrastat.code'
    _description = 'Intrastat Code'
    _translate = False

    name = fields.Char(string='Name')
    code = fields.Char(string='Code', required=True)
    country_id = fields.Many2one('res.country', string='Country', help='Restrict the applicability of code to a country.', domain="[('intrastat', '=', True)]")
    description = fields.Char(string='Description')
    type = fields.Selection(string='Type', required=True,
        selection=[('commodity', 'Commodity'), ('transport', 'Transport'), ('transaction', 'Transaction'), ('region', 'Region')],
        default='commodity',
        help='''Type of intrastat code used to filter codes by usage.
            * commodity: Code to be set on invoice lines for European Union statistical purposes.
            * transport: The active vehicle that moves the goods across the border.
            * transaction: A movement of goods.
            * region: A sub-part of the country.
        ''')

    @api.multi
    def name_get(self):
        result = []
        for r in self:
            text = r.name or r.description
            result.append((r.id, text and '%s %s' % (r.code, text) or r.code))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', '|', ('code', operator, name), ('name', operator, name), ('description', operator, name)]
        return super(AccountIntrastatCode, self).search(expression.AND([args, domain]), limit=limit).name_get()

    _sql_constraints = [
        ('intrastat_region_code_unique', 'UNIQUE (code, type, country_id)', 'Triplet code/type/country_id must be unique.'),
    ]
