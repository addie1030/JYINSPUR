# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountFiscalPositionTemplate(models.Model):
    _inherit = 'account.fiscal.position.template'

    is_taxcloud = fields.Boolean(string='Use TaxCloud API')


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    is_taxcloud = fields.Boolean(string='Use TaxCloud API')
