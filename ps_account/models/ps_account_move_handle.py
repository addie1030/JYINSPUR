# -*- coding: utf-8 -*-
import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta

from odoo.exceptions import UserError
from odoo import api,  models, fields, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError

from lxml import etree

############################################
# describe：凭证断号处理
# date：20180809
# author：sunny
############################################
class PsAccountMoveHandle(models.TransientModel):
    _name = 'ps.account.move.no.process'
    _description = 'Broken Number Handling'

    # 默认为当前日期所在的期间
    @api.model
    def _get_default_period(self):
        period_ids = self.env['ps.account.period'].get_period(fields.Date.today())
        if not period_ids:
            raise UserError(_("There is no activated period yet, please enable it in the accounting period function!"))
        if len(period_ids)>0:
            return period_ids[0]

    name = fields.Char(default=lambda self: _('Broken Number Handling'))
    # 会计期间
    period_id = fields.Many2one('ps.account.period', string='Period', required=True, default=_get_default_period)
    # 账簿类型
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    # 处理方式
    no_process_style = fields.Selection([('0', _('According to broken number')),
                                         ('1', _('According to voucher date'))],
                                        string='Method', default='0', required=True)
    move_ids = fields.One2many('ps.account.move.no.process.detail', 'move_no_id', string='Voucher List')

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     if self._context is None: self._context = {}
    #     res = super(PsAccountMoveHandle, self).fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #     if res['type'] == "form":
    #         # id = res['id']
    #         # // 根据id去取得资料，并进行判断
    #         # if id:
    #         doc = etree.XML(res['arch'])
    #         doc.xpath("//form")[0].set("create", "false")
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    @api.multi
    def get_move_records(self):
        self.ensure_one()
        cur_year = self.period_id.year
        cur_period = self.period_id.period
        voucher_name = self.journal_id.ps_voucher_word
        # document_no_ids = self.env['ps.account.document.no'].search(
        #     [('company_id', '=', self.env.user.company_id.id), ('year', '=', cur_year), ('period', '=', cur_period)])
        # for docno in document_no_ids:

        self.move_ids.unlink()
        #余额初始生成的凭证不参与统一编号
        sql = ""
        if self.no_process_style=='0':
            sql = """select row_number() OVER(order by name asc) as rownumber, cast (right(name,5) as int) as move_no,name,
                      date,account_move.id as move_id,ref as move_ref from account_move
                      left join ps_account_period on account_move.ps_period_code = ps_account_period.id
                      where name!='00000' and ps_account_period.year='%s' and ps_account_period.period='%s' and ps_voucher_word='%s'
                      """ % (cur_year, cur_period, voucher_name)
        else:
            sql = """select row_number() OVER(order by date asc,name asc) as rownumber, cast (right(name,5) as int) as move_no,name,
                      date,account_move.id as move_id,ref as move_ref from account_move
                      left join ps_account_period on account_move.ps_period_code = ps_account_period.id
                      where name!='00000' and ps_account_period.year='%s' and ps_account_period.period='%s' and ps_voucher_word='%s'
                      """ % (cur_year, cur_period, voucher_name)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        move_ids_data = []
        for item in temp_ids:
            if item[0] != item[1]:
                move_ids_data.append((0, 0, {
                    'old_no': item[2],
                    'new_no': voucher_name+'-'+str(item[0]).zfill(5),
                    'move_date': item[3],
                    'move_id': item[4],
                    'move_ref': item[5],
                }))

        self.move_ids = move_ids_data
        return True


    @api.multi
    def handle_move_records(self):
        self.ensure_one()
        if len(self.move_ids) == 0:
            raise ValidationError(_('There are no Vouchers to be processed during the current period!'))
        ps_move_object = self.env['account.move']

        for item in self.move_ids:
            temp_data={}
            if item.move_ref == item.old_no:
                temp_data = {'name': item.new_no, 'ref': item.new_no}
            else:
                temp_data = {'name': item.new_no}
            ps_move_object.search([('id', '=', item.move_id)]).with_context(check_move_validity=False).write(temp_data)
        self.move_ids.unlink()
        return True


class PsAccountMoveBalance(models.TransientModel):
    _name = 'ps.account.move.no.process.detail'
    _description = 'Broken Number Handling_transient'

    move_date = fields.Date(string='Voucher Date')
    old_no = fields.Char(string="Origin Voucher Number", readonly=True)
    new_no = fields.Char(string="New Voucher Number", readonly=True)
    move_id = fields.Integer(string="Voucher ID")
    move_ref = fields.Char(string="Voucher REF")
    move_no_id = fields.Many2one('ps.account.move.no.process', string='Broken Number Handling', ondelete="cascade", required=True)

    no_process_style = fields.Selection(related='move_no_id.no_process_style', store=False)