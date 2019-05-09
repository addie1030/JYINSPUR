odoo.define('event_barcode.EventScanView', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Dialog = require('web.Dialog');
var time = require('web.time');

var _t = core._t;
var QWeb = core.qweb;


// load widget with main barcode scanning View
var EventScanView = AbstractAction.extend({
    template: 'event_barcode_template',
    events: {
        'keypress #event_barcode': 'on_manual_scan',
        'click .o_event_social': 'open_attendees',
        'click .o_event_info': 'open_event_form',
    },

    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.action = action;
    },
    willStart: function() {
        var self = this;
        return this._super().then(function() {
            return self._rpc({
                route: '/event_barcode/event',
                params: {
                    event_id: self.action.context.active_id
                }
            }).then(function (result) {
                self.data = self.prepare_data(result);
            });
        });
    },
    start: function() {
        var self = this;
        core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        this.updateCount(
            self.$('.o_event_reg_attendee'),
            self.data.count
        );
    },
    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        this._super();
    },
    prepare_data: function(result) {
        var start_date = moment(time.auto_str_to_date(result.start_date));
        var end_date = moment(time.auto_str_to_date(result.end_date));
        var localedata = start_date.localeData();
        result['date'] =  start_date.date() === end_date.date() ? start_date.date() : _.str.sprintf("%s - %s", start_date.date(), end_date.date());
        result['month'] = start_date.month() === end_date.month() ? localedata._months[start_date.month()] : _.str.sprintf('%s - %s', localedata._monthsShort[start_date.month()], localedata._monthsShort[end_date.month()]);
        return result;
    },
    on_manual_scan: function(e) {
        if (e.which === 13) { // Enter
            var value = $(e.currentTarget).val().trim();
            if(value) {
                this._onBarcodeScanned(value);
                $(e.currentTarget).val('');
            } else {
                this.do_warn(_t('Error'), _t('Invalid user input'));
            }
        }
    },
    _onBarcodeScanned: function(barcode) {
        var self = this;
        this._rpc({
            route: '/event_barcode/register_attendee',
            params: {
                barcode: barcode,
                event_id: self.action.context.active_id
            }
        }).then(function(result) {
            if (result.success) {
                self.updateCount(
                    self.$('.o_event_reg_attendee'),
                    result.count
                );
            }
            if (result.registration && (result.registration.alert || !_.isEmpty(result.registration.information))) {
                new Dialog(self, {
                    title: _t('Registration Summary'),
                    size: 'medium',
                    $content: QWeb.render('event_registration_summary', {
                        'success': result.success,
                        'warning': result.warning,
                        'registration': result.registration
                    }),
                    buttons: [
                        {text: _t('Close'), close: true, classes: 'btn-primary'},
                        {text: _t('Print'), click: function () {
                          self.do_action({
                              type: 'ir.actions.report.xml',
                              report_type: 'qweb-pdf',
                              report_name: 'event.event_registration_report_template_badge/' + result.registration.id,
                          });
                        }
                    },
                    {text: _t('View'), close: true, click: function() {
                        self.do_action({
                            type: 'ir.actions.act_window',
                            res_model: 'event.registration',
                            res_id: result.registration.id,
                            views: [[false, 'form']],
                            target: 'current'
                        });
                    }},
                ]}).open();
            } else if (result.success) {
                self.do_notify(result.success, false, false, 'o_event_success');
            } else if (result.warning) {
                self.do_warn(_t("Warning"), result.warning);
            }
        });
    },
    open_attendees: function() {
        this.do_action({
            name: "Attendees",
            type:'ir.actions.act_window',
            res_model: 'event.registration',
            views: [[false, 'list'], [false, 'form']],
            context :{
                'search_default_event_id': this.action.context.active_id,
                'default_event_id': this.action.context.active_id,
                'search_default_expected': true
            }
        });
    },
    open_event_form: function() {
        this.do_action({
            name: 'Event',
            type: 'ir.actions.act_window',
            res_model: 'event.event',
            views: [[false, 'form'], [false, 'kanban'], [false, 'calendar'], [false, 'list']],
            res_id: this.action.context.active_id,
        });
    },
    updateCount: function(element, count) {
        element.html(count);
    }
});

core.action_registry.add('even_barcode.scan_view', EventScanView);

return EventScanView;

});
