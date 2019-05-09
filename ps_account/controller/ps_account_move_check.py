
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date


class MyController(http.Controller):
    @http.route('/ps_spj_print/spj_print', auth='public', type='json', method='POST')
    def spj_print(self, **kw):
        parm = kw['active_ids'][0]
        print(parm)
        sql_header = """
                                SELECT
                                RES_PARTNER.NAME AS 单位名称,ACCOUNT_MOVE.DATE AS 日期,ACCOUNT_MOVE.REF AS 凭证编号, 0 AS 凭证
                                FROM
                                ACCOUNT_MOVE Left join RES_PARTNER ON ACCOUNT_MOVE.PARTNER_ID =  RES_PARTNER.ID
                                WHERE
                                ACCOUNT_MOVE.ID = %s 
                             """ % parm
        request.env.cr.execute(sql_header)
        head_data = request.env.cr.dictfetchone()
        if not head_data['单位名称']:
            head_data['单位名称'] = '无'
        print(head_data)
        # ====================================================
        # 关联关系：account_move.id = account_move_line.move_id
        # ====================================================

        sql_body = """
                            SELECT
                            ACCOUNT_MOVE_LINE.NAME AS 摘要,ACCOUNT_ACCOUNT.NAME AS 总账科目,ACCOUNT_ACCOUNT.NAME AS 二级科目, ACCOUNT_ACCOUNT.NAME AS 明细科目,ACCOUNT_MOVE_LINE.DEBIT AS 借方,ACCOUNT_MOVE_LINE.CREDIT AS 贷方
                            FROM
                            ACCOUNT_MOVE_LINE,ACCOUNT_ACCOUNT
                            WHERE
                            ACCOUNT_MOVE_LINE.MOVE_ID = %s AND ACCOUNT_MOVE_LINE.ACCOUNT_ID = ACCOUNT_ACCOUNT.ID
                           """ % parm
        request.env.cr.execute(sql_body)
        data_data = request.env.cr.dictfetchall()

        head_data['凭证'] = data_data

        url = 'http://10.24.35.4:8080/print/' + str(head_data)
        return url


class PsAccountMoveCheckPostController(http.Controller):
    @http.route('/account/check', type='json', auth='user')
    def check_account_move(self, **kw):
        print(kw['active_ids'])
        obj = request.env['ps.account.move.check']
        context = dict(obj._context or {})
        print(context.get('active_ids'))

        return{'rtn': 'ok'}