# -*- coding: utf-8 -*-

from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # TODO - Remove in master
    l10n_mx_edi_incoterm = fields.Selection(
        [('CIP', 'CARRIAGE AND INSURANCE PAID TO'),
         ('CPT', 'CARRIAGE PAID TO'),
         ('CFR', 'COST AND FREIGHT'),
         ('CIF', 'COST, INSURANCE AND FREIGHT'),
         ('DAF', 'DELIVERED AT FRONTIER'),
         ('DAP', 'DELIVERED AT PLACE'),
         ('DAT', 'DELIVERED AT TERMINAL'),
         ('DDP', 'DELIVERED DUTY PAID'),
         ('DDU', 'DELIVERED DUTY UNPAID'),
         ('DEQ', 'DELIVERED EX QUAY'),
         ('DES', 'DELIVERED EX SHIP'),
         ('EXW', 'EX WORKS'),
         ('FAS', 'FREE ALONGSIDE SHIP'),
         ('FCA', 'FREE CARRIER'),
         ('FOB', 'FREE ON BOARD')],
        help='Indicates the applicable INCOTERM to the '
        'external trade customer invoice.')
    l10n_mx_edi_cer_source = fields.Char(
        'Certificate Source',
        help='Used in CFDI like attribute derived from the exception of '
        'certificates of Origin of the Free Trade Agreements that Mexico '
        'has celebrated with several countries. If it has a value, it will '
        'indicate that it serves as certificate of origin and this value will '
        'be set in the CFDI node "NumCertificadoOrigen".')
    l10n_mx_edi_external_trade = fields.Boolean(
        'Need external trade?', compute='_compute_need_external_trade',
        inverse='_inverse_need_external_trade', store=True,
        help='If this field is active, the CFDI that generates this invoice '
        'will include the complement "External Trade".')

    @api.depends('partner_id')
    def _compute_need_external_trade(self):
        """Assign the "Need external trade?" value how in the partner"""
        for record in self.filtered(lambda i: i.type == 'out_invoice'):
            record.l10n_mx_edi_external_trade = record.partner_id.l10n_mx_edi_external_trade

    def _inverse_need_external_trade(self):
        return True

    @api.multi
    def _l10n_mx_edi_create_cfdi(self):
        if not self.l10n_mx_edi_external_trade:
            return super(AccountInvoice, self)._l10n_mx_edi_create_cfdi()

        # Call the onchange to obtain the values of l10n_mx_edi_qty_umt
        # and l10n_mx_edi_price_unit_umt, this is necessary when the
        # invoice is created from the sales order or from the picking
        self.invoice_line_ids.onchange_quantity()
        self.invoice_line_ids._set_price_unit_umt()
        return super(AccountInvoice, self)._l10n_mx_edi_create_cfdi()

    @api.multi
    def _l10n_mx_edi_create_cfdi_values(self):
        """Create the values to fill the CFDI template with external trade.
        """
        values = super(AccountInvoice, self)._l10n_mx_edi_create_cfdi_values()
        if not self.l10n_mx_edi_external_trade:
            return values

        ctx = dict(company_id=self.company_id.id, date=self.date_invoice)
        customer = values['customer']
        values.update({
            'usd': self.env.ref('base.USD').with_context(ctx),
            'mxn': self.env.ref('base.MXN').with_context(ctx),
            'europe_group': self.env.ref('base.europe'),
            'receiver_reg_trib': customer.vat,
        })
        values['quantity_aduana'] = lambda p, i: sum([
            l.l10n_mx_edi_qty_umt for l in i.invoice_line_ids
            if l.product_id == p])
        values['unit_value_usd'] = lambda l, c, u: c.compute(
            l.l10n_mx_edi_price_unit_umt, u)
        values['amount_usd'] = lambda origin, dest, amount: origin.compute(
            amount, dest, round=False)
        # http://omawww.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/Complementoscfdi/GuiaComercioExterior3_3.pdf
        # ValorDolares : it depends of the currency  (p. 62-63):
        #   - if currency is MXN: ValorDolares = Importe (subtotal without discounts) / TipoCambioUSD
        #   - if currency is USD: ValorDolares = Importe
        #   - if currency is anoter: ValorDolares = Importe x TipoCambio / TipoCambioUSD
        # There is a common mistake to mutiply the Qty UMT with the unit price UMT. (p. 76)
        #
        # TotalUSD : must be the sum of all the Valor Dolares fields (p. 48)
        values['valor_usd'] = lambda l, u, c : c.compute(
            l.price_subtotal / (1 - l.discount/100) if l.discount != 100 else
            l.price_unit * l.quantity, u)
        values['total_usd'] = lambda i, u, c: sum([values['valor_usd'](l, u, c)
            for l in i])

        return values

    @api.model
    def l10n_mx_edi_get_et_etree(self, cfdi):
        """Get the ComercioExterior node from the cfdi.
        :param cfdi: The cfdi as etree
        :return: the ComercioExterior node
        """
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'cce11:ComercioExterior[1]'
        namespace = {'cce11': 'http://www.sat.gob.mx/ComercioExterior11'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    l10n_mx_edi_tariff_fraction_id = fields.Many2one(
        'l10n_mx_edi.tariff.fraction', 'Tariff Fraction', store=True,
        related='product_id.l10n_mx_edi_tariff_fraction_id', readonly=True,
        help='It is used to express the key of the tariff fraction '
        'corresponding to the description of the product to export.')
    l10n_mx_edi_umt_aduana_id = fields.Many2one(
        'uom.uom', 'UMT Aduana', store=True,
        related='product_id.l10n_mx_edi_umt_aduana_id', readonly=True,
        help='Used in complement "Comercio Exterior" to indicate in the '
        'products the TIGIE Units of Measurement. It is based in the SAT '
        'catalog.')
    l10n_mx_edi_qty_umt = fields.Float(
        'Qty UMT', help='Quantity expressed in the UMT from product. It is '
        'used in the attribute "CantidadAduana" in the CFDI',
        digits=dp.get_precision('Product Unit of Measure'))
    l10n_mx_edi_price_unit_umt = fields.Float(
        'Unit Value UMT', help='Unit value expressed in the UMT from product. '
        'It is used in the attribute "ValorUnitarioAduana" in the CFDI')

    @api.multi
    def _set_price_unit_umt(self):
        for res in self:
            res.l10n_mx_edi_price_unit_umt = round(
                res.quantity * res.price_unit / res.l10n_mx_edi_qty_umt
                if res.l10n_mx_edi_qty_umt else
                res.l10n_mx_edi_price_unit_umt, 2)

    @api.onchange('quantity', 'product_id', 'l10n_mx_edi_umt_aduana_id')
    @api.multi
    def onchange_quantity(self):
        """When change the quantity by line, update the QTY in the UMT"""
        for res in self.filtered(
                lambda l: l.invoice_id.l10n_mx_edi_external_trade and
                l.product_id):
            pdt_aduana = res.l10n_mx_edi_umt_aduana_id.l10n_mx_edi_code_aduana
            if pdt_aduana == res.uom_id.l10n_mx_edi_code_aduana:
                res.l10n_mx_edi_qty_umt = res.quantity
            elif pdt_aduana and '01' in pdt_aduana:
                res.l10n_mx_edi_qty_umt = round(
                    res.product_id.weight * res.quantity, 3)
