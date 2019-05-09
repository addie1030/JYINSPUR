# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo import tools


class PsStockCreateAccountMove(models.TransientModel):
    _name = "ps.stock.create.account.move"
    _description = _("Inventory document generation voucher")

    @api.multi
    def stock_create_account_move(self):
        context = dict(self._context or {})
        id_list = []
        id_uncheck_list = []
        id_default_list = []
        is_merge = context.get('stock_is_merge')
        if len(context.get('stock_active_ids')) > 0:
            for r in context.get('stock_active_ids'):
                id_list.append(int(r))

        if is_merge == '0':  # 不合并
            moves = self.env['stock.move'].search([('id', 'in', id_list)])
            if moves:
                for move in moves:
                    if move.product_id.type != 'product':
                        raise UserError(_('The product type of the document of the certificate: ') + move.reference + _(
                            'is not [in stockable product], and the certificate cannot be generated.'))
                    if move.account_move_id > 0:
                        raise UserError(_('The product type of the document of the certificate: ' + moves[
                            0].reference + 'has been generated!'))
                    if move.state == 'done':
                        res = self.env['stock.move.line'].search([('move_id', '=', move.id)])
                        # correction_value = move._run_valuation(res.qty_done)  force_valuation_amount=correction_value,
                        move.with_context(stock_move_id=move.id)._account_entry_move()
        if is_merge == '1':  # 合并
            if len(context.get('stock_active_ids')) < 2:
                raise UserError(_('Please check at least two records to be merged.'))
            if len(context.get('stock_move_date')) < 1:
                raise UserError(_('Please select the date of the voucher.'))
            else:
                movedate = context.get('stock_move_date')
            self.env['stock.move'].with_context(stock_is_merge='1', stock_move_date=movedate,
                                                stock_active_ids=id_list)._account_entry_moves()

        return {'type': 'ir.actions.act_window_close'}


