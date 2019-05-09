# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PsStockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    ps_inspect_wh_id = fields.Many2one('stock.location',
                                       string='Recheck Inventory',
                                       )
    ps_pending_wh_id = fields.Many2one('stock.location',
                                       string='Disposal Inventory',
                                       )
    inventory_check_type_id = fields.Many2one('stock.picking.type', string='Inventory Check')

    bad_return_type_id = fields.Many2one('stock.picking.type', string='Bad Return')

    @api.model
    def create(self, vals):
        warehouse = super(PsStockWarehouse, self).create(vals)
        for field_name, values in self._get_quality_locations_values(warehouse.view_location_id).items():
            vals[field_name] = self.env['stock.location'].create(values).id

        # sequence_data = self._get_qc_sequence_values(warehouse)
        IrSequenceSudo = self.env['ir.sequence'].sudo()
        StockPickingType = self.env['stock.picking.type'].sudo()
        for field_picking_type, sequence_data in self._get_qc_sequence_values(warehouse).items():
            sequence_id = IrSequenceSudo.create(sequence_data)
            picking_type_id = StockPickingType.create({
                'name': _(' '.join(str(sequence_id.name).split()[-2:])),
                'code': 'internal',
                'warehouse_id': warehouse.id,
                'sequence_id': sequence_id.id,
            })
            vals[field_picking_type] = picking_type_id.id
        warehouse.write(vals)
        return warehouse

    def _get_quality_locations_values(self, location_id):
        """ Update the warehouse locations. """
        return {

            'ps_inspect_wh_id': {'name': _('Inventory Qualitycheck'), 'active': True,
                                 'usage': 'internal', 'location_id': location_id.id, },
            'ps_pending_wh_id': {'name': _('Inventory Disposal'), 'active': True, }}

    def _get_qc_sequence_values(self, warehouse):
        return {
            'inventory_check_type_id': {
                'name': warehouse.name + ' ' + _('Sequence Inventory Check'),
                'prefix': warehouse.code + '/QC/',
                'padding': 5,
                'company_id': warehouse.company_id.id,
            },
            'bad_return_type_id': {
                'name': warehouse.name + ' ' + _('Sequence Bad Return'),
                'prefix': warehouse.code + '/BR/',
                'padding': 5,
                'company_id': warehouse.company_id.id,
            }
        }
