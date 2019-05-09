# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.exceptions import ValidationError

from odoo import models, api, fields, _


class PsCheckPostAccountMove(models.TransientModel):
    _name = "ps.check.outbound.cost.calculation"
    _description = "Check Outbound Cost Calculation"

    @api.model
    def get_currentperiod(self):
        if self.env["ps.account.period"].get_current_period():
            return self.env['ps.account.period'].get_current_period()[0]
        else:
            raise ValidationError(
                _('Did not find the corresponding accounting period, please maintain the period first!'))

    # recalc:0显示已有数据，1计算，默认显示已有数据
    @api.multi
    def outbound_cost_recalculation(self):
        fyearperiod = self.get_currentperiod()
        period = self._context.get('period', fyearperiod)
        return {
            'type': 'ir.actions.client',
            'tag': 'outbound_cost_calculation_widget',
            'name': _('Outbound Cost Calculation'),
            'context': {'model': 'outbound.cost.calculation.report', 'recalc': '1', 'period': period},
            'target': 'current',
        }

    @api.multi
    def outbound_cost_recalculation_cancel(self):
        fyearperiod = self.get_currentperiod()
        period = self._context.get('period', fyearperiod)
        return {
            'type': 'ir.actions.client',
            'tag': 'outbound_cost_calculation_widget',
            'name': _('Outbound Cost Calculation'),
            'context': {'model': 'outbound.cost.calculation.report', 'recalc': '0', 'period': period},
            'target': 'current',
        }


# 出库成本计算功能主类
class PsOutboundCostCalculation(models.TransientModel):
    _name = 'ps.outbound.cost.calculation'
    _description = _('Outbound Cost Calculation')

    def _current_period(self):
        if self.env["ps.account.period"].get_current_period():
            return self.env["ps.account.period"].get_current_period()[0]

    account_period = fields.Selection(selection='_get_account_periods', string=_('Account Period'),
                                      default=_current_period, required=True)

    def _get_account_periods(self):
        if self.env["ps.account.period"].get_current_period():
            return self.env["ps.account.period"].get_current_period()[1]

    @api.multi
    def confirm_set_button(self):
        account_period = self.env.context.get('account_period')
        # 根据选择的会计区间，如果会计区间存在记录，显示，如果会计区间不存在记录，不显示
        if account_period:
            fiscal_year = account_period[0:4]
            fiscal_period = account_period[4:6]
            outbound_cost_calculation_ids = self.env['ps.stock.material.balance.table'].search(
                [('accounting_period_id.year', '=', fiscal_year), ('accounting_period_id.period', '=', fiscal_period)])
            if outbound_cost_calculation_ids:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Check Outbound Cost Calculation'),
                    'view_mode': 'form',
                    'res_model': 'ps.check.outbound.cost.calculation',
                    'target': 'new',
                    'context': {'period': account_period},
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'outbound_cost_calculation_widget',
                    'name': _('Outbound Cost Calculation'),
                    'context': {'model': 'outbound.cost.calculation.report', 'recalc': '1', 'period': account_period},
                    'target': 'current',
                }
        else:
            return {'type': 'ir.actions.act_window_close'}
