# -*- coding: utf-8 -*-

import json

from odoo import api, models, _
from odoo.tools import float_round


class ReportBomStructure(models.AbstractModel):
    _name = 'report.report_ps_quality_sampling_code'
    _description = 'Sampling Code Report'

    def _get_quality_sampling_code(self, code_id):
        quality_sampling_id = self.env['ps.quality.sampling.name'].browse(code_id)
        level_category = self.env['ps.quality.sampling.code'].read_group(
            [('sampling_id', '=', quality_sampling_id.id)], ['inspection_level_category'],
            ['inspection_level_category'])
        # search  level category group by category
        level_category = [x['inspection_level_category'] for x in level_category]
        code_list = []

        # search all sampling code data
        codes = self.env['ps.quality.sampling.code'].search([('sampling_id', '=', quality_sampling_id.id)], order='id')

        scope = []
        for s in codes.mapped('size_scope'):
            # list all level size scope
            if s not in scope:
                scope.append(s)
        level = []
        for s in codes.mapped('inspection_level'):
            # list all level
            if s.code not in level:
                level.append(s.code)

        for x in scope:
            # list all level code
            code = self.env['ps.quality.sampling.code'].search(
                [('sampling_id', '=', quality_sampling_id.id), ('size_scope', '=', x)], order='id').mapped('code')
            code_list.append(code)

        scope_codes = []
        for i, code in enumerate(code_list):
            code.insert(0, scope[i])
            scope_codes.append(code)
        values = {'type': level_category, 'level': level, 'scope_codes': scope_codes}

        res = {
            'doc_ids': code_id,
            'doc_model': 'ps.quality.sampling.name',
            'name': quality_sampling_id.name,  # sampling name
            'type': level_category,  # sampling name
            'level': level,
            'scope_codes': scope_codes,
            'data': values,
            'lines': {}
        }
        return res

    @api.model
    def get_html(self, code_id):

        res = self._get_quality_sampling_code(code_id)

        res['lines']['report_type'] = 'html'
        res['lines']['report_structure'] = 'all'

        res['lines'] = self.env.ref('ps_quality_management.report_quality_sampling_code').render({'data': {
            'name': res['name'],
            'type': res['type'],
            'level': res['level'],
            'scope_codes': res['scope_codes'],
        }})
        return res