class PsInvoiceStockMoveValidate(models.TransientModel):
    _name = "ps.invoice.stock.move.validate"

    def get_invoice_line_validate_qty(self, id):
        recs = self.env['ps.invoice.line.stock.move.recs'].search([('invoice_line_id', '=', id)])
        total = 0
        if recs:
            for r in recs:
                if r.invoice_line_validate_qty:
                    total = total + r.invoice_line_validate_qty
        return total

    def get_stock_move_validate_qty(self, id):
        recs = self.env['ps.invoice.line.stock.move.recs'].search([('stock_move_id', '=', id)])
        total = 0
        if recs:
            for r in recs:
                if r.stock_move_validate_qty:
                    total = total + r.stock_move_validate_qty
        return total

    def _create_validate_move(self, product_id, qty, price, stock_move_type):
        """
        :param product_id: 产品ID
        :param qty: 核销数量
        :param price: 入库核销：价格差=发票单价-入库单价；出库核销：价格
        :param stock_move_type :库存单据类型：in:入库单；out:出库单
        :return: 返回凭证
        """

        credit_account_id = 0
        debit_account_id = 0

        rec_pp = self.env['product.product'].browse(product_id)
        if stock_move_type == 'in': #入库单核销
            debit_account_id = rec_pp.categ_id.property_stock_valuation_account_id.id #借方科目
            credit_account_id = rec_pp.categ_id.property_stock_account_input_categ_id.id #贷方科目

        elif stock_move_type == 'out': #出库单核销
            credit_account_id = rec_pp.categ_id.property_stock_account_output_categ_id.id  # 贷方科目
            debit_account_id = self.env.user.company_id.cogs_account_id.id  # 借方科目,公司维护的主营业务成本科目



        if not credit_account_id or not debit_account_id:
            if stock_move_type == 'in':
                raise UserError(_('Please maintain the subject on the product category.'))#在产品类别上维护科目
            else:
                raise UserError(_('Please maintain the subject on the product category and the company.'))  # 在产品类别上与公司上维护科目

        debit_line_vals = {
            'name': rec_pp.name,
            'product_id': product_id,
            'quantity': qty,
            'product_uom_id': rec_pp.uom_id.id,
            'debit': qty * price,
            'account_id': debit_account_id,
        }
        credit_line_vals = {
            'name': rec_pp.name,
            'product_id': product_id,
            'quantity': qty,
            'product_uom_id': rec_pp.uom_id.id,
            'credit': qty * price,
            'account_id': credit_account_id,
        }
        move_lines = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

        am = self.env['account.move']
        if move_lines:
            return am.create({
                'journal_id': rec_pp.categ_id.property_stock_journal.id,
                'line_ids': move_lines,
                'date': fields.Date.today(),
            })


    @api.multi
    def invoic_stock_move_validate(self):
        context = dict(self._context or {})
        validate_type = context.get('validate_type')
        if validate_type == 'auto':
            invoice_active_ids = list(map(int, context.get('invoice_active_ids')))
            stock_move_active_ids = list(map(int, context.get('stock_move_active_ids')))
            L = len(stock_move_active_ids)
        elif validate_type == 'manual':
            invoice_active_ids = list(map(int, context.get('invoice_active_ids')))
            dic_stock_moves = context.get('dic_stock_moves')
            stock_move_active_ids = sorted(list(map(int, dic_stock_moves.keys())))
            L = len(stock_move_active_ids)

        smt = context.get('stock_move_type')
        if len(smt) == 4:
            stock_move_type = 'in'
        elif len(smt) == 5:
            stock_move_type = 'out'

        ail = self.env['account.invoice.line']
        sm = self.env['stock.move']
        psmlv = self.env['ps.stock.move.line.view']
        pailv = self.env['ps.account.invoice.line.view']
        am = self.env['account.move']
        i = 0
        j = 0
        qty_ail = 0
        qty_sm = 0
        un_qty_sm = 0
        qty_tmp_ail = 0
        qty_tmp_sm = 0
        qty_sm_validate = 0
        qty_ail_validate = 0
        flag_move = True
        flag_invoice = True
        key_sm_id = ''
        qty_tmp_ail_dict = {}
        qty_tmp_sm_dict = {}

        move_id = 0
        price_diff = 0.00

        if len(invoice_active_ids) > 0 and L > 0:
            if validate_type == 'auto':  # 自动核销
                while len(invoice_active_ids) > 0 and i < len(invoice_active_ids) and j < L:
                    if flag_invoice:
                        r_inv_id = invoice_active_ids[i]
                        qty_ail_validate = self.get_invoice_line_validate_qty(r_inv_id)  # 取本单据已经核销的数量
                        rec_inv = ail.search([('id', '=', r_inv_id)])
                        rec_pailv = pailv.search([('ps_invoice_line_id', '=', r_inv_id)])
                    while len(stock_move_active_ids) > 0 and j < len(stock_move_active_ids):
                        if flag_move:
                            r_sm_id = stock_move_active_ids[j]
                            qty_sm_validate = self.get_stock_move_validate_qty(r_sm_id)  # 取本单据已经核销的数量
                            rec_sm = sm.search([('id', '=', r_sm_id)])
                            rec_psmlv = psmlv.search([('ps_stock_move_id', '=', r_sm_id)])
                        if rec_inv and rec_sm:
                            if flag_invoice:
                                qty_ail = rec_inv.ps_uncancelled_quantity
                            if flag_move:
                                qty_sm = rec_sm.ps_uncancelled_quantity
                            if rec_inv.invoice_id.origin:  # 如果有订单号，就按照订单号来核销
                                if rec_sm.origin:  # 如果有订单号，就按照订单号来核销
                                    if rec_inv.invoice_id.origin == rec_sm.origin and rec_inv.product_id.id == rec_sm.product_id.id:  # 订单号相等，产品相等
                                        if qty_ail > qty_sm:  # 发票未核销数量大于入库单未核销数量
                                            sm_qty_recs = qty_sm

                                            if stock_move_type == 'in':
                                                price_diff = rec_inv.price_unit - rec_sm.price_unit #价格差
                                                if abs(price_diff): #有价格差，则生成价格差异凭证
                                                    move = self._create_validate_move(rec_inv.product_id.id, sm_qty_recs, price_diff, stock_move_type)
                                                    if move:
                                                        move_id = move.id
                                            elif stock_move_type == 'out':#出库核销生成凭证
                                                move = self._create_validate_move(rec_inv.product_id.id,
                                                                                          sm_qty_recs, rec_sm.price_unit,
                                                                                          stock_move_type)
                                                if move:
                                                    move_id = move.id

                                            if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                                qty_tmp_ail_dict[str(rec_inv.id)] = qty_tmp_ail_dict[
                                                                                        str(rec_inv.id)] + qty_sm
                                            else:
                                                qty_tmp_ail_dict[str(rec_inv.id)] = qty_sm
                                            qty_tmp_sm = qty_tmp_ail_dict[str(rec_inv.id)]
                                            if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                                qty_sm = qty_sm + qty_tmp_sm_dict[str(rec_sm.id)]
                                            rec_pailv.write({'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate,
                                                             'ps_uncancelled_quantity': rec_inv.quantity - qty_tmp_sm - qty_ail_validate})
                                            rec_psmlv.write({'ps_cancelled_quantity': qty_sm + qty_sm_validate,

                                                             'ps_uncancelled_quantity': 0})
                                            rec_inv.write({
                                                'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate})  # 用入库单上的未核销数更新采购发票上的核销数 + 已经核销过的数
                                            rec_sm.write(
                                                {
                                                    'ps_cancelled_quantity': qty_sm + qty_sm_validate})  # 更新入库单的核销数，为入库单的未核销数
                                            values = {'invoice_line_id': rec_inv.id,
                                                      'invoice_line_qty': rec_inv.quantity,
                                                      'invoice_line_validate_qty': sm_qty_recs,
                                                      'invoice_line_validate_value': sm_qty_recs * rec_inv.price_unit,
                                                      'stock_move_id': rec_sm.id,
                                                      'stock_move_qty': rec_sm.product_qty,
                                                      'stock_move_validate_qty': sm_qty_recs,
                                                      'stock_move_validate_value': sm_qty_recs * rec_sm.price_unit,
                                                      'operation_date': fields.Date.today(),
                                                      'move_id': move_id,
                                                      'origin': stock_move_type
                                                      }
                                            self.env['ps.invoice.line.stock.move.recs'].create(values)
                                            qty_ail = qty_ail - sm_qty_recs  # 未核销数量
                                            flag_move = True
                                            flag_invoice = False
                                            j = j + 1
                                            if j < L:
                                                continue
                                            else:
                                                break
                                        elif qty_ail < qty_sm:  # 发票未核销数量小于入库单未核销数量
                                            ail_qty_recs = qty_ail

                                            if stock_move_type == 'in':
                                                price_diff = rec_inv.price_unit - rec_sm.price_unit #价格差
                                                if abs(price_diff): #有价格差，则生成价格差异凭证
                                                    move = self._create_validate_move(rec_inv.product_id.id, ail_qty_recs, price_diff, stock_move_type)
                                                    if move:
                                                        move_id = move.id
                                            elif stock_move_type == 'out': #出库核销生成凭证
                                                move = self._create_validate_move(rec_inv.product_id.id,
                                                                                          ail_qty_recs, rec_sm.price_unit,
                                                                                          stock_move_type)
                                                if move:
                                                    move_id = move.id

                                            if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                                qty_tmp_sm_dict[str(rec_sm.id)] = qty_tmp_sm_dict[
                                                                                      str(rec_sm.id)] + qty_ail
                                            else:
                                                qty_tmp_sm_dict[str(rec_sm.id)] = qty_ail
                                            qty_tmp_ail = qty_tmp_sm_dict[str(rec_sm.id)]
                                            if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                                qty_ail = qty_ail + qty_tmp_ail_dict[str(rec_inv.id)]

                                            rec_pailv.write({'ps_cancelled_quantity': qty_ail + qty_ail_validate,
                                                             'ps_uncancelled_quantity': 0})
                                            rec_psmlv.write({'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate,
                                                             'ps_uncancelled_quantity': rec_sm.product_qty - qty_tmp_ail - qty_sm_validate})
                                            rec_inv.write(
                                                {
                                                    'ps_cancelled_quantity': qty_ail + qty_ail_validate})  # 更新采购发票上的核销数,为采购发票的未核销数
                                            rec_sm.write(
                                                {
                                                    'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate})  # 更新入库单的核销数，为采购发票的未核销数之和
                                            values = {'invoice_line_id': rec_inv.id,
                                                      'invoice_line_qty': rec_inv.quantity,
                                                      'invoice_line_validate_qty': ail_qty_recs,
                                                      'invoice_line_validate_value': ail_qty_recs * rec_inv.price_unit,
                                                      'stock_move_id': rec_sm.id,
                                                      'stock_move_qty': rec_sm.product_qty,
                                                      'stock_move_validate_qty': ail_qty_recs,
                                                      'stock_move_validate_value': ail_qty_recs * rec_sm.price_unit,
                                                      'operation_date': fields.Date.today(),
                                                      'move_id': move_id,
                                                      'origin': stock_move_type
                                                      }
                                            self.env['ps.invoice.line.stock.move.recs'].create(values)
                                            i = i + 1
                                            qty_sm = qty_sm - ail_qty_recs  # 未核销数量
                                            flag_invoice = True
                                            flag_move = False
                                            break  # 跳出本次循环
                                        elif qty_ail == qty_sm:  # 发票未核销数量等于入库单未核销数量

                                            if stock_move_type == 'in':
                                                price_diff = rec_inv.price_unit - rec_sm.price_unit #价格差
                                                if abs(price_diff): #有价格差，则生成价格差异凭证
                                                    move = self._create_validate_move(rec_inv.product_id.id, qty_ail,
                                                                                      price_diff, stock_move_type)
                                                    if move:
                                                        move_id = move.id
                                            elif stock_move_type == 'out': #出库核销生成凭证
                                                move = self._create_validate_move(rec_inv.product_id.id,
                                                                                          qty_ail, rec_sm.price_unit,
                                                                                          stock_move_type)
                                                if move:
                                                    move_id = move.id

                                            if flag_invoice:  # 最后一行取得是发票
                                                if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                                    qty_tmp_ail = qty_tmp_sm_dict[str(rec_sm.id)] + qty_sm
                                                else:
                                                    qty_tmp_ail = qty_sm
                                                rec_pailv.write({'ps_cancelled_quantity': qty_ail + qty_ail_validate,
                                                                 'ps_uncancelled_quantity': 0})
                                                rec_inv.write(
                                                    {
                                                        'ps_cancelled_quantity': qty_ail + qty_ail_validate})  # 更新采购发票上的核销数,为采购发票的未核销数
                                                rec_psmlv.write({'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate,
                                                                 'ps_uncancelled_quantity': 0})
                                                rec_sm.write(
                                                    {
                                                        'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate})  # 更新入库单的核销数，为采购发票的合计
                                            elif flag_move:  # 最后一行取得是入库单
                                                if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                                    qty_tmp_sm = qty_tmp_ail_dict[str(rec_inv.id)] + qty_sm
                                                else:
                                                    qty_tmp_sm = qty_sm
                                                rec_pailv.write({'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate,
                                                                 'ps_uncancelled_quantity': 0})
                                                rec_inv.write(
                                                    {
                                                        'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate})  # 更新采购发票上的核销数,为入库单的合计
                                                rec_psmlv.write({'ps_cancelled_quantity': qty_sm + qty_sm_validate,
                                                                 'ps_uncancelled_quantity': 0})
                                                rec_sm.write(
                                                    {
                                                        'ps_cancelled_quantity': qty_sm + qty_sm_validate})  # 更新入库单的核销数，为入库单的未核销数
                                            values = {'invoice_line_id': rec_inv.id,
                                                      'invoice_line_qty': rec_inv.quantity,
                                                      'invoice_line_validate_qty': qty_ail,
                                                      'invoice_line_validate_value': qty_ail * rec_inv.price_unit,
                                                      'stock_move_id': rec_sm.id,
                                                      'stock_move_qty': rec_sm.product_qty,
                                                      'stock_move_validate_qty': qty_sm,
                                                      'stock_move_validate_value': qty_sm * rec_sm.price_unit,
                                                      'operation_date': fields.Date.today(),
                                                      'move_id': move_id,
                                                      'origin': stock_move_type
                                                      }
                                            self.env['ps.invoice.line.stock.move.recs'].create(values)
                                            i = i + 1
                                            j = j + 1
                                            flag_invoice = True
                                            flag_move = True
                                            break  # 跳出本次循环
                                    else:
                                        flag_move = True
                                        j = j + 1
                                        if j < L:
                                            continue  # 订单号不相等，内循环继续往下走
                                        else:
                                            flag_move = True
                                            j = 0
                                            flag_invoice = True
                                            i = i + 1
                                            break
                                else:  # 内层循环没有订单号
                                    j = j + 1
                                    flag_move = True
                                    if j < L:
                                        continue
                                    else:
                                        flag_move = True
                                        j = 0
                                        flag_invoice = True
                                        i = i + 1
                                        break
                            else:  # 外层循环没有订单号，跳出本次循环
                                flag_move = True
                                flag_invoice = True
                                i = i + 1
                                j = 0  # 内侧循环从第一条开始
                                break  # 跳出本次循环
            elif validate_type == 'manual':  # 手工核销
                while len(invoice_active_ids) > 0 and i < len(invoice_active_ids) and j < L:
                    if flag_invoice:
                        r_inv_id = invoice_active_ids[i]
                        qty_ail_validate = self.get_invoice_line_validate_qty(r_inv_id)  # 取本单据已经核销的数量
                        rec_inv = ail.search([('id', '=', r_inv_id)])
                        rec_pailv = pailv.search([('ps_invoice_line_id', '=', r_inv_id)])
                    while len(stock_move_active_ids) > 0 and j < len(stock_move_active_ids):
                        if flag_move:
                            r_sm_id = stock_move_active_ids[j]
                            key_sm_id = str(r_sm_id)
                            qty_sm_validate = self.get_stock_move_validate_qty(r_sm_id)  # 取本单据已经核销的数量
                            rec_sm = sm.search([('id', '=', r_sm_id)])
                            rec_psmlv = psmlv.search([('ps_stock_move_id', '=', r_sm_id)])
                        if rec_inv and rec_sm:
                            if flag_invoice:
                                qty_ail = rec_inv.ps_uncancelled_quantity
                            if flag_move:
                                un_qty_sm = rec_sm.ps_uncancelled_quantity
                                qty_sm = float(dic_stock_moves[key_sm_id])
                                if qty_sm > un_qty_sm:
                                    raise UserError(_('Inbound order: ') + rec_sm.reference + _(
                                        ' [The number of write-offs] cannot be greater than [unwritten amount].'))
                            if rec_inv.product_id.id == rec_sm.product_id.id:  # 产品相等
                                if qty_ail > qty_sm:  # 发票未核销数量大于入库单未核销数量
                                    sm_qty_recs = qty_sm

                                    if stock_move_type == 'in':
                                        price_diff = rec_inv.price_unit - rec_sm.price_unit  # 价格差
                                        if abs(price_diff):  # 有价格差，则生成价格差异凭证
                                            move = self._create_validate_move(rec_inv.product_id.id, sm_qty_recs,
                                                                                      price_diff, stock_move_type)
                                            if move:
                                                move_id = move.id
                                    elif stock_move_type == 'out': #出库核销生成凭证
                                        move = self._create_validate_move(rec_inv.product_id.id,
                                                                                  sm_qty_recs, rec_sm.price_unit,
                                                                                  stock_move_type)
                                        if move:
                                            move_id = move.id

                                    if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                        qty_tmp_ail_dict[str(rec_inv.id)] = qty_tmp_ail_dict[str(rec_inv.id)] + qty_sm
                                    else:
                                        qty_tmp_ail_dict[str(rec_inv.id)] = qty_sm
                                    qty_tmp_sm = qty_tmp_ail_dict[str(rec_inv.id)]
                                    if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                        qty_sm = qty_sm + qty_tmp_sm_dict[str(rec_sm.id)]
                                    rec_pailv.write({'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate,
                                                     'ps_uncancelled_quantity': rec_inv.quantity - qty_tmp_sm - qty_ail_validate})
                                    rec_psmlv.write({'ps_cancelled_quantity': qty_sm + qty_sm_validate,
                                                     'ps_uncancelled_quantity': rec_sm.product_qty - qty_sm - qty_sm_validate})
                                    rec_inv.write({
                                        'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate})  # 用入库单上的未核销数更新采购发票上的核销数 + 已经核销过的数
                                    rec_sm.write(
                                        {'ps_cancelled_quantity': qty_sm + qty_sm_validate})  # 更新入库单的核销数，为入库单的未核销数
                                    values = {'invoice_line_id': rec_inv.id,
                                              'invoice_line_qty': rec_inv.quantity,
                                              'invoice_line_validate_qty': sm_qty_recs,
                                              'invoice_line_validate_value': sm_qty_recs * rec_inv.price_unit,
                                              'stock_move_id': rec_sm.id,
                                              'stock_move_qty': rec_sm.product_qty,
                                              'stock_move_validate_qty': sm_qty_recs,
                                              'stock_move_validate_value': sm_qty_recs * rec_sm.price_unit,
                                              'operation_date': fields.Date.today(),
                                              'move_id': move_id,
                                              'origin': stock_move_type
                                              }
                                    self.env['ps.invoice.line.stock.move.recs'].create(values)
                                    qty_ail = qty_ail - sm_qty_recs  # 未核销数量
                                    flag_move = True
                                    flag_invoice = False
                                    j = j + 1
                                    if j < L:
                                        continue
                                    else:
                                        break
                                elif qty_ail < qty_sm:  # 发票未核销数量小于入库单未核销数量
                                    ail_qty_recs = qty_ail

                                    if stock_move_type == 'in':
                                        price_diff = rec_inv.price_unit - rec_sm.price_unit  # 价格差
                                        if abs(price_diff):  # 有价格差，则生成价格差异凭证
                                            move = self._create_validate_move(rec_inv.product_id.id, ail_qty_recs,
                                                                                      price_diff, stock_move_type)
                                            if move:
                                                move_id = move.id
                                    elif stock_move_type == 'out': #出库核销生成凭证
                                        move = self._create_validate_move(rec_inv.product_id.id,
                                                                                  ail_qty_recs, rec_sm.price_unit,
                                                                                  stock_move_type)
                                        if move:
                                            move_id = move.id

                                    if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                        qty_tmp_sm_dict[str(rec_sm.id)] = qty_tmp_sm_dict[str(rec_sm.id)] + qty_ail
                                    else:
                                        qty_tmp_sm_dict[str(rec_sm.id)] = qty_ail
                                    qty_tmp_ail = qty_tmp_sm_dict[str(rec_sm.id)]
                                    if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                        qty_ail = qty_ail + qty_tmp_ail_dict[str(rec_inv.id)]

                                    rec_pailv.write({'ps_cancelled_quantity': qty_ail + qty_ail_validate,
                                                     'ps_uncancelled_quantity': 0})
                                    rec_psmlv.write({'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate,
                                                     'ps_uncancelled_quantity': rec_sm.product_qty - qty_tmp_ail - qty_sm_validate})
                                    rec_inv.write(
                                        {'ps_cancelled_quantity': qty_ail + qty_ail_validate})  # 更新采购发票上的核销数,为采购发票的未核销数
                                    rec_sm.write(
                                        {
                                            'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate})  # 更新入库单的核销数，为采购发票的未核销数之和
                                    values = {'invoice_line_id': rec_inv.id,
                                              'invoice_line_qty': rec_inv.quantity,
                                              'invoice_line_validate_qty': ail_qty_recs,
                                              'invoice_line_validate_value': ail_qty_recs * rec_inv.price_unit,
                                              'stock_move_id': rec_sm.id,
                                              'stock_move_qty': rec_sm.product_qty,
                                              'stock_move_validate_qty': ail_qty_recs,
                                              'stock_move_validate_value': ail_qty_recs * rec_sm.price_unit,
                                              'operation_date': fields.Date.today(),
                                              'move_id': move_id,
                                              'origin': stock_move_type
                                              }
                                    self.env['ps.invoice.line.stock.move.recs'].create(values)
                                    i = i + 1
                                    qty_sm = qty_sm - ail_qty_recs  # 未核销数量
                                    flag_invoice = True
                                    flag_move = False
                                    break  # 跳出本次循环
                                elif qty_ail == qty_sm:  # 发票未核销数量等于入库单未核销数量

                                    if stock_move_type == 'in':
                                        price_diff = rec_inv.price_unit - rec_sm.price_unit  # 价格差
                                        if abs(price_diff):  # 有价格差，则生成价格差异凭证
                                            move = self._create_validate_move(rec_inv.product_id.id, qty_ail,
                                                                                      price_diff, stock_move_type)
                                            if move:
                                                move_id = move.id
                                    elif stock_move_type == 'out': #出库核销生成凭证
                                        move = self._create_validate_move(rec_inv.product_id.id,
                                                                                  qty_ail, rec_sm.price_unit,
                                                                                  stock_move_type)
                                        if move:
                                            move_id = move.id

                                    if flag_invoice:  # 最后一行取得是发票
                                        if qty_tmp_sm_dict.get(str(rec_sm.id)):
                                            qty_tmp_ail = qty_tmp_sm_dict[str(rec_sm.id)] + qty_sm
                                        else:
                                            qty_tmp_ail = qty_sm
                                        rec_pailv.write({'ps_cancelled_quantity': qty_ail + qty_ail_validate,
                                                         'ps_uncancelled_quantity': 0})
                                        rec_inv.write(
                                            {
                                                'ps_cancelled_quantity': qty_ail + qty_ail_validate})  # 更新采购发票上的核销数,为采购发票的未核销数
                                        rec_psmlv.write({'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate,
                                                         'ps_uncancelled_quantity': rec_sm.product_qty - qty_sm - qty_sm_validate})
                                        rec_sm.write(
                                            {
                                                'ps_cancelled_quantity': qty_tmp_ail + qty_sm_validate})  # 更新入库单的核销数，为采购发票的合计
                                    elif flag_move:  # 最后一行取得是入库单
                                        if qty_tmp_ail_dict.get(str(rec_inv.id)):
                                            qty_tmp_sm = qty_tmp_ail_dict[str(rec_inv.id)] + qty_sm
                                        else:
                                            qty_tmp_sm = qty_sm
                                        rec_pailv.write({'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate,
                                                         'ps_uncancelled_quantity': 0})
                                        rec_inv.write(
                                            {
                                                'ps_cancelled_quantity': qty_tmp_sm + qty_ail_validate})  # 更新采购发票上的核销数,为入库单的合计
                                        rec_psmlv.write({'ps_cancelled_quantity': qty_sm + qty_sm_validate,
                                                         'ps_uncancelled_quantity': rec_sm.product_qty - qty_sm - qty_sm_validate})
                                        rec_sm.write(
                                            {'ps_cancelled_quantity': qty_sm + qty_sm_validate})  # 更新入库单的核销数，为入库单的未核销数
                                    values = {'invoice_line_id': rec_inv.id,
                                              'invoice_line_qty': rec_inv.quantity,
                                              'invoice_line_validate_qty': qty_ail,
                                              'invoice_line_validate_value': qty_ail * rec_inv.price_unit,
                                              'stock_move_id': rec_sm.id,
                                              'stock_move_qty': rec_sm.product_qty,
                                              'stock_move_validate_qty': qty_sm,
                                              'stock_move_validate_value': qty_sm * rec_sm.price_unit,
                                              'operation_date': fields.Date.today(),
                                              'move_id': move_id,
                                              'origin': stock_move_type
                                              }
                                    self.env['ps.invoice.line.stock.move.recs'].create(values)
                                    i = i + 1
                                    j = j + 1
                                    flag_invoice = True
                                    flag_move = True
                                    break  # 跳出本次循环
                            else:
                                flag_move = True
                                j = j + 1
                                if j < L:
                                    continue  # 产品不相等，内循环继续往下走
                                else:
                                    flag_move = True
                                    j = 0
                                    flag_invoice = True
                                    i = i + 1
                                    break
                qty_tmp_ail_dict.clear()
                qty_tmp_sm_dict.clear()
        return {'type': 'ir.actions.act_window_close'}
