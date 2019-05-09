# coding: utf-8

from odoo.tests.common import TransactionCase
from odoo import fields
from odoo.tools import pycompat

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
from suds.client import Client


class AlwaysCallable(object):
    """
    Represents a chainable-access object and proxies calls to ClientMock.
    """
    name = None

    def __init__(self, client_cls):
        self._client_cls = client_cls

    def __call__(self, *args, **kwargs):
        try:
            hook = object.__getattribute__(self._client_cls, self.name)
        except AttributeError:
            pass
        else:
            return hook(self._client_cls, *args, **kwargs)

    def __getattr__(self, item):
        new = object.__getattribute__(self, '__class__')(self._client_cls)
        new.name = item
        return new


class ClientMock(Client):
    """
    Abstract mock suds client.
    """

    def __init__(self, url, **kwargs):
        pass

    def __getattr__(self, item):
        return AlwaysCallable(self.__class__)

    def __unicode__(self):
        return 'Client mock'

    def __str__(self):
        return 'Client mock'


class serviceClientMock(ClientMock):
    """
    Mock object that implements remote side services.
    """

    return_str = """
<CompactData xmlns="http://www.SDMX.org/resources/SDMXML/schemas/v1_0/message"
    xmlns:bm="http://www.banxico.org.mx/structure/key_families/dgie/sie/series/compact"
    xmlns:compact="http://www.SDMX.org/resources/SDMXML/schemas/v1_0/compact"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.SDMX.org/resources/SDMXML/schemas/v1_0/message SDMXMessage.xsd http://www.banxico.org.mx/structure/key_families/dgie/sie/series/compact BANXICO_DGIE_SIE_Compact.xsd http://www.SDMX.org/resources/SDMXML/schemas/v1_0/compact SDMXCompactData.xsd">
  <Header>
    <ID>TIPOSDECAMBIO</ID>
    <Test>false</Test>
    <Truncated>false</Truncated>
    <Name xml:lang="sp">Tipos de Cambio</Name>
    <Prepared>%(date)s 16:37:11.381</Prepared>
    <Sender id="BANXICO">
      <Name xml:lang="sp">Banco de M&#195;&#169;xico</Name>
      <Contact>
        <Name xml:lang="sp">Subgerencia de Desarrollo de Sistemas</Name>
        <Telephone>(01 55)52372678</Telephone>
      </Contact>
    </Sender>
    <DataSetAction>Update</DataSetAction>
    <Extracted>%(date)s 16:37:11.381</Extracted>
  </Header>
  <bm:DataSet>
    <bm:SiblingGroup BANXICO_FREQ="Dia" TIME_FORMAT="P1D"/>
    <bm:Series TITULO="Tipo de cambio pesos por d&#195;&#179;lar E.U.A. Tipo de cambio para solventar obligaciones denominadas en moneda extranjera Fecha de liquidaci&#195;&#179;n" IDSERIE="SF60653" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="PesoxDoll">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="21.7204"/>
    </bm:Series>
    <bm:Series TITULO="Tipo de cambio                                          Pesos por d&#195;&#179;lar E.U.A. Tipo de cambio para solventar obligaciones denominadas en moneda extranjera Fecha de determinaci&#195;&#179;n (FIX)" IDSERIE="SF43718" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="PesoxDoll">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="21.6643"/>
    </bm:Series>
    <bm:Series TITULO="Cotizaci&#195;&#179;n de las divisas que conforman la canasta del DEG Respecto al peso mexicano Euro" IDSERIE="SF46410" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="Peso">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="23.0649"/>
    </bm:Series>
    <bm:Series TITULO="Cotizaci&#195;&#179;n de la divisa Respecto al peso mexicano D&#195;&#179;lar Canadiense" IDSERIE="SF60632" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="Peso">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="%(value_special)s"/>
    </bm:Series>
    <bm:Series TITULO="Cotizaci&#195;&#179;n de las divisas que conforman la canasta del DEG Respecto al peso mexicano Yen japon&#195;&#169;s" IDSERIE="SF46406" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="Peso">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="0.1889"/>
    </bm:Series>
    <bm:Series TITULO="Cotizaci&#195;&#179;n de las divisas que conforman la canasta del DEG Respecto al peso mexicano Libra esterlina" IDSERIE="SF46407" BANXICO_FREQ="Dia" BANXICO_FIGURE_TYPE="TipoCambio" BANXICO_UNIT_TYPE="Peso">
      <bm:Obs TIME_PERIOD="%(date)s" OBS_VALUE="26.3893"/>
    </bm:Series>
  </bm:DataSet>
</CompactData>
"""

    def tiposDeCambioBanxico(cls):
        """
        Stub for remote service.
        """
        return cls.return_str % dict(
            date=fields.Date.today(), value_special=16.4474)


class serviceClientMock2(serviceClientMock):

    def tiposDeCambioBanxico(cls):
        """
        Stub for remote service.
        """
        return cls.return_str % dict(
            date=fields.Date.today(), value_special='N/E')


