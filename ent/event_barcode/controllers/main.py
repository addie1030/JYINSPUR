# -*- coding: utf-8 -*-
from odoo import fields, http, _
from odoo.http import request


class EventBarcode(http.Controller):

    @http.route('/event_barcode/register_attendee', type='json', auth="user")
    def register_attendee(self, barcode, event_id, **kw):
        Registration = request.env['event.registration']
        attendee = Registration.search([('barcode', '=', barcode), ('event_id', '=', event_id)], limit=1)
        if not attendee:
            return {'warning': _('This ticket is not valid for this event')}
        res = {
            'registration': dict(attendee.summary(), id=attendee.id),
        }
        count = Registration.search_count([('state', '=', 'done'), ('event_id', '=', event_id)])
        attendee_name = attendee.name or _('Attendee')
        if attendee.state == 'cancel':
            res.update({'warning': _('Canceled registration')})
        elif attendee.state != 'done':
            attendee.write({'state': 'done', 'date_closed': fields.Datetime.now()})
            count += 1
            res.update({'success': _('%s is successfully registered') % attendee_name})
        else:
            res.update({'warning': _('%s is already registered') % attendee_name})
        res['count'] = count
        return res

    @http.route(['/event_barcode/event'], type='json', auth="user")
    def get_event_data(self, event_id):
        event = request.env['event.event'].browse(event_id)
        return {
            'name': event.name,
            'start_date': event.date_begin,
            'end_date': event.date_end,
            'country': event.address_id.country_id.name,
            'city': event.address_id.city,
            'count': len(event.registration_ids.filtered(lambda reg: reg.state == 'done')),
            'total_attendee': len(event.registration_ids.filtered(lambda reg: reg.state != 'cancel'))
        }
