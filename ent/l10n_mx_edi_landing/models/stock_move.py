# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMove(models.Model):

    _inherit = 'stock.move'

    move_orig_fifo_ids = fields.Many2many(
        'stock.move', 'stock_move_move_fifo_rel', 'move_dest_id',
        'move_orig_id', 'Original Fifo Move',
        help="Optional: previous stock move when chaining them")

    @api.model
    def _run_fifo(self, move, quantity=None):
        candidates = move.product_id._get_fifo_candidates_in_move()
        candidate_to_take = {}
        for move_candidate in candidates:
            candidate_to_take[move_candidate.id] = move_candidate.remaining_qty
        res = super(StockMove, self)._run_fifo(move, quantity=quantity)
        for candidate_taked in candidates:
            if (candidate_taked.remaining_qty !=
                    candidate_to_take[candidate_taked.id]):
                move.write({
                    'move_orig_fifo_ids': [(4, candidate_taked.id, 0)]})
        return res
