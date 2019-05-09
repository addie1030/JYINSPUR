# -*- coding: utf-8 -*-

import time
import math
from collections import defaultdict

from datetime import datetime
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round
from odoo.tools import float_is_zero


class PsStockMove(models.Model):
    _inherit = 'stock.move'

    account_move_id = fields.Integer(string=_('Certificate ID'), default=0)


    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        AccountMove = self.env['account.move']
        move_lines = self._prepare_account_move_line(self.product_qty, abs(self.value), credit_account_id,
                                                     debit_account_id)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': self.picking_id.name,
                'stock_move_id': self.id,
            })

    def _create_account_move_lines(self, credit_account_id, debit_account_id, journal_id):  # 处理合并
        self.ensure_one()
        move_lines = self._prepare_account_move_line(self.product_qty, abs(self.value), credit_account_id,
                                                     debit_account_id)
        return move_lines

    def _account_entry_moves(self):
        id_list = []
        move_merge_lines = []
        move_line = []

        if len(self.env.context.get('stock_active_ids')) > 1:  # 处理合并
            strdate = self.env.context.get('stock_move_date')
            strdate = strdate[0:4] + '-' + strdate[5:7] + '-' + strdate[8:10]
            movedate = datetime.strptime(strdate, '%Y-%m-%d')
            for r in self.env.context.get('stock_active_ids'):
                id_list.append(int(r))
            moves = self.env['stock.move'].search([('id', 'in', id_list)])
            if moves:
                for move in moves:
                    location_from = move.location_id
                    location_to = move.location_dest_id
                    company_from = move._is_out() and move.mapped('move_line_ids.location_id.company_id') or False
                    company_to = move._is_in() and move.mapped('move_line_ids.location_dest_id.company_id') or False

                    # Create Journal Entry for products arriving in the company; in case of routes making the link between several
                    # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
                    if move._is_in():
                        journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                        if location_from and location_from.usage == 'customer':  # goods returned from customer
                            move_line = move.with_context(force_company=company_to.id)._create_account_move_lines(
                                acc_dest, acc_valuation, journal_id)
                        else:
                            move_line = move.with_context(force_company=company_to.id)._create_account_move_lines(
                                acc_src, acc_valuation, journal_id)

                    # Create Journal Entry for products leaving the company
                    if move._is_out():
                        journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                        if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                            move_line = move.with_context(force_company=company_from.id)._create_account_move_lines(
                                acc_valuation, acc_src, journal_id)
                        else:
                            move_line = move.with_context(force_company=company_from.id)._create_account_move_lines(
                                acc_valuation, acc_dest, journal_id)

                    if move.company_id.anglo_saxon_accounting and move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'customer':
                        # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
                        journal_id, acc_src, acc_dest, acc_valuation = move._get_accounting_data_for_valuation()
                        move_line = move.with_context(force_company=self.company_id.id)._create_account_move_lines(
                            acc_src, acc_dest, journal_id)

                    move_merge_lines = move_merge_lines + move_line

                AccountMove = self.env['account.move']
                new_account_move = AccountMove.with_context(stock_move_ids=id_list).create({
                    'journal_id': journal_id,
                    'line_ids': move_merge_lines,
                    'date': movedate,  # 来自创建凭证页面的date
                    'ref': self.picking_id.name,
                    'stock_move_id': self.id,
                })

    def _account_entry_move(self):
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False
        location_from = self.location_id
        location_to = self.location_dest_id
        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_from and location_from.usage == 'customer':  # goods returned from customer
                self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation,
                                                                                         journal_id)
            else:
                self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation,
                                                                                         journal_id)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            if location_to and location_to.usage == 'supplier':  # goods returned to supplier
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src,
                                                                                           journal_id)
            else:
                self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_dest,
                                                                                           journal_id)

        if self.company_id.anglo_saxon_accounting and self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer':
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
            self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest,
                                                                                          journal_id)


class PsStockPickingView(models.TransientModel):
    _name = 'ps.stock.picking.view'

    stock_picking_id = fields.Integer(string=_('Bill ID'))  # 单据ID
    name = fields.Char(string=_('Bill Number'))  # 单号
    location_dest_id = fields.Many2one(
        'stock.location', string=_("Library Position"))  # 库位
    partner_id = fields.Many2one(
        'res.partner', string=_('Partner'))  # 往来单位
    origin = fields.Char(string=_('Origin'))  # 源单据
    date = fields.Datetime(string=_('Bill Date'))  # 单据日期
    ref = fields.Char(string=_('Move Number'))  # 凭证编号
    move_create_id = fields.Many2one('ps.stock.picking.create.move', ondelete="cascade")


