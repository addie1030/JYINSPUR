# -*- coding: utf-8 -*-
import sys
import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import odoo.addons.decimal_precision as dp
# reload(sys)
# sys.setdefaultencoding('utf8')

import logging
_logger = logging.getLogger(__name__)


class PsMarkMoveTrade(models.TransientModel):
    _name = 'ps.mark.move.trade.wizard'

    @api.multi
    def mark_move_trade(self):
        am = self.env['account.move'].browse(int(self.env.context.get('ps_move_id')))
        pamt = self.env['ps.account.move.trade']
        if am:
            if am.ps_way == 'receive':
                recs_send = pamt.search([('trade_no', '=', am.ps_trade_no), ('origin', '=', 'send')])#发送方写入的记录
                #接收方循环写入中间表
                pamt.create({'src_move_id': am.id,
                             'des_company_id': am.ps_partner_id.id,
                             'type_id': am.ps_type_id.id,
                             'trade_no': am.ps_trade_no,
                             'src_company_id': self.env.user.company_id.partner_id.id,
                             'state': 'done',
                             'origin': 'receive'
                             })
                # 发送方数据设置已发送已接收
                recs_send.write({
                    'state': 'done'
                })
            else:
                    pamt.create({'src_move_id': am.id,
                                 'des_company_id': am.ps_partner_id.id,
                                 'type_id': am.ps_type_id.id,
                                 'trade_no': am.ps_trade_no,
                                 'src_company_id': self.env.user.company_id.partner_id.id,
                                 'state': 'draft',
                                 'origin': 'send'
                                 })
                    am.write({'ps_boolean_inside': True})

class PsCancleMoveTrade(models.TransientModel):
    _name = 'ps.cancle.move.trade.wizard'

    @api.multi
    def cancel_move_trade(self):
        recs = self.env['ps.account.move.trade'].search([('trade_no', '=', self.env.context.get('ps_trade_no')),('origin', '=', self.env.context.get('origin'))])
        if self.env.context.get('origin') == 'receive':
            self.env['ps.account.move.trade'].search([('trade_no', '=', self.env.context.get('ps_trade_no')),
                                                             ('origin', '=', 'send')]).write({'state': 'draft'})
        return recs.unlink()
