# -*- coding: utf-8 -*-

import time
import math

from datetime import datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools


class PsSalePurchaseAccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def post(self, invoice=False):

        self._post_validate()
        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name:
                    move.name = new_name

        return self.write({'state': 'posted',
                           'ps_create_user': self.env.user.id,
                           'ps_confirmed_user': self.env.user.id,
                           'ps_confirmed_datetime': fields.Date.today(),
                           'ps_posted_user': self.env.user.id,
                           'ps_posted_datetime': fields.Date.today()
                           })