class PsStockPickingCreateMove(models.TransientModel):
    _name = 'ps.stock.picking.create.move'
    _description = 'Stock Pickings Create Move'
    _rec_name = 'picking_type_id'

    name = fields.Char(string=_('Flow Number'))  # 生成凭证的操作日志流水号，记录本次日志流水对应的库存记录
    picking_type_id = fields.Many2one('stock.picking.type', string=_('Operation Type'))  # 作业类型
    is_merge = fields.Boolean(string=_('Bill Merge'), default=False)  # 是否合并
    move_date = fields.Selection([('1', _('Document Date')), ('2', _('Move Date'))], string=_('Move Date')) # 凭证日期
    date = fields.Date(string=_('Move Date'))  # 凭证日期
    stock_picking_ids = fields.One2many('ps.stock.picking.view', 'move_create_id')

    @api.multi
    def refresh_data(self):
        self.ensure_one()
        if not self.picking_type_id:
            raise ValidationError(_('Please select picking type.'))  # 请选择作业类型

        if self.stock_picking_ids:
            self.stock_picking_ids.unlink()
        sql = """select t2.reference,t1.location_dest_id,t1.partner_id,t1.origin,t1.date ,t2.id
                 from stock_picking t1, stock_move t2
        		 where t1.id = t2.picking_id and 
        		        t1.state = 'done' and 
        		        t2.account_move_id = 0 and
        		        t1.picking_type_id = %s 
        		        order by t2.reference
        		 """ % (self.picking_type_id.id)
        self.env.cr.execute(sql)
        temp_ids = self.env.cr.fetchall()
        if temp_ids:
            if self.picking_type_id.code == 'outgoing':
                # 单据日期所在的会计区间的产品是否在ps.stock.material.balance.table表中存在记录
                exist_line = False
                for line in temp_ids:
                    product = self.env['stock.move'].search([('id', '=', line[5])]).product_id
                    if product.cost_method != 'onemonth':
                        continue
                    res = self.env['ps.account.period'].search([('date_start', '<=', line[4]), ('date_end', '>=', line[4])])
                    exist_ids = self.env['ps.stock.material.balance.table'].search(
                        [('product_id', '=', product.id),
                         ('accounting_period_id.year', '=', res.year),
                         ('accounting_period_id.period', '=', res.period),
                         ('company_id', '=', self.env.user.company_id.id)
                         ])

                    if exist_ids:
                        exist_line = True
                        break
                if not exist_line:
                    raise ValidationError(_('Please perform the outbound cost calculation first.'))  # 请首先执行出库成本计算

            item_data = []
            for item in temp_ids:
                item_data.append((0, 0, {
                    'name': item[0],
                    'location_dest_id': item[1],
                    'partner_id': item[2],
                    'origin': item[3],
                    'date': item[4],
                    'stock_picking_id': item[5]
                }))
            self.stock_picking_ids = item_data
        return True


class ProductTemplate(models.Model):
    _inherit = "product.template"
    ps_incoming_price = fields.Float(string=_('Incoming Price'), digits=dp.get_precision("Product Price"),
                                  help=_('Update incoming price of products, which did not have price on their upstream orders'))

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)'),
        ('onemonth', 'Once-month Weighted Average')], string="Costing Method",
        company_dependent=True, copy=True,
        help=_("""Standard Price: The products are valued at their standard cost defined on the product.
                Average Cost (AVCO): The products are valued at weighted average cost.
                First In First Out (FIFO): The products are valued supposing those that enter the company first will also leave it first.
                """))

    @api.one
    def _set_cost_method(self):
        # When going from FIFO to AVCO or to standard, we update the standard price with the
        # average value in stock.
        if self.property_cost_method == 'fifo' and self.cost_method in ['average', 'standard', 'onemonth']:
            # Cannot use the `stock_value` computed field as it's already invalidated when
            # entering this method.
            valuation = sum([variant._sum_remaining_values()[0] for variant in self.product_variant_ids])
            qty_available = self.with_context(company_owned=True).qty_available
            if qty_available:
                self.standard_price = valuation / qty_available
        return self.write({'property_cost_method': self.cost_method})


