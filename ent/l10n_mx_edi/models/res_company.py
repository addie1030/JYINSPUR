# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.l10n_mx_edi.hooks import _load_xsd_files


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_colony = fields.Char(
        compute='_compute_l10n_mx_edi_address',
        inverse='_inverse_l10n_mx_edi_colony')
    l10n_mx_edi_locality = fields.Char(
        compute='_compute_l10n_mx_edi_address',
        inverse='_inverse_l10n_mx_edi_locality')

    l10n_mx_edi_pac = fields.Selection(
        selection=[('finkok', 'Finkok'), ('solfact', 'Solucion Factible')],
        string='PAC',
        help='The PAC that will sign/cancel the invoices',
        default='finkok')
    l10n_mx_edi_pac_test_env = fields.Boolean(
        string='PAC test environment',
        help='Enable the usage of test credentials',
        default=False)
    l10n_mx_edi_pac_username = fields.Char(
        string='PAC username',
        help='The username used to request the seal from the PAC')
    l10n_mx_edi_pac_password = fields.Char(
        string='PAC password',
        help='The password used to request the seal from the PAC')
    l10n_mx_edi_certificate_ids = fields.Many2many('l10n_mx_edi.certificate',
        string='Certificates')

    @api.multi
    def _compute_l10n_mx_edi_address(self):
        for company in self:
            address_data = company.partner_id.sudo().address_get(adr_pref=['contact'])
            if address_data['contact']:
                partner = company.partner_id.browse(address_data['contact'])
                company.l10n_mx_edi_colony = partner.l10n_mx_edi_colony
                company.l10n_mx_edi_locality = partner.l10n_mx_edi_locality

    @api.multi
    def _inverse_l10n_mx_edi_colony(self):
        for company in self:
            company.partner_id.l10n_mx_edi_colony = company.l10n_mx_edi_colony

    @api.multi
    def _inverse_l10n_mx_edi_locality(self):
        for company in self:
            company.partner_id.l10n_mx_edi_locality = company.l10n_mx_edi_locality

    @api.model
    def _load_xsd_attachments(self):
        url = 'http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd'
        xml_ids = self.env['ir.model.data'].search(
            [('name', 'like', 'xsd_cached_%')])
        xsd_files = ['%s.%s' % (x.module, x.name) for x in xml_ids]
        for xsd in xsd_files:
            self.env.ref(xsd).unlink()
        _load_xsd_files(self._cr, None, url)
