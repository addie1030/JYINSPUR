# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import tools


class PsStockAccountChinaCenterCancelMove(models.Model):
    _name = 'ps.stock.account.china.center.cancel.move'
    _auto = False

    reference = fields.Char(compute='_compute_reference', string=_("Reference"), store=True)
    picking_type_id = fields.Many2one('stock.picking.type', string=_('Operation Type'),
                                      required=True,
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    partner_id = fields.Many2one('res.partner', string=_('Partner'),
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    origin = fields.Char(string=_('Source Document'), index=True,
                         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                         help="Reference of the document")
    date = fields.Datetime(string=_('Creation Date'),
                           default=fields.Datetime.now, index=True, track_visibility='onchange',
                           states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                           help="Creation Date, usually the time of the order")
    account_move_id = fields.Integer(string=_('Certificate ID'))

    state = fields.Selection([
        ('draft', _('Draft')),
        ('waiting', _('Waiting Another Operation')),
        ('confirmed', _('Waiting')),
        ('assigned', _('Ready')),
        ('done', _('Done')),
        ('cancel', _('Cancelled')),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=_(" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore."))

    @api.model_cr
    def init(self):
        self._table = 'ps_stock_account_china_center_cancel_move'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        create or replace view ps_stock_account_china_center_cancel_move as (
            select 
            t2.reference as reference,
            t1.picking_type_id as picking_type_id,
            t1.partner_id as partner_id,
            t1.origin as origin,
            t1.date as date,
            t1.state as state,
            t2.id as id,
            t2.account_move_id as account_move_id
            from stock_picking t1, stock_move t2
            where t1.id = t2.picking_id and t2.account_move_id <> 0
        )
        """)