# 增加全月一次加权平均
class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_cost_method = fields.Selection(selection_add=[('onemonth', 'Once-month Weighted Average')])


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        for product in self:
            if product.cost_method in ['standard', 'average', 'onemonth']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        domain = [('product_id', '=', product.id),
                                  ('date', '<=', to_date)] + StockMove._get_all_base_domain()
                        moves = StockMove.search(domain)
                        product.stock_value = sum(moves.mapped('value'))
                        product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(moves.ids)
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                else:
                    product.stock_value, moves = product._sum_remaining_values()
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = moves
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.multi
    def write(self, vals):
        if 'qty_done' in vals:
            moves_to_update = {}
            for move_line in self.filtered(
                    lambda ml: ml.state == 'done' and (ml.move_id._is_in() or ml.move_id._is_out())):
                moves_to_update[move_line.move_id] = vals['qty_done'] - move_line.qty_done

            for move_id, qty_difference in moves_to_update.items():
                move_vals = {}
                if move_id.product_id.cost_method in ['standard', 'average', 'onemonth']:
                    correction_value = qty_difference * move_id.product_id.standard_price
                    if move_id._is_in():
                        move_vals['value'] = move_id.value + correction_value
                    elif move_id._is_out():
                        move_vals['value'] = move_id.value - correction_value
                else:
                    if move_id._is_in():
                        correction_value = qty_difference * move_id.price_unit
                        new_remaining_value = move_id.remaining_value + correction_value
                        move_vals['value'] = move_id.value + correction_value
                        move_vals['remaining_qty'] = move_id.remaining_qty + qty_difference
                        move_vals['remaining_value'] = move_id.remaining_value + correction_value
                    elif move_id._is_out() and qty_difference > 0:
                        correction_value = self.env['stock.move']._run_fifo(move_id, quantity=qty_difference)
                        # no need to adapt `remaining_qty` and `remaining_value` as `_run_fifo` took care of it
                        move_vals['value'] = move_id.value - correction_value
                    elif move_id._is_out() and qty_difference < 0:
                        candidates_receipt = self.env['stock.move'].search(move_id._get_in_domain(),
                                                                           order='date, id desc', limit=1)
                        if candidates_receipt:
                            candidates_receipt.write({
                                'remaining_qty': candidates_receipt.remaining_qty + -qty_difference,
                                'remaining_value': candidates_receipt.remaining_value + (
                                        -qty_difference * candidates_receipt.price_unit),
                            })
                            correction_value = qty_difference * candidates_receipt.price_unit
                        else:
                            correction_value = qty_difference * move_id.product_id.standard_price
                        move_vals['value'] = move_id.value - correction_value
                move_id.write(move_vals)

                if move_id.product_id.valuation == 'real_time':
                    move_id.with_context(force_valuation_amount=correction_value,
                                         forced_quantity=qty_difference)._account_entry_move()
                if qty_difference > 0:
                    move_id.product_price_update_before_done(forced_qty=qty_difference)
        return super(StockMoveLine, self).write(vals)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _run_valuation(self, quantity=None):
        self.ensure_one()
        if self._is_in():
            valued_move_lines = self.move_line_ids.filtered(lambda
                                                                ml: not ml.location_id._should_be_valued() and ml.location_dest_id._should_be_valued() and not ml.owner_id)
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     self.product_id.uom_id)

            # Note: we always compute the fifo `remaining_value` and `remaining_qty` fields no
            # matter which cost method is set, to ease the switching of cost method.
            vals = {}
            price_unit = self._get_price_unit()
            value = price_unit * (quantity or valued_quantity)
            vals = {
                'price_unit': price_unit,
                'value': value if quantity is None or not self.value else self.value,
                'remaining_value': value if quantity is None else self.remaining_value + value,
            }
            vals['remaining_qty'] = valued_quantity if quantity is None else self.remaining_qty + quantity

            if self.product_id.cost_method == 'standard':
                value = self.product_id.standard_price * (quantity or valued_quantity)
                vals.update({
                    'price_unit': self.product_id.standard_price,
                    'value': value if quantity is None or not self.value else self.value,
                })
            self.write(vals)
        elif self._is_out():
            valued_move_lines = self.move_line_ids.filtered(lambda
                                                                ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     self.product_id.uom_id)
            self.env['stock.move']._run_fifo(self, quantity=quantity)
            if self.product_id.cost_method in ['standard', 'average', 'onemonth']:
                curr_rounding = self.company_id.currency_id.rounding
                value = -float_round(
                    self.product_id.standard_price * (valued_quantity if quantity is None else quantity),
                    precision_rounding=curr_rounding)
                self.write({
                    'value': value if quantity is None else self.value + value,
                    'price_unit': value / valued_quantity,
                })
        elif self._is_dropshipped() or self._is_dropshipped_returned():
            curr_rounding = self.company_id.currency_id.rounding
            if self.product_id.cost_method in ['fifo']:
                price_unit = self._get_price_unit()
                # see test_dropship_fifo_perpetual_anglosaxon_ordered
                self.product_id.standard_price = price_unit
            else:
                price_unit = self.product_id.standard_price
            value = float_round(self.product_qty * price_unit, precision_rounding=curr_rounding)
            # In move have a positive value, out move have a negative value, let's arbitrary say
            # dropship are positive.
            self.write({
                'value': value if self._is_dropshipped() else -value,
                'price_unit': price_unit if self._is_dropshipped() else -price_unit,
            })

    @api.multi
    def product_price_update_before_done(self, forced_qty=None):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(lambda move: move.location_id.usage in (
                'supplier', 'production') and move.product_id.cost_method in ['average', 'onemonth']):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            qty_done = 0.0
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                    float_is_zero(product_tot_qty_available + qty_done, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                amount_unit = std_price_update.get(
                    (move.company_id.id, move.product_id.id)) or move.product_id.standard_price
                qty_done = move.product_uom._compute_quantity(move.quantity_done, move.product_id.uom_id)
                qty = forced_qty or qty_done
                new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (
                        product_tot_qty_available + qty_done)

            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write(
                {'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price
