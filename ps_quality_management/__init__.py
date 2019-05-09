# -*- coding: utf-8 -*-
from . import models
from . import report

import logging
from odoo import api, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


def check_quality_location(obj, location_name, location_id):
    instance = obj.search([('name', '=', location_name), ('location_id', '=', False)])
    if not instance:
        return obj.create({
            'name': location_name,
            'active': False,
            'usage': 'internal',
            'location_id': location_id.id,
        }).id
    return None


def _init_qc_sequence_values(warehouse):
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


def _create_quality_picking_type(cr, warehouse, IrSequenceSudo, StockPickingType):
    vals = {}
    for field_picking_type, sequence_data in _init_qc_sequence_values(warehouse).items():
        sequence_id = IrSequenceSudo.create(sequence_data)
        name = ''
        if ' '.join(str(sequence_id.name).split()[-2:]) == 'Bad Return':
            name = 'Bad Return'
        if ' '.join(str(sequence_id.name).split()[-2:]) == 'Inventory Check':
            name = 'Inventory Check'
        picking_type_id = StockPickingType.create({
            'name': name,
            'code': 'internal',
            'warehouse_id': warehouse.id,
            'sequence_id': sequence_id.id,
        })
        vals[field_picking_type] = picking_type_id.id
        _translate_update(cr, picking_type_id, name)

    warehouse.write(vals)


def _translate_update(cr, res_id, name):
    env = api.Environment(cr, SUPERUSER_ID, {})
    value = False
    if name == 'Bad Return':
        value = '不良退货'
    if name == 'Inventory Check':
        value = "库存复检"
    values = {
        'name': 'stock.picking.type,name',
        'res_id': res_id.id,
        'lang': 'zh_CN',
        'type': 'model',
        'src': name,
        'value': value,
    }
    env['ir.translation'].sudo().create(values)


def post_init_hook(cr, registry):
    """更新之前stock.warehouse的复检库位 待处理库位"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    warehouses = env['stock.warehouse']
    stock_location = env['stock.location']
    IrSequenceSudo = env['ir.sequence'].sudo()
    StockPickingType = env['stock.picking.type'].sudo()
    for warehouse in warehouses.search([('ps_inspect_wh_id', '=', False)]):
        ps_inspect_wh_id = check_quality_location(stock_location, 'Inventory Qualitycheck',
                                                  warehouse.view_location_id)
        ps_pending_wh_id = check_quality_location(stock_location, 'Inventory Disposal', warehouse.view_location_id)
        if ps_pending_wh_id and ps_inspect_wh_id:
            warehouse.write({
                'ps_pending_wh_id': ps_pending_wh_id,
                'ps_inspect_wh_id': ps_inspect_wh_id,
            })
    for warehouse in warehouses.search([('inventory_check_type_id', '=', False)]):
        _create_quality_picking_type(cr, warehouse, IrSequenceSudo, StockPickingType)
    env['stock.quant'].search([]).write({'ps_is_request': False, 'ps_is_date_company': False})


def uninstall_hook(cr, registry):
    cr.execute("delete from stock_picking_type where name='Bad Return'")
    cr.execute("delete from stock_picking_type where name='Inventory Check'")


from odoo.addons.quality_control.models.stock_move import StockMove

"""采用猴子补丁，取消原有的代码逻辑"""


#
def _create_quality_checks(self):
    pass


StockMove._create_quality_checks = _create_quality_checks
