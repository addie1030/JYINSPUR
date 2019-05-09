# -*- coding: utf-8 -*-

from odoo import models
from odoo.tools.translate import _
from odoo.tools.misc import formatLang, format_date

LINE_FILLER = '*'

class report_print_check(models.Model):
    _inherit = 'account.payment'

