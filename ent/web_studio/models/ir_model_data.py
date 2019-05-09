# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class IrModelData(models.Model):
    _inherit = 'ir.model.data'

    studio = fields.Boolean(help='Checked if it has been edited with Studio.')

    @api.model
    def create(self, vals):
        if self._context.get('studio'):
            vals['studio'] = True
        return super(IrModelData, self).create(vals)

    @api.multi
    def write(self, vals):
        """ When editing an ir.model.data with Studio, we put it in noupdate to
                avoid the customizations to be dropped when upgrading the module.
        """
        if self._context.get('studio'):
            vals['noupdate'] = True
            vals['studio'] = True
        return super(IrModelData, self).write(vals)
