# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    default_contract_id = fields.Many2one('hr.contract', string="Default Contract for New Employees",
        help="Default contract used when making an offer to an applicant.")
