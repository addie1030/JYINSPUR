odoo.define('voip.phonecall', function (require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var Widget = require('web.Widget');

var _t = core._t;

var PhonecallWidget = Widget.extend({
    "template": "voip.PhonecallWidget",
    events: {
        "click": "_onSelectCall",
        "click .o_dial_remove_phonecall": "_onRemovePhonecall"
    },
    /**
     * @constructor
     */
    init: function (parent, phonecall) {
        this._super.apply(this, arguments);
        this.id = phonecall.id;
        this.state = phonecall.state;
        if (phonecall.partner_name) {
            this.partner_name = phonecall.partner_name;
        } else {
            this.partner_name = phonecall.name;
        }
        this.name = phonecall.name;
        this.short_name =phonecall.name;
        this.partner_id = phonecall.partner_id;
        this.phone = phonecall.phone;
        this.mobile = phonecall.mobile;
        this.date = phonecall.call_date;
        this.seconds = (phonecall.duration % 1 * 60).toFixed();
        this.minutes = Math.floor(phonecall.duration).toString();
        this.image_small = phonecall.partner_image_small;
        this.email = phonecall.partner_email;
        this.activity_id = phonecall.activity_id;
        this.activity_res_id = phonecall.activity_res_id;
        this.activity_res_model = phonecall.activity_res_model;
        this.activity_model_name = phonecall.activity_model_name;
        this.activity_summary = phonecall.activity_summary;
        this.note = phonecall.activity_note || phonecall.note;
        this.isContact = phonecall.isContact;
        this.isRecent = phonecall.isRecent;
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Makes rpc to log the hangup call.
     *
     * @return {Deferred}
     */
    hangup: function () {
        var self = this;
        return this._rpc({
            model: 'voip.phonecall',
            method: 'hangup_call',
            args: [this.id],
        }).then(function () {
            self.call('mail_service', 'getMailBus').trigger('voip_reload_chatter');
        });
    },
    /**
     * Makes rpc to set the call as rejected.
     *
     * @return {Deferred}
     */
    rejectPhonecall: function () {
        return this._rpc({
            model: 'voip.phonecall',
            method: 'rejected_call',
            args: [this.id],
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     *
     * @param {Event} e
     */
    _onRemovePhonecall: function (e) {
        e.stopPropagation();
        e.preventDefault();
        this.trigger("removePhonecall",this.id);
    },
    /**
     * @private
     */
    _onSelectCall: function () {
        this.trigger("selectCall", this);
    },

});

var PhonecallDetails = Widget.extend({
    "template": "voip.PhonecallDetails",
    events: {
        "click .o_dial_activity_cancel": "_onCancel",
        "click .o_dial_activity_done": "_onMarkAsDone",
        "click .o_dial_call_number": "_onCallNumber",
        "click .o_dial_email": "_onSendEmail",
        "click .o_dial_log": "_onLogCall",
        "click .o_dial_mute_button": "_onMuteButtonClick",
        "click .o_dial_unmute_button": "_onUnmuteButtonClick",
        "click .o_dial_reschedule_activity": "_onRescheduleActivity",
        "click .o_dial_to_partner": "_onToPartnerClick",
        "click .o_dial_to_record": "_onToRecordClick",
        "click .o_dial_transfer_button": "_onTransferButtonClick",
        "click .o_phonecall_details_close": "_onClosePhonecallDetails",
    },

    /**
     * @constructor
     */
    init: function (parent, phonecall) {
        this._super.apply(this, arguments);
        this.id = phonecall.id;
        this.state = phonecall.state;
        if (phonecall.partner_name) {
            this.partner_name = phonecall.partner_name;
        } else {
            this.partner_name = _t("Unknown");
        }
        this.name = phonecall.name;
        this.partner_id = phonecall.partner_id;
        this.phone = phonecall.phone;
        this.mobile = phonecall.mobile;
        this.date = phonecall.date;
        this.seconds = phonecall.seconds;
        this.minutes = phonecall.minutes;
        this.image_small = phonecall.image_small;
        this.email = phonecall.partner_email;
        this.activity_id = phonecall.activity_id;
        this.activity_res_id = phonecall.activity_res_id;
        this.activity_res_model = phonecall.activity_res_model;
        this.activity_model_name = phonecall.activity_model_name;
        this.activity_summary = phonecall.activity_summary;
        this.isMuted = false;
    },
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this.$closeDetails = this.$('.o_phonecall_details_close');
        this.$phonecallInfo = this.$('.o_phonecall_info');
        this.$phonecallDetails = this.$('.o_phonecall_details');
        this.$phonecallActivityButtons = this.$('.o_phonecall_activity_button');
        this.$phonecallInCall = this.$('.o_phonecall_in_call');
        this.$('.o_dial_transfer_button').attr('disabled', 'disabled');
        this.$mute_button = this.$('.o_dial_mute_button');
        this.$mute_icon = this.$('.o_dial_mute_button .fa');
        this.$mute_button.attr('disabled', 'disabled');
        this.$timerSeconds = this.$('.o_dial_timer_seconds');
        this.$timerMinutes = this.$('.o_dial_timer_minutes');
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * The call is accepted then we can offer more options to the user.
     */
    activateInCallButtons: function () {
        this.$('.o_dial_transfer_button').removeAttr('disabled');
        this.$('.o_dial_mute_button').removeAttr('disabled');
    },
    /**
     * Changes the display to show the in call layout.
     */
    hideCallDisplay: function () {
        this.$phonecallDetails.removeClass('details_in_call');
        this.$closeDetails.show();
        this.$phonecallInfo.show();
        this.$phonecallInCall.hide();
        this.$el.removeClass('in_call');
    },
    /**
     * Changes the display to show the in call layout.
     */
    showCallDisplay: function () {
        var self = this;
        this.$phonecallDetails.addClass('details_in_call');
        this.$closeDetails.hide();
        this.$phonecallInfo.hide();
        this.$phonecallInCall.show();
        this.$phonecallActivityButtons.hide();
        this.$el.addClass('in_call');
        var sec = 0;
        function formatTimer ( val ) { return val > 9 ? val : "0" + val; }
        this.timer = setInterval( function(){
            self.$timerSeconds.html(formatTimer(++sec%60));
            self.$timerMinutes.html(formatTimer(parseInt(sec/60)));
        }, 1000);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onCallNumber: function (ev) {
        ev.preventDefault();
        this.trigger_up('clickOnNumber', {number: ev.currentTarget.text});
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onCancel: function (ev) {
        var self = this;
        ev.preventDefault();
        this._rpc({
            model: 'mail.activity',
            method: 'unlink',
            args: [[this.activity_id]],
        }).then(function () {
            self.trigger_up('closePhonecallDetails');
        });
    },
    /**
     * @private
     */
    _onClosePhonecallDetails: function () {
        this.trigger_up('closePhonecallDetails');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onLogCall: function (ev) {
        ev.preventDefault();
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.activity_res_id,
                default_res_model: this.activity_res_model,
            },
            res_id: this.activity_id,
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onMarkAsDone: function (ev) {
        var self = this;
        ev.preventDefault();
        this._rpc({
            model: 'mail.activity',
            method: 'action_done',
            args: [[this.activity_id]],
        }).then(function () {
            self.call('mail_service', 'getMailBus').trigger('voip_reload_chatter');
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onMuteButtonClick: function (ev) {
        ev.preventDefault();
        if (!this.isMuted) {
            this.trigger_up('muteCall');
            this.$mute_icon.removeClass('fa-microphone');
            this.$mute_icon.addClass('fa-microphone-slash');
            this.isMuted = true;
        } else {
            this.trigger_up('unmuteCall');
            this.$mute_icon.addClass('fa-microphone');
            this.$mute_icon.removeClass('fa-microphone-slash');
            this.isMuted = false;
        }
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onRescheduleActivity: function (ev) {
        ev.preventDefault();
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.activity_res_id,
                default_res_model: this.activity_res_model,
            },
            res_id: false,
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onSendEmail: function (ev) {
        ev.preventDefault();
        if (this.activity_res_model && this.activity_res_id) {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mail.compose.message',
                src_model: 'voip.phonecall',
                multi: "True",
                target: 'new',
                key2: 'client_action_multi',
                context: {
                            'default_composition_mode': 'mass_mail',
                            'active_ids': [this.activity_res_id],
                            'default_model': this.activity_res_model,
                            'default_partner_ids': this.partner_id ? [this.partner_id] : [],
                            'default_use_template': true,
                        },
                views: [[false, 'form']],
            });
        } else if (this.partner_id) {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mail.compose.message',
                src_model: 'voip.phonecall',
                multi: "True",
                target: 'new',
                key2: 'client_action_multi',
                context: {
                            'default_composition_mode': 'mass_mail',
                            'active_ids': [this.partner_id],
                            'default_model': 'res.partner',
                            'default_partner_ids': [this.partner_id],
                            'default_use_template': true,
                        },
                views: [[false, 'form']],
            });
        }
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onToPartnerClick: function (ev) {
        ev.preventDefault();
        var res_id;
        var def = $.Deferred();
        if (this.partner_id) {
            res_id = this.partner_id;
            def.resolve();
        } else {
            var domain = ['|',
                          ['phone', '=', this.phone],
                          ['mobile', '=', this.phone]];
            this._rpc({
                method: 'search_read',
                model: "res.partner",
                kwargs: {
                    domain: domain,
                    fields: ['id'],
                    limit: 1
                }
            }).then(function(ids) {
                if (ids.length)
                    res_id = ids[0].id;
            }).always(function(){
                def.resolve();
            })
        }
        $.when(def).then((function() {
            if (res_id !== undefined) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: "res.partner",
                    res_id: res_id,
                    views: [[false, 'form']],
                    target: 'current',
                });
            } else {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: "res.partner",
                    views: [[false, 'form']],
                    target: 'current',
                    context: {
                        default_email: this.email,
                        default_phone: this.phone,
                        default_mobile: this.mobile,
                    },
                });
            }
        }).bind(this));
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onTransferButtonClick: function (ev) {
        ev.preventDefault();
        //Launch the transfer wizard
        this.do_action({
            type: 'ir.actions.act_window',
            key2: 'client_action_multi',
            src_model: "voip.phonecall",
            res_model: "voip.phonecall.transfer.wizard",
            multi: "True",
            target: 'new',
            context: {},
            views: [[false, 'form']],
            flags: {
                'headless': true,
            },
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onToRecordClick: function (ev) {
        ev.preventDefault();
        var self = this;
        var resModel = this.activity_res_model;
        var resId = this.activity_res_id;
        this._rpc({
            model: resModel,
            method: 'get_formview_id',
            args: [[resId], session.user_context],
        }).then(function (viewId) {
            self.do_action({
                type:'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_model: resModel,
                views: [[viewId || false, 'form']],
                res_id: resId,
            });
        });
    },
});

return {
    PhonecallWidget: PhonecallWidget,
    PhonecallDetails: PhonecallDetails,
};

});
