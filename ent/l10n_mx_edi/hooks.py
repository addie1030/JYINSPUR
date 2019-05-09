# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
from contextlib import closing
from os.path import join, dirname, realpath
from lxml import etree, objectify

from werkzeug import url_quote

from odoo import api, tools, SUPERUSER_ID
import requests

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _load_product_sat_catalog(cr, registry)
    _assign_codes_uom(cr, registry)
    url = 'http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv33.xsd'
    _load_xsd_files(cr, registry, url)


def _load_product_sat_catalog(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    csv_path = join(dirname(realpath(__file__)), 'data',
                    'l10n_mx_edi.product.sat.code.csv')
    csv_file = open(csv_path, 'rb')
    cr.copy_expert(
        """COPY l10n_mx_edi_product_sat_code(code, name, applies_to, active)
           FROM STDIN WITH DELIMITER '|'""", csv_file)
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model)
           SELECT concat('prod_code_sat_', code), id, 'l10n_mx_edi', 'l10n_mx_edi.product.sat.code'
           FROM l10n_mx_edi_product_sat_code """)


def _assign_codes_uom(cr, registry):
    """Assign the codes in UoM of each data, this is here because the data is
    created in the last method"""
    tools.convert.convert_file(
        cr, 'l10n_mx_edi', 'data/product_data.xml', None, mode='init',
        kind='data')


def _load_xsd_files(cr, registry, url):
    fname = url.split('/')[-1]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logging.getLogger(__name__).info(
            'I cannot connect with the given URL.')
        return ''
    try:
        res = objectify.fromstring(response.content)
    except etree.XMLSyntaxError as e:
        logging.getLogger(__name__).info(
            'You are trying to load an invalid xsd file.\n%s', e)
        return ''
    namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    if fname == 'cfdv33.xsd':
        # This is the xsd root
        res = _load_xsd_complements(cr, registry, res)
    sub_urls = res.xpath('//xs:import', namespaces=namespace)
    for s_url in sub_urls:
        s_url_catch = _load_xsd_files(cr, registry, s_url.get('schemaLocation'))
        s_url.attrib['schemaLocation'] = url_quote(s_url_catch)
    try:
        xsd_string = etree.tostring(res, pretty_print=True)
    except etree.XMLSyntaxError:
        logging.getLogger(__name__).info('XSD file downloaded is not valid')
        return ''
    env = api.Environment(cr, SUPERUSER_ID, {})
    xsd_fname = 'xsd_cached_%s' % fname.replace('.', '_')
    attachment = env.ref('l10n_mx_edi.%s' % xsd_fname, False)
    filestore = tools.config.filestore(cr.dbname)
    if attachment:
        return join(filestore, attachment.store_fname)
    attachment = env['ir.attachment'].create({
        'name': xsd_fname,
        'datas_fname': fname,
        'datas': base64.encodestring(xsd_string),
    })
    # Forcing the triggering of the store_fname
    attachment._inverse_datas()
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model)
           VALUES (%s, %s, 'l10n_mx_edi', 'ir.attachment')""", (
               xsd_fname, attachment.id))
    return join(filestore, attachment.store_fname)


