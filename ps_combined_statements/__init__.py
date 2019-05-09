# -*- coding: utf-8 -*-

from . import models
from . import wizard


def post_init_hook(cr, registry):
	from odoo import api, SUPERUSER_ID

	env = api.Environment(cr, SUPERUSER_ID, {})
	try:
		f = open('/data/init.sql', 'r')
		sql = f.read()
		cr.execute(sql)
	except IOError as e:
		pass
