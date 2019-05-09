# -*- coding: utf-8 -*-

from odoo import fields, models, api
from ..hooks import _load_xsd_complement


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_num_exporter = fields.Char(
        'Number of Reliable Exporter',
        help='Indicates the number of reliable exporter in accordance '
        'with Article 22 of Annex 1 of the Free Trade Agreement with the '
        'European Association and the Decision of the European Community. '
        'Used in External Trade in the attribute "NumeroExportadorConfiable".')
    l10n_mx_edi_locality_id = fields.Many2one(
        'l10n_mx_edi.res.locality', string='Locality',
        related='partner_id.l10n_mx_edi_locality_id', readonly=False,
        help='Municipality configured for this company')
    l10n_mx_edi_colony_code = fields.Char(
        string='Colony Code',
        compute='_compute_l10n_mx_edi_colony_code',
        inverse='_inverse_l10n_mx_edi_colony_code',
        help='Colony Code configured for this company. It is used in the '
        'external trade complement to define the colony where the domicile '
        'is located.')

    @api.multi
    def _compute_l10n_mx_edi_colony_code(self):
        for company in self:
            address_data = company.partner_id.sudo().address_get(
                adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact'])
                company.l10n_mx_edi_colony_code = (
                    partner.l10n_mx_edi_colony_code)

    @api.multi
    def _inverse_l10n_mx_edi_colony_code(self):
        for company in self:
            company.partner_id.l10n_mx_edi_colony_code = (
                company.l10n_mx_edi_colony_code)

    @api.model
    def _load_xsd_attachments(self):
        res = super(ResCompany, self)._load_xsd_attachments()
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/ComercioExterior11/ComercioExterior11.xsd' # noqa
        xsd = self.env.ref(
            'l10n_mx_edi.xsd_cached_ComercioExterior11_xsd', False)
        if xsd:
            xsd.unlink()
        _load_xsd_complement(self._cr, None, url)
        return res
