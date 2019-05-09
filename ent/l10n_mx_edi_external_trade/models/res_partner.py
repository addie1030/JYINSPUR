# coding: utf-8

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_mx_edi_external_trade = fields.Boolean(
        'Need external trade?', help='check this box to add by default '
        'the external trade complement in invoices for this customer.')
    l10n_mx_edi_colony_code = fields.Char(
        string='Colony Code',
        help='Note: Only use this field if this partner is the company '
        'address or if it is a branch office.\nColony code that will be '
        'used in the CFDI with the external trade as Emitter colony. It must '
        'be a code from the SAT catalog.')
    l10n_mx_edi_locality_id = fields.Many2one(
        'l10n_mx_edi.res.locality', string='Locality',
        help='Optional attribute used in the XML that serves to define the '
        'locality where the domicile is located.')
    l10n_mx_edi_curp = fields.Char(
        'CURP', size=18, help='Attribute to set in XML to express the CURP '
        'when the partner is from a natural person.')

    @api.onchange('l10n_mx_edi_locality_id')
    def _onchange_l10n_mx_edi_locality_id(self):
        self.l10n_mx_edi_locality = self.l10n_mx_edi_locality_id.name
