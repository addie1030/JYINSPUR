from odoo import models, fields, api

class book(models.Model):
    _name='library.book'
	name = fields.Char('Title', required=True)