def _load_xsd_complements(cr, registry, content):
    complements = [
        ['http://www.sat.gob.mx/servicioparcialconstruccion',
         'http://www.sat.gob.mx/sitio_internet/cfd/servicioparcialconstruccion/servicioparcialconstruccion.xsd'],
        ['http://www.sat.gob.mx/EstadoDeCuentaCombustible',
         'http://www.sat.gob.mx/sitio_internet/cfd/EstadoDeCuentaCombustible/ecc11.xsd'],
        ['http://www.sat.gob.mx/donat',
         'http://www.sat.gob.mx/sitio_internet/cfd/donat/donat.xsd'],
        ['http://www.sat.gob.mx/divisas',
         'http://www.sat.gob.mx/sitio_internet/cfd/divisas/Divisas.xsd'],
        ['http://www.sat.gob.mx/implocal',
         'http://www.sat.gob.mx/sitio_internet/cfd/implocal/implocal.xsd'],
        ['http://www.sat.gob.mx/leyendasFiscales',
         'http://www.sat.gob.mx/sitio_internet/cfd/leyendasFiscales/leyendasFisc.xsd'],
        ['http://www.sat.gob.mx/pfic',
         'http://www.sat.gob.mx/sitio_internet/cfd/pfic/pfic.xsd'],
        ['http://www.sat.gob.mx/TuristaPasajeroExtranjero',
         'http://www.sat.gob.mx/sitio_internet/cfd/TuristaPasajeroExtranjero/TuristaPasajeroExtranjero.xsd'],
        ['http://www.sat.gob.mx/detallista',
         'http://www.sat.gob.mx/sitio_internet/cfd/detallista/detallista.xsd'],
        ['http://www.sat.gob.mx/registrofiscal',
         'http://www.sat.gob.mx/sitio_internet/cfd/cfdiregistrofiscal/cfdiregistrofiscal.xsd'],
        ['http://www.sat.gob.mx/nomina12',
         'http://www.sat.gob.mx/sitio_internet/cfd/nomina/nomina12.xsd'],
        ['http://www.sat.gob.mx/pagoenespecie',
         'http://www.sat.gob.mx/sitio_internet/cfd/pagoenespecie/pagoenespecie.xsd'],
        ['http://www.sat.gob.mx/valesdedespensa',
         'http://www.sat.gob.mx/sitio_internet/cfd/valesdedespensa/valesdedespensa.xsd'],
        ['http://www.sat.gob.mx/consumodecombustibles',
         'http://www.sat.gob.mx/sitio_internet/cfd/consumodecombustibles/consumodecombustibles.xsd'],
        ['http://www.sat.gob.mx/aerolineas',
         'http://www.sat.gob.mx/sitio_internet/cfd/aerolineas/aerolineas.xsd'],
        ['http://www.sat.gob.mx/notariospublicos',
         'http://www.sat.gob.mx/sitio_internet/cfd/notariospublicos/notariospublicos.xsd'],
        ['http://www.sat.gob.mx/vehiculousado',
         'http://www.sat.gob.mx/sitio_internet/cfd/vehiculousado/vehiculousado.xsd'],
        ['http://www.sat.gob.mx/renovacionysustitucionvehiculos',
         'http://www.sat.gob.mx/sitio_internet/cfd/renovacionysustitucionvehiculos/renovacionysustitucionvehiculos.xsd'],
        ['http://www.sat.gob.mx/certificadodestruccion',
         'http://www.sat.gob.mx/sitio_internet/cfd/certificadodestruccion/certificadodedestruccion.xsd'],
        ['http://www.sat.gob.mx/arteantiguedades',
         'http://www.sat.gob.mx/sitio_internet/cfd/arteantiguedades/obrasarteantiguedades.xsd'],
        ['http://www.sat.gob.mx/ComercioExterior11',
         'http://www.sat.gob.mx/sitio_internet/cfd/ComercioExterior11/ComercioExterior11.xsd'],
        ['http://www.sat.gob.mx/Pagos',
         'http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos10.xsd'],
        ['http://www.sat.gob.mx/iedu',
         'http://www.sat.gob.mx/sitio_internet/cfd/iedu/iedu.xsd'],
        ['http://www.sat.gob.mx/ventavehiculos',
         'http://www.sat.gob.mx/sitio_internet/cfd/ventavehiculos/ventavehiculos11.xsd'],
        ['http://www.sat.gob.mx/terceros',
         'http://www.sat.gob.mx/sitio_internet/cfd/terceros/terceros11.xsd'],
        ['http://www.sat.gob.mx/spei',
         'http://www.sat.gob.mx/sitio_internet/cfd/spei/spei.xsd'],
        ['http://www.sat.gob.mx/ine',
         'http://www.sat.gob.mx/sitio_internet/cfd/ine/INE11.xsd'],
        ['http://www.sat.gob.mx/acreditamiento',
         'http://www.sat.gob.mx/sitio_internet/cfd/acreditamiento/AcreditamientoIEPS10.xsd'],
    ]
    for complement in complements:
        xsd = {'namespace': complement[0], 'schemaLocation': complement[1]}
        node = etree.Element('{http://www.w3.org/2001/XMLSchema}import', xsd)
        content.insert(0, node)
    return content
