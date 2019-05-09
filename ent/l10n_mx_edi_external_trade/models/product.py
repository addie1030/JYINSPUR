# coding: utf-8

from odoo import api, fields, models
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_mx_edi_tariff_fraction_id = fields.Many2one(
        'l10n_mx_edi.tariff.fraction', string='Tariff Fraction',
        help='It is used to express the key of the tariff fraction '
        'corresponding to the description of the product to export.')
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        'uom.uom', 'UMT Aduana', help='Used in complement '
        '"Comercio Exterior" to indicate in the products the '
        'TIGIE Units of Measurement. It is based in the SAT catalog.')


class UoM(models.Model):
    _inherit = 'uom.uom'

    l10n_mx_edi_code_aduana = fields.Char(
        'Customs code', help='Used in the complement of "Comercio Exterior" to'
        ' indicate in the products the UoM. It is based in the SAT catalog.')


class L10nMXEdiTariffFraction(models.Model):
    _name = 'l10n_mx_edi.tariff.fraction'
    _description = "Mexican EDI Tariff Fraction"

    code = fields.Char(help='Code defined in the SAT to this record.')
    name = fields.Char(help='Name defined in the SAT catalog to this record.')
    uom_code = fields.Char(
        help='UoM code related with this tariff fraction. This value is '
        'defined in the SAT catalog and will be assigned in the attribute '
        '"UnidadAduana" in the merchandise.')
    active = fields.Boolean(
        help='If the tariff fraction has expired it could be disabled to '
        'do not allow select the record.', default=True)

    @api.multi
    def name_get(self):
        result = []
        for tariff in self:
            result.append((tariff.id, "%s %s" % (
                tariff.code, tariff.name or '')))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', 'ilike', name), ('code', 'ilike', name)]
        ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(ids).name_get()
