# -*- coding: utf-8 -*-

from odoo import models


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_bom_reference(self, bom):
        """ Get bom reference """
        code = super(ReportBomStructure, self)._get_bom_reference(bom)
        if bom.version:
            code += ' - Version' + str(bom.version)
        return code
