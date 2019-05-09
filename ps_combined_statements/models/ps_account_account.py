# -*- coding: utf-8 -*-
from odoo import fields, models, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    subject_select = fields.Many2many(comodel_name='ps.account.subject.config', relation='account_to_subject_config_rel',
                                      column1='account_id', column2='config_id', string='Subject limit set ')


class AccountSubjectConfig(models.Model):
    _name = 'ps.account.subject.config'

    name = fields.Char(string='describe ')
    field_id = fields.Char(string='field ID')
