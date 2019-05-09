# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    forecast_uom = fields.Selection([
        ('hour', 'Hours'),
        ('day', 'Days'),
    ], string="Time Unit", related='company_id.forecast_uom', required=True, help="Encode your forecasts in hours or days.", readonly=False)
    forecast_span = fields.Selection([
        ('day', 'By day'),
        ('week', 'By week'),
        ('month', 'By month')
    ], string="Time Span", related='company_id.forecast_span', required=True, help="Encode your forecast in a table displayed by days, weeks or the whole year.", readonly=False)

    @api.model
    def create(self, values):
        # Optimisation purpose, saving a res_config even without changing any values will trigger the write of all
        # related values, including the forecast_uom field on res_company. This in turn will trigger the recomputation
        # of account_move_line related field company_currency_id which can be slow depending on the number of entries
        # in the database. Thus, if we do not explicitly change the forecast_uom, we should not write it on the company
        if ('company_id' in values and 'forecast_uom' in values):
            company = self.env['res.company'].browse(values.get('company_id'))
            if company.forecast_uom == values.get('forecast_uom'):
                values.pop('forecast_uom')
        return super(ResConfigSettings, self).create(values)