class BanxicoTest(TransactionCase):
    def setUp(self):
        super(BanxicoTest, self).setUp()
        self.company = self.env.user.company_id
        self.company.currency_provider = 'banxico'
        self.company_2 = self.env.ref('currency_rate_live.res_company_company_2')
        self.company_1 = self.env.ref('currency_rate_live.res_company_company_1')
        self.user_root = self.env.ref('base.user_root')
        self.mxn = self.env.ref('base.MXN')
        self.usd = self.env.ref('base.USD')
        self.eur = self.env.ref('base.EUR')
        self.cad = self.env.ref('base.CAD')
        self.jpy = self.env.ref('base.JPY')
        self.gbp = self.env.ref('base.GBP')
        self.foreign_currencies = [
            self.usd, self.eur, self.cad, self.jpy, self.gbp]
        self.foreign_expected_rates = [
            21.7204, 23.0649, 16.4474, 0.1889, 26.3893]
        self.mxn.active = True
        for currency in self.foreign_currencies:
            currency.active = True

    def set_rate(self, currency, rate):
        currency.rate_ids.unlink()
        currency.rate_ids = self.env['res.currency.rate'].create({
            'rate': rate,
            'currency_id': currency.id,
            'name': fields.Datetime.now().replace(hour=0, minute=0, second=0),
            'company_id': self.company.id,
        })

    def test_banxico_currency_update_nomxn(self):
        self.company.currency_id = self.eur
        self.test_banxico_currency_update()

    def test_banxico_currency_update(self):
        self.company.currency_id = self.mxn
        # Using self.usd.rate=1 and self.mxn.rate != 1
        self.set_rate(self.usd, 1.0)
        self.assertEqual(self.usd.rate, 1.0)
        self.set_rate(self.mxn, 10.0)
        self.assertEqual(self.mxn.rate, 10.0)
        with patch('suds.client.Client', new=serviceClientMock):
            self.company.update_currency_rates()
        self.assertNotEqual(self.usd.rate, 1.0)
        self.assertNotEqual(self.mxn.rate, 10.0)
        foreigns1 = [foreign_currency._convert(1.0, self.mxn, company=self.company, date=fields.Date.today())
                     for foreign_currency in self.foreign_currencies]

        # Using self.mxn.rate=1 and self.usd.rate != 1
        self.set_rate(self.mxn, 1.0)
        self.assertEqual(self.mxn.rate, 1.0)
        self.set_rate(self.usd, 0.1)
        self.assertEqual(self.usd.compare_amounts(self.usd.rate, 0.1), 0)
        with patch('suds.client.Client', new=serviceClientMock):
            self.company.update_currency_rates()
        self.assertEqual(self.mxn.rate, 1.0)
        self.assertNotEqual(self.usd.rate, 1.0 / 10.0)
        foreigns2 = [foreign_currency._convert(1.0, self.mxn, company=self.company, date=fields.Date.today())
                     for foreign_currency in self.foreign_currencies]
        for curr, foreign1, foreign2 in pycompat.izip(self.foreign_currencies, foreigns1, foreigns2):
            self.assertEqual(curr.compare_amounts(foreign1, foreign2), 0,
                             "%s diff rate %s != %s" % (curr.name, foreign1, foreign2))
        # Compare expected xml mocked rate values vs real ones
        for curr, real_rate, expected_rate in pycompat.izip(self.foreign_currencies, foreigns1, self.foreign_expected_rates):
            self.assertEqual(curr.compare_amounts(real_rate, expected_rate), 0,
                             "%s diff rate %s != %s" % (curr.name, real_rate, expected_rate))

    def test_banxico_without_rate(self):
        """In some cases Banxico return N/E to the rates, in that cases is not
        changed the rate. In that cases, rate is not added"""
        self.set_rate(self.mxn, 1)
        self.assertEqual(self.mxn.rate, 1)
        self.cad.rate_ids.unlink()
        with patch('suds.client.Client', new=serviceClientMock2):
            self.company.update_currency_rates()
        self.assertFalse(self.cad.rate_ids)

    def test_banxico_multicompany(self):
        companies = self.env['res.company']
        companies |= self.company_2
        companies |= self.company_1

        # Let us switch to  company_2
        self.user_root.write({'company_id': self.company_2.id})

        # Checking company_2 & company_1 has USD as Currency
        self.assertEqual(self.company_2.currency_id.id, self.mxn.id)
        self.assertEqual(self.company_1.currency_id.id, self.mxn.id)

        # Checking company_2 & company_1 has banxico as Currency Provider
        self.assertEqual(self.company_2.currency_provider, 'banxico')
        self.assertEqual(self.company_1.currency_provider, 'banxico')

        # Checking company_2 & company_1 have no rates for USD currency
        self.assertFalse(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_2.id))
        self.assertFalse(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_1.id))

        # Let us fetch the newest USD rates for company_2 & company_1
        with patch('suds.client.Client', new=serviceClientMock):
            companies.update_currency_rates()
        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_2.id)), 1)
        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_1.id)), 1)

        # Let us switch from company_1 to company_2, delete the rates for USD
        # and set company_1's provider to None
        self.user_root.write({'company_id': self.company_2.id})
        self.usd.rate_ids.filtered(lambda r: r.name == fields.Date.today()).unlink()
        self.company_1.write({'currency_provider': False})

        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_2.id)), 0)
        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_1.id)), 0)

        # Update the currency rates, as banxico is only set in company_2 then
        # company_1 is left without currency rates
        with patch('suds.client.Client', new=serviceClientMock):
            companies.update_currency_rates()

        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_2.id)), 1)
        self.assertEqual(len(self.usd.rate_ids.filtered(lambda r: r.company_id.id == self.company_1.id)), 0)
