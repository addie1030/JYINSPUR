# -*- coding: utf-8 -*-

from odoo import fields, models
class EventRegistration(models.Model):
    _inherit = 'event.registration'

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], groups="hr.group_hr_user", default="male")
    company_name = fields.Char(string='Company Name')
    position = fields.Char(string='Position')
    state_id = fields.Char(string='State')
    relationship = fields.Selection([
        ('customer', 'Customer'),
        ('cloud', 'Cloud Partner'),
        ('employee', 'Employee'),
        ('other', 'Other')
    ], default="customer")