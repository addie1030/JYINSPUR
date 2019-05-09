# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
from os.path import join, dirname, realpath
from lxml import etree, objectify

from werkzeug import url_quote

from odoo import api, tools, SUPERUSER_ID
# TODO: Add after merge https://github.com/odoo/enterprise/pull/1617
# from odoo.addons.l10n_mx_edi.hooks import _load_xsd_files
import requests

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    url = 'http://www.sat.gob.mx/sitio_internet/cfd/ComercioExterior11/ComercioExterior11.xsd'
    _load_xsd_complement(cr, registry, url)
    _load_locality_sat_catalog(cr, registry)
    _load_tariff_fraction_catalog(cr, registry)


def _load_xsd_complement(cr, registry, url):
    db_fname = _load_xsd_files(cr, registry, url)
    env = api.Environment(cr, SUPERUSER_ID, {})
    xsd = env.ref('l10n_mx_edi.xsd_cached_cfdv33_xsd', False)
    if not xsd:
        return False
    complement = {
        'namespace':
        'http://www.sat.gob.mx/sitio_internet/cfd/ComercioExterior11',
        'schemaLocation': db_fname,
    }
    node = etree.Element('{http://www.w3.org/2001/XMLSchema}import',
                         complement)
    res = objectify.fromstring(base64.decodebytes(xsd.datas))
    res.insert(0, node)
    xsd_string = etree.tostring(res, pretty_print=True)
    xsd.datas = base64.encodebytes(xsd_string)
    return True


def _load_locality_sat_catalog(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""

    # Triggers temporarily added to find the ids of many2one fields
    cr.execute(
        """CREATE OR REPLACE FUNCTION l10n_mx_edi_locality()
            RETURNS trigger AS $locality$
            DECLARE
                new_array text[];
            BEGIN
                new_array := (SELECT regexp_split_to_array(NEW.name, E'--+'));
                NEW.name := new_array[1];
                NEW.state_id := (SELECT res_id FROM ir_model_data
                    WHERE name=new_array[2] and model='res.country.state');
                NEW.country_id := (SELECT res_id FROM ir_model_data
                    WHERE name='mx' and model='res.country');
                RETURN NEW;
            END;
           $locality$ LANGUAGE plpgsql;
           CREATE TRIGGER l10n_mx_edi_locality BEFORE INSERT
               ON l10n_mx_edi_res_locality
               FOR EACH ROW EXECUTE PROCEDURE l10n_mx_edi_locality();
           CREATE TRIGGER l10n_mx_edi_locality BEFORE INSERT ON res_city
               FOR EACH ROW EXECUTE PROCEDURE l10n_mx_edi_locality();
        """)

    # Read file and copy data from file
    csv_path = join(dirname(realpath(__file__)), 'data',
                    'l10n_mx_edi.res.locality.csv')
    csv_file = open(csv_path, 'rb')
    cr.copy_from(csv_file, 'l10n_mx_edi_res_locality', sep='|',
                 columns=('code', 'name'))

    csv_path = join(dirname(realpath(__file__)), 'data',
                    'res.city.csv')
    csv_file = open(csv_path, 'rb')
    cr.copy_from(
        csv_file, 'res_city', sep='|', columns=('l10n_mx_edi_code', 'name'))

    cr.execute(
        """delete from res_city where l10n_mx_edi_code is null and name in (select name from res_city where l10n_mx_edi_code is not null)""")

    # Remove triggers
    cr.execute(
        """DROP TRIGGER IF EXISTS l10n_mx_edi_locality
               ON l10n_mx_edi_res_locality;
           DROP TRIGGER IF EXISTS l10n_mx_edi_locality ON res_city;""")

    # Create xml_id, to allow make reference to this data
    # Locality
    cr.execute("""
               INSERT INTO ir_model_data (name, res_id, module, model)
               SELECT
               ('res_locality_mx_' || lower(state.code) || '_' || loc.code),
                    loc.id, 'l10n_mx_edi', 'l10n_mx_edi.res.locality'
               FROM l10n_mx_edi_res_locality AS loc, res_country_state AS state
               WHERE state.id = loc.state_id
               AND (('res_locality_mx_' || lower(state.code) || '_' || loc.code), 'l10n_mx_edi') not in (select name, module from ir_model_data)""")
    # City or Municipality
    cr.execute("""
               INSERT INTO ir_model_data (name, res_id, module, model)
               SELECT ('res_city_mx_' || lower(state.code)
               || '_' || city.l10n_mx_edi_code),
                city.id, 'l10n_mx_edi', 'res.city'
               FROM  res_city AS city, res_country_state AS state
               WHERE state.id = city.state_id AND city.country_id = (
                SELECT id FROM res_country WHERE code = 'MX')
                AND (('res_city_mx_' || lower(state.code)|| '_' || city.l10n_mx_edi_code), 'l10n_mx_edi') not in (select name,  module from ir_model_data)
                """)

def _load_xsd_files(cr, registry, url):
    # TODO: Remove method after merge this PR
    # https://github.com/odoo/enterprise/pull/1617
    fname = url.split('/')[-1]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        res = objectify.fromstring(response.content)
    except requests.exceptions.HTTPError:
        logging.getLogger(__name__).info(
            'I cannot connect with the given URL: %s.', url)
        return ''
    except etree.XMLSyntaxError as e:
        logging.getLogger(__name__).info(
            'You are trying to load an invalid xsd file.\n%s', e)
        return ''
    namespace = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    sub_urls = res.xpath('//xs:import', namespaces=namespace)
    for s_url in sub_urls:
        s_url_catch = _load_xsd_files(
            cr, registry, s_url.get('schemaLocation'))
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
        'datas': base64.encodebytes(xsd_string),
    })
    # Forcing the triggering of the store_fname
    attachment._inverse_datas()
    cr.execute(
        """INSERT INTO ir_model_data (name, res_id, module, model)
           VALUES (%s, %s, 'l10n_mx_edi', 'ir.attachment')""",
        (xsd_fname, attachment.id))
    return join(filestore, attachment.store_fname)


def _load_tariff_fraction_catalog(cr, registry):
    """Import CSV data as it is faster than xml and because we can't use
    noupdate anymore with csv"""
    csv_path = join(dirname(realpath(__file__)), 'data',
                    'l10n_mx_edi.tariff.fraction.csv')
    csv_file = open(csv_path, 'rb')
    cr.copy_expert(
        """COPY l10n_mx_edi_tariff_fraction(code, name, uom_code)
           FROM STDIN WITH DELIMITER '|'""", csv_file)
    # Create xml_id, to allow make reference to this data
    cr.execute(
        """UPDATE l10n_mx_edi_tariff_fraction
        SET active = 't'""")
    cr.execute(
        """INSERT INTO ir_model_data
           (name, res_id, module, model)
           SELECT concat('tariff_fraction_', code), id,
                'l10n_mx_edi_external_trade', 'l10n_mx_edi.tariff.fraction'
           FROM l10n_mx_edi_tariff_fraction """)
