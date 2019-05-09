# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError


############################################
# describe：会计年度、区间
# date：20180420
# author：sunny
############################################
class PsAccountFiscalYear(models.Model):
    _name = 'ps.account.fiscalyear'
    _description = 'Fiscal Year'
    _order = 'id'

    name = fields.Char(string='Fiscal Year', size=4, required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    state = fields.Selection([('0', _('Draft')), ('1', 'Activate'), ('2', 'Settled')], string='Status', default='0', readonly=True)

    period_ids = fields.One2many('ps.account.period', 'fiscalyear_id', string='Period')

    @api.model
    def create(self, vals):
        if self._check_year(vals['name']):
            rec = super(PsAccountFiscalYear, self).create(vals)
            return rec

    @api.multi
    def unlink(self):
        for item in self:
            if self._check_period_use(item.name):
                raise ValidationError(
                    _('The period') + item.name + _('has been used，and cannot be deleted.'))
            if self.env.user.company_id.ps_account_begin_date:
                if self.env.user.company_id.ps_account_begin_date == item.date_start:
                    self.env.user.company_id.ps_account_begin_date = False
            cur_kjqj = self.env.user.company_id.ps_current_fiscalyear
            if cur_kjqj:
                if cur_kjqj[0: 4] == item.name:
                    self.env.user.company_id.ps_current_fiscalyear = False
        return super(PsAccountFiscalYear, self).unlink()

    def _check_period_use(self, year):
        sql = "SELECT count(*) FROM account_move A LEFT JOIN PS_ACCOUNT_PERIOD B ON A.PS_PERIOD_CODE = B.ID WHERE B.YEAR ='%s'" %(year)

        # sql = """select count(*) from account_move where ps_period_code.year='%s' """ % (year)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        bill_count = temp_ids[0][0]
        if bill_count > 0:
            return True
        return False

    @api.one
    def create_period(self):
        period_obj = self.env['ps.account.period']
        period_ids_data = []
        index = 0
        for fy in self.browse(self.ids):
            ds = fy.date_start
            while ds < fy.date_end:
                de = ds + relativedelta(months=1, days=-1)
                if de > fy.date_end:
                    de = fy.date_end
                index = index + 1
                period_ids_data.append((0, 0, {
                    'period': str(index).zfill(2),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_end': de.strftime('%Y-%m-%d'),
                    'financial_state': '0',
                    'business_state': '0',
                    'year': self.name,

                }))

                ds = ds + relativedelta(months=1)
            fy.period_ids = period_ids_data
        self.env.user.company_id.set_onboarding_step_done('account_setup_fy_data_state')
        return True

    @api.one
    def create_period1(self):
        return self.create_period()

    @api.one
    def create_period2(self):
        records = self.env['ps.account.period'].search([('fiscalyear_id', '=', self.id)])
        if len(records) > 0:
            records.unlink()
        return self.create_period()

    # 初始使用时，启用会计年度，根据当前日期算出当前的期间
    @api.one
    def enable_year(self):
        # 格式如 2018-05-10
        if self.env.user.company_id.ps_current_fiscalyear:
            raise ValidationError(_('The accounting period has been used, no need to activate again.'))
            # return  True
        else:
            currentday = datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            periodlist = self.env['ps.account.period'].search(
                [('fiscalyear_id', '=', self.id), ('date_start', '<=', currentday),
                 ('date_end', '>=', currentday)])
            if len(periodlist) == 0:
                raise ValidationError(
                    _('The period corresponding to the current date has not been generated yet. Please add a period first.'))
            currentperiod = periodlist[0].period
            if len(periodlist) > 1:
                raise ValidationError(
                    _('There are multiple eligible periods, please modify the period first!'))
            currentperiod = periodlist[0].period
            self.write({'state': '1'})
            self.env['ps.account.period'].search(
                [('fiscalyear_id', '=', self.id), ('period', '<', currentperiod)]).write({'financial_state': '2'})
            self.env['ps.account.period'].search([('id', '=', periodlist[0].id)]).write({'financial_state': '1'})
            self.env.user.company_id.ps_current_fiscalyear = self.name + currentperiod
        return True

    @api.one
    def TestGetPeriod(self):
        period_ids = self.env['ps.account.period'].get_period('2018-04-12')
        if period_ids == False:
            raise ValidationError(
                _('The corresponding accounting period was not found, please maintain the period first.'))
        if len(period_ids) > 1:
            raise ValidationError(
                _('There are multiple periods, please modify the period first.'))
        year = period_ids[0].year
        period = period_ids[0].period

    def _check_year(self, year):
        if len(year) != 4:
            raise ValidationError(_('Please enter the 4-digit annual number.'))
        try:
            num = int(year)
            return True
        except:
            raise ValidationError(_('The input number is not in accordance with the rules.'))


class PsAccountPeriod(models.Model):
    _name = 'ps.account.period'
    _description = _('Accounting Period')
    _order = 'year,period asc'

    company_id = fields.Many2one('res.company', string=_('Company'), required=True,
                                 default=lambda self: self.env.user.company_id)
    fiscalyear_id = fields.Many2one('ps.account.fiscalyear', ondelete='cascade', string=_('Year ID'), required=True,
                                    index=True)
    year = fields.Char(related="fiscalyear_id.name", string=_('Year'), store=True, readonly=True)
    period = fields.Char(string=_('Period'), size=2, default='00')
    date_start = fields.Date(string=_('Start Date'), required=True)
    date_end = fields.Date(string=_('End Date'), required=True)
    financial_state = fields.Selection([('0', _('Open')), ('1', _('Current')), ('2', _('Archived'))], string=_('Financial Status'), default='0',
                                       readonly=True)

    #
    # 返回1 当前期间 用来设置默认期间
    # 返回2 当前会计年度的所有期间 设置选择项
    #
    def get_current_period(self):
        # 当前时间
        current_date = datetime.today().strftime("%Y-%m-%d")
        current_period = self.search([('date_start', '<=', current_date), ('date_end', '>=', current_date)])
        if len(current_period) == 0:
            return False
        if len(current_period) > 1:
            raise ValidationError(_('There are multiple periods, please modify the period first.'))
        # 默认会计区间
        default_year = current_period[0].year
        default_period = current_period[0].period
        default_period_code = default_year + default_period
        default_id = current_period[0].id
        # 当前会计年度所有区间
        periods = []
        period_ids = self.env['ps.account.period'].search([('year', '=', default_year)])
        if period_ids:
            for period_id in period_ids:
                record_period = period_id.period
                record_period_code = default_year + record_period
                periods.append([record_period_code, record_period_code])
        return default_period_code, periods, default_id

    def _get_next_period_code(self, year_id):
        period_ids = self.search([('fiscalyear_id', '=', year_id)])
        period_len = len(period_ids)
        if period_len == 0:
            return '01'
        else:
            return str(period_len + 1).zfill(2)

    def _check_period(self, periodcode):
        if len(periodcode) != 2:
            raise ValidationError(_('Please enter the 2-digit period number.'))
        try:
            num = int(periodcode)
            return True
        except:
            raise ValidationError(_('The input number is not in accordance with the rules.'))

    @api.model
    def create(self, vals):
        if self._check_period(vals['period']):
            if not self.env.user.company_id.ps_account_begin_date:
                self.env.user.company_id.ps_account_begin_date = vals['date_start']
            # 只要生成了期间，年度的状态就是启用
            self.env['ps.account.fiscalyear'].search([('id', '=', vals['fiscalyear_id'])]).write({'state': '1'})
            if not self.env.user.company_id.ps_current_fiscalyear:
                year_res = self.env['ps.account.fiscalyear'].search([('id', '=', vals['fiscalyear_id'])], limit=1)
                self.env.user.company_id.ps_current_fiscalyear = year_res.name + vals['period']
                vals.update({'financial_state': '1'})
            rec = super(PsAccountPeriod, self).create(vals)
            return rec

    @api.multi
    def unlink(self):
        for r in self:
            if r.financial_state != '0':
                raise ValidationError(
                    _('The period has been used and cannot be deleted.'))
        return super(PsAccountPeriod, self).unlink()

    @api.model
    def get_period(self, date):
        """
        :param string date: the date to get the account'year and period.
        :return: the record of the model, or ``False`` if it does not exist.
        """
        res = self.search([('date_start', '<=', date), ('date_end', '>=', date)])
        if len(res) == 0:
            return False
        return res

    @api.model
    def get_all_period1(self):
        # 取当前会计年度
        cur_kjqj = self.env.user.company_id.ps_current_fiscalyear
        if not cur_kjqj:
            return []

        cur_year = cur_kjqj[0:4]
        sql = """select period||'期 - '||date_part('month',date_start)||'月' 期间,year||period 期间值 ,financial_state,year from ps_account_period  
                            order by year,period 
                          """
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        ids_data = []
        ids_month_data = []
        lastyear = ''
        for record in temp_ids:
            if lastyear != record[3]:
                lastyear = record[3]
                ids_month_data = []
                if lastyear == cur_year:
                    # 当前年度
                    ids_data.append({'year': lastyear, 'state': '1', 'month': ids_month_data})
                else:
                    ids_data.append({'year': lastyear, 'state': '0', 'month': ids_month_data})
            ids_month_data.append({
                'displayname': record[0],
                'value': record[1],
                'state': record[2],
            })
        return ids_data

    @api.model
    def get_all_period(self):
        # 取当前会计年度
        cur_kjqj = self.env.user.company_id.ps_current_fiscalyear
        if not cur_kjqj:
            raise UserError(_('There is no activated period yet, please enable it in the accounting period function.'))

        cur_year = cur_kjqj[0:4]
        sql = """select period||'期 - '||date_part('month',date_start)||'月' 期间,year||period 期间值 ,financial_state,year from ps_account_period  
                    order by year,period 
                  """
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        ids_data = []
        ids_month_data = []
        lastyear = ''
        for record in temp_ids:
            if lastyear != record[3]:
                lastyear = record[3]
                ids_month_data = []
                if lastyear == cur_year:
                    # 当前年度
                    ids_data.append({'year': lastyear, 'state': '1', 'month': ids_month_data})
                else:
                    ids_data.append({'year': lastyear, 'state': '0', 'month': ids_month_data})
            ids_month_data.append({
                'displayname': record[0],
                'value': record[1],
                'state': record[2],
            })
        return ids_data

    @api.multi
    @api.depends('period', 'year')
    def name_get(self):
        result = []
        for item in self:
            name = item.year + '年 ' + item.period + '期'
            result.append((item.id, name))
        return result

    @api.model
    def get_yearperiod(self, date):
        res = self.search([('date_start', '<=', date), ('date_end', '>=', date)])
        if len(res) == 0:
            return False
        return res.year + res.period