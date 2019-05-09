# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class PsMrpInventoryWizard(models.TransientModel):
    _name = 'ps.mrp.inventory.wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period',
                                domain=[('financial_state', 'in', ['1', '0'])],
                                default=lambda self: self.env['ps.account.period'].search(
                                    [('financial_state', '=', '1')]))  # 期间
    lines_ids = fields.One2many('ps.mrp.inventory.line.wizard', 'line_id')
    state = fields.Selection([
        ('draft', 'Created'),
        ('confirm', 'Confirmed')], default='draft', string='Mrp State')
    name = fields.Char()

    def confirm(self):
        self.ensure_one()
        if not self.lines_ids:
            raise ValidationError(_('The record is empty and cannot be confirmd.'))
        if self.lines_ids:
            for r in self.lines_ids:
                pmi = self.env['ps.mrp.inventory'].search([('name', '=', r.name)])
                if pmi:
                    pmi.write({'product_inventory_qty': r.product_inventory_qty,
                               'product_qty': r.product_qty,
                               'state': r.state,
                               'picking_type_id': r.picking_type_id,
                               'picking_type_name': r.picking_type_name
                    })
                else:
                    self.env['ps.mrp.inventory'].create({
                        'product_id': r.product_id,
                        'mrp_cost_accounting_id': r.mrp_cost_accounting_id,
                        'name': r.name,
                        'product_qty': r.product_qty,
                        'product_inventory_qty': r.product_inventory_qty,
                        'picking_type_id': r.picking_type_id,
                        'picking_type_name': r.picking_type_name,
                        'state': r.state,
                        'period_id': self.period_id.id
                    })
            self.write({'state': 'confirm'})


    @api.multi
    def refresh_data(self):
        self.ensure_one()
        self.name = "在产品盘点录入"
        if not self.period_id:
            raise ValidationError(_('Please select the account period.'))  #请选择开始和结束日期

        if self.lines_ids:
            self.lines_ids.unlink()
        sql = """select routing_id,product_id,picking_type_id,name,product_qty,state
                 from mrp_production 
        		 where state <> 'confirmed' And state <> 'cancel' And date_planned_start >= '""" + str(self.period_id.date_start) + """' and date_planned_start <= '""" + str(self.period_id.date_end) + """'
        		        order by date_planned_start
        		 """
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()

        mrp_cost_accounting_id = 0
        mrp_cost_accounting_name = ''
        product_id = 0
        product_name = ''
        picking_type_id = 0
        picking_type_name = ''
        state_name = ''
        if temp_ids:
            item_data = []
            for item in temp_ids:
                if item[0]:
                    workcenter_id = self.env['mrp.routing.workcenter'].search([('routing_id', '=', item[0])]).workcenter_id
                    if workcenter_id:
                        rec = self.env['ps.mrp.cost.accounting'].search([('workcenter_id', '=', workcenter_id.id)])
                        # sql = """Select id,name From ps_mrp_cost_accounting	WHere workcenter_id = %s """ % (workcenter_id.id)
                        if rec:
                            mrp_cost_accounting_id = rec.id
                            mrp_cost_accounting_name = rec.name
                else:
                    mrp_cost_accounting_id = 0
                    mrp_cost_accounting_name = ''
                if item[1]:
                    if self.env['product.template'].browse(item[1]):
                        product_id = item[1]
                        product_name = self.env['product.template'].browse(item[1]).name
                    else:
                        product_id = 0
                        product_name = ''
                if item[2]:
                    if self.env['stock.picking.type'].browse(item[1]):
                        picking_type_id = item[2]
                        picking_type_name = self.env['stock.picking.type'].browse(item[1]).name
                        if self.env.user.partner_id.lang and self.env.user.partner_id.lang == 'zh_CN':
                            r = self.env['ir.translation'].search([('src', '=', picking_type_name)])
                            if r:
                                picking_type_name = r[0].value
                            else:
                                picking_type_name = ''
                    else:
                        picking_type_id = 0
                        picking_type_name = ''
                state_name = item[5]
                if state_name != 'done':
                    sql = """Select sml.qty_done
                             From stock_move_line sml,stock_location sl
                             Where sml.reference = '%s' And 
                             sml.location_dest_id = sl.id And
	                         sl.usage = 'internal'
                            		 """ % (item[3])
                    self.env.cr.execute(sql)
                    r = self.env.cr.fetchone()
                    if r:
                        product_qty = item[4] - r[0]
                    else:
                        product_qty = item[4]
                else:
                    product_qty = 0
                item_data.append((0, 0, {
                    'product_name': product_name,
                    'product_id': product_id,
                    'mrp_cost_accounting_name': mrp_cost_accounting_name,
                    'mrp_cost_accounting_id': mrp_cost_accounting_id,
                    'name': item[3],
                    'product_qty': product_qty,
                    'picking_type_name': picking_type_name,
                    'picking_type_id': picking_type_id,
                    'state': state_name
                }))
            self.lines_ids = item_data
        return True


class PsMrpInventoryLineWizard(models.TransientModel):
    _name = 'ps.mrp.inventory.line.wizard'

    line_id = fields.Many2one('ps.mrp.inventory.wizard')
    product_id = fields.Integer()
    product_name = fields.Char(string='Product')
    mrp_cost_accounting_id = fields.Integer()
    mrp_cost_accounting_name = fields.Char(string='Mrp Cost Accounting')
    name = fields.Char('Reference')
    product_qty = fields.Float(
        'Quantity To Produce', digits=dp.get_precision('Product Unit of Measure'))
    product_inventory_qty = fields.Float(string='Inventory QTY', digits=dp.get_precision('Product Unit of Measure'))
    picking_type_id = fields.Integer()
    picking_type_name = fields.Char(string='Operation Type')
    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='Mrp State')

    @api.constrains('product_inventory_qty')
    def _check_product_inventory_qty(self):
        for r in self:
            if r.product_inventory_qty < 0:
                raise ValidationError(_('The number of discs should not be less than 0.'))#盘点数量不能小于0


class PsMrpExpenseDistributionWizard(models.TransientModel):
    _name = 'ps.mrp.expense.distribution.wizard'

    period_id = fields.Many2one('ps.account.period', string='Account Period',
                                domain=[('financial_state', 'in', ['1', '0'])],
                                default=lambda self: self.env['ps.account.period'].search(
                                    [('financial_state', '=', '1')]))  # 期间


    def confirm(self):
        if self.period_id:
            sql = """select a.period_id,a.cost_account_id,b.cost_item_id,sum(a.amount) 
                     from ps_mrp_expenses_pull a, ps_mrp_expense_item b
                     Where a.period_id = %s And
	                       a.expenses_id = b.id And
	                       b.cost_item_id is not null 								
                     group by a.period_id ,a.cost_account_id ,b.cost_item_id	
                  """ % (self.period_id.id)
            self.env.cr.execute(sql)
            recs = self.env.cr.fetchall()
            print(recs)
            #
            #
            # sql_mrp = """
            #         SELECT SUM(product_qty)
            #         FROM mrp_production
            #         WHERE state = 'done'
            #             AND date_planned_start BETWEEN %s AND %s
            #             AND product_id = %s
            #             AND routing_id IN (
            #                 SELECT routing_id
            #                 FROM mrp_routing_workcenter
            #                 WHERE workcenter_id IN (
            #                     SELECT mrp_workcenter_id
            #                     FROM mrp_workcenter_ps_mrp_cost_accounting_rel
            #                     WHERE ps_mrp_cost_accounting_id = %s
            #                 )
            #             )
            #       """ %



