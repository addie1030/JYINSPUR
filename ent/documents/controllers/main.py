# -*- coding: utf-8 -*-

import base64
import zipfile
import io
import logging

import werkzeug
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils

from ast import literal_eval

from odoo import http, fields, models
from odoo.http import request, content_disposition
from odoo.osv import expression
from odoo.tools import pycompat, consteq

logger = logging.getLogger(__name__)


class ShareRoute(http.Controller):

    # util methods #################################################################################

    def _get_file_response(self, id, filename=None, field='datas', share_id=None, share_token=None):
        """
        returns the http response to download one file.

        """
        status, headers, content = request.registry['ir.http'].binary_content(
            id=id, field=field, filename=filename, related_id=share_id,
            access_token=share_token, access_mode='documents_share', download=True)

        if status == 304:
            response = werkzeug.wrappers.Response(status=status, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200:
            response = request.not_found()
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)

        return response

    def _make_zip(self, name, attachments):
        """returns zip files for the Document Inspector and the portal.

        :param name: the name to give to the zip file.
        :param attachments: files (ir.attachment) to be zipped.
        :return: a http response to download a zip file.
        """
        stream = io.BytesIO()
        try:
            with zipfile.ZipFile(stream, 'w') as doc_zip:
                for attachment in attachments:
                    if attachment.type in ['url', 'empty']:
                        continue
                    filename = attachment.datas_fname
                    doc_zip.writestr(filename, base64.b64decode(attachment['datas']),
                                     compress_type=zipfile.ZIP_DEFLATED)
        except zipfile.BadZipfile:
            logger.exception("BadZipfile exception")

        content = stream.getvalue()
        headers = [
            ('Content-Type', 'zip'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(name))
        ]
        return request.make_response(content, headers)

    # Download & upload routes #####################################################################

    @http.route(['/document/zip'], type='http', auth='user')
    def _get_zip(self, file_ids, zip_name, *args, **kwargs):
        """route to get the zip file of the selection in the document's Kanban view (Document inspector).
        :param file_ids: if of the files to zip.
        :param zip_name: name of the zip file.
        """
        ids_list = [int(x) for x in file_ids.split(',')]
        env = request.env
        return self._make_zip(zip_name, env['ir.attachment'].browse(ids_list))

    @http.route(["/document/download/all/<int:share_id>/<access_token>"], type='http', auth='public')
    def share_download_all(self, access_token=None, share_id=None, **kwargs):
        """
        :param share_id: id of the share, the name of the share will be the name of the zip file share.
        :param access_token: share access token
        :returns the http response for a zip file if the token and the ID are valid.
        """
        env = request.env
        try:
            share = env['documents.share'].sudo().browse(share_id)
            if share.state == 'expired':
                return request.not_found()
            if consteq(access_token, share.access_token):
                if share.action != 'upload':
                    attachments = False
                    if share.type == 'domain':
                        domain = []
                        if share.domain:
                            domain = literal_eval(share.domain)
                        domain = expression.AND([domain, [['folder_id', '=', share.folder_id.id]]])
                        attachments = http.request.env['ir.attachment'].sudo().search(domain)
                    elif share.type == 'ids':
                        attachments = share.attachment_ids
                    return self._make_zip((share.name or 'unnamed-link') + '.zip', attachments)
        except Exception:
            logger.exception("Failed to zip share link id: %s" % share_id)
        return request.not_found()

    @http.route(["/document/avatar/<int:share_id>/<access_token>"], type='http', auth='public')
    def get_avatar(self, access_token=None, share_id=None, **kwargs):
        """
        :param share_id: id of the share.
        :param access_token: share access token
        :returns the picture of the share author for the front-end view.
        """
        try:
            env = request.env
            share = env['documents.share'].sudo().browse(share_id)
            if consteq(access_token, share.access_token):
                return base64.b64decode(env['res.users'].sudo().browse(share.create_uid.id).image_small)
            else:
                return request.not_found()
        except Exception:
            logger.exception("Failed to download portrait id: %s" % id)
        return request.not_found()

    @http.route(["/document/thumbnail/<int:share_id>/<access_token>/<int:id>"],
                type='http', auth='public')
    def get_thumbnail(self, id=None, access_token=None, share_id=None, **kwargs):
        """
        :param id:  id of the attachment
        :param access_token: token of the share link
        :param share_id: id of the share link
        :return: the thumbnail of the attachment for the portal view.
        """
        try:
            env = request.env
            share = env['documents.share'].sudo().browse(share_id)
            if share.state == 'expired':
                return request.not_found()
            if consteq(share.access_token, access_token):
                return self._get_file_response(id, share_id=share.id, share_token=share.access_token, field='thumbnail')
        except Exception:
            logger.exception("Failed to download thumbnail id: %s" % id)
        return request.not_found()

    # single file download route.
    @http.route(["/document/download/<int:share_id>/<access_token>/<int:id>"],
                type='http', auth='public')
    def download_one(self, id=None, access_token=None, share_id=None, **kwargs):
        """
        used to download a single file from the portal multi-file page.

        :param id: id of the file
        :param access_token:  token of the share link
        :param share_id: id of the share link
        :return: a portal page to preview and download a single file.
        """
        env = request.env
        share = env['documents.share'].sudo().browse(share_id)
        if consteq(access_token, share.access_token):
            try:
                if share.action != 'upload' and share.state != 'expired':
                    return self._get_file_response(id, share_id=share_id, share_token=share.access_token, field='datas')
            except Exception:
                logger.exception("Failed to download attachment %s" % id)

        return request.not_found()

    # Upload file route.
    @http.route(["/document/upload/<int:arg_id>/<token>/"], type='http', auth='public', methods=['POST'], csrf=False)
    def upload_attachment(self, arg_id=None, token=None, **kwargs):
        """
        Allows public upload if provided with the right token and share_Link.

        :param arg_id: id of the share.
        :param token: share access token.
        :return if files are uploaded, recalls the share portal with the updated content.
        """
        share = http.request.env['documents.share'].sudo().search([('id', '=', arg_id)])
        if 'upload' not in share.action or share.state == 'expired':
            return http.request.not_found()
        if consteq(token, share.access_token):
            attachments = request.env['ir.attachment']
            folder = share.folder_id
            folder_id = folder.id or False
            try:
                for file in request.httprequest.files.getlist('files'):
                    data = file.read()

                    attachment_dict = {
                        'tag_ids': [(6, 0, share.tag_ids.ids)],
                        'partner_id': share.partner_id.id,
                        'owner_id': share.owner_id.id,
                        'folder_id': folder_id,
                        'mimetype': file.content_type,
                        'name': file.filename,
                        'datas_fname': file.filename,
                        'datas': base64.b64encode(data),
                    }
                    attachment = attachments.sudo().create(attachment_dict)
                    if share.activity_option:
                        attachment.documents_set_activity(settings_model=share)

            except Exception as e:
                logger.exception("Failed to upload attachment")
        else:
            return http.request.not_found()

        return """<script type='text/javascript'>
                    window.open("/document/share/%s/%s", "_self");
                </script>""" % (arg_id, token)

    # Frontend portals #############################################################################

    # share portals route.
    @http.route(['/document/share/<int:share_id>/<token>'], type='http', auth='public')
    def share_portal(self, share_id=None, token=None):
        """
        Leads to a public portal displaying downloadable files for anyone with the token.

        :param share_id: id of the share link
        :param token: share access token
        """
        try:
            share = http.request.env['documents.share'].sudo().search([('id', '=', share_id)])
            if share.state == 'expired':
                expired_options = {
                    'expiration_date': share.date_deadline,
                    'author': share.create_uid.name,
                }
                return request.render('documents.not_available', expired_options)
            if not consteq(token, share.access_token):
                return request.not_found()

            if share.type == 'domain':
                domain = []
                if share.domain:
                    domain = literal_eval(share.domain)
                domain += [['folder_id', '=', share.folder_id.id]]
                attachments = http.request.env['ir.attachment'].sudo().search(domain)
            elif share.type == 'ids':
                attachments = share.attachment_ids
            else:
                return request.not_found()

            options = {
                'base_url': http.request.env["ir.config_parameter"].sudo().get_param("web.base.url"),
                'token': str(token),
                'upload': share.action == 'downloadupload',
                'share_id': str(share.id),
                'author': share.create_uid.name,
            }
            if len(attachments) == 1 and share.type == 'ids':
                options.update(attachment=attachments[0])
                return request.render('documents.share_single', options)
            else:
                options.update(all_button='binary' in [attachment.type for attachment in attachments],
                               attachment_ids=attachments)
                return request.render('documents.share_page', options)
        except Exception:
            logger.exception("Failed to generate the multi file share portal")
        return request.not_found()


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _check_access_mode(cls, env, id, access_mode, model, access_token=None, related_id=None):
        """
        Implemented by each module to define an additional way to check access.

        :param env: the env of binary_content
        :param id: id of the record from which to fetch the binary
        :param access_mode: typically a string that describes the behaviour of the custom check
        :param model: the model of the object for which binary_content was called
        :param related_id: the id of the documents.share.
        :return: object binary if the access_token matches the share and the attachment is in the share.
        """
        if access_mode == 'documents_share' and related_id:
            share = env['documents.share'].sudo().browse(int(related_id))
            if share:
                if share.state == 'expired':
                    return False
                if not consteq(access_token, share.access_token or ''):
                    return False
                elif share.type == 'ids' and (id in share.attachment_ids.ids):
                    return True
                elif share.type == 'domain':
                    obj = env[model].sudo().browse(int(id))
                    share_domain = []
                    if share.domain:
                        share_domain = literal_eval(share.domain)
                    domain = [['folder_id', '=', share.folder_id.id]] + share_domain
                    attachments_check = http.request.env['ir.attachment'].sudo().search(domain)
                    if obj in attachments_check:
                        return True
        return super(IrHttp, cls)._check_access_mode(env, id, access_mode, model,
                                                    access_token=access_token, related_id=related_id)
