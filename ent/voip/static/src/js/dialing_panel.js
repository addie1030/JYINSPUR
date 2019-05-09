odoo.define('voip.dialingPanel', function (require) {
"use strict";

var DialingTab = require('voip.dialing_tab');
var UserAgent = require('voip.user_agent');

var basic_fields = require('web.basic_fields');
var core = require('web.core');
var config = require('web.config');
var real_session = require('web.session');
var SystrayMenu = require('web.SystrayMenu');
var WebClient = require('web.WebClient');
var Widget = require('web.Widget');

var dialingPanel = null;
var _t = core._t;
var HEIGHT_OPEN = '480px';
var HEIGHT_FOLDED = '0px';

// As voip is not supported on mobile devices, we want to keep the standard phone widget
if (config.device.isMobile) {
    return;
}

var DialingPanel = Widget.extend({
    template: "voip.DialingPanel",
    events:{
        "input .o_dial_search_input": "_onSearchChange",
        "click .o_dial_fold": "_onToggleFold",
        "click .o_dial_window_close": function (ev) {ev.preventDefault();ev.stopPropagation();this._onToggleDisplay();},
        "click .o_dial_call_button":  "_onCallButtonClick",
        "click .o_dial_keypad_icon": function (ev) {ev.preventDefault();this._onToggleKeypad();},
        "click .O_dial_number": function (ev) {ev.preventDefault();this._onKeypadButtonClick(ev.currentTarget.textContent);},
        "click .o_dial_keypad_backspace": "_onKeypadBackspaceClick",
        "click .o_dial_hangup_button": "_onHangupButtonClick",
        "click .o_dial_tabs .o_dial_tab": "_onClickTab",
    },
    custom_events:{
        'muteCall': '_onMuteCall',
        'unmuteCall': '_onUnmuteCall',
        'sip_accepted': '_onSipAccepted',
        'sip_cancel': '_onSipRejected',
        'sip_rejected': '_onSipRejected',
        'sip_bye': '_onSipBye',
        'sip_error': '_onSipError',
        'sip_error_resolved': '_onSipErrorResolved',
        'sip_customer_unavailable': '_onSipCustomerUnavailable',
        'sip_incoming_call': '_onSipIncomingCall',
        'toggleHangupButton': '_onToggleHangupButton',
    },
    /**
     * @constructor
     */
    init: function () {
        if (dialingPanel) {
            return dialingPanel;
        }
        this._super.apply(this, arguments);
        this.inCall = false;
        this.shown = false;
        this.folded = false;
        this.silentMode = false;

        this.userAgent = new UserAgent(this);


        dialingPanel = this;
        this.tabs = {
            'recent': new DialingTab.RecentTab(this),
            'nextActivities': new DialingTab.ActivitiesTab(this),
            'contacts': new DialingTab.ContactsTab(this),
        };
        this._onSearchChange = _.debounce(this._onSearchChange, 500);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        this.$el.css("bottom", 0);
        this.$tabsPanel = this.$('.o_dial_panel');
        this.$tabs = this.$('.o_dial_tabs');
        this.$mainButtons = this.$('.o_dial_main_buttons');
        this.$callButton = this.$('.o_dial_call_button');
        this.$searchBar = this.$('.o_dial_searchbar');
        this.$searchInput = this.$('.o_dial_search_input');
        this.$keypad = this.$('.o_dial_keypad');
        this.$keypad.hide();
        this.$keypadInputDiv = this.$('.o_dial_keypad_input_div');
        this.$keypadInput = this.$('.o_dial_keypad_input');
        this.tabs.nextActivities.appendTo(this.$('.o_dial_next_activities'));
        this.tabs.recent.appendTo(this.$('.o_dial_recent'));
        this.tabs.contacts.appendTo(this.$('.o_dial_contacts'));
        this.$el.hide();
        this.activeTab = this.tabs.nextActivities;

        core.bus.on('transfer_call', this, this._onTransferCall);
        core.bus.on('voip_onToggleDisplay', this, this._onToggleDisplay);

        this.call('bus_service', 'onNotification', this, function (notifications) {
            _.each(notifications, function (notification) {
                if (notification[1].type === 'refresh_voip') {
                    self._onNotifRefreshVoip();
                }
            });
        });
        _.mapObject(this.tabs, function (tab) {
            tab.on('callNumber', self, function (ev) {
                this._makeCall(ev.data.number);
            });
            tab.on('hidePanelHeader', self, function () {
                this._hideHeader();
            });
            tab.on('showPanelHeader', self, function () {
                this._showHeader();
            });
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Block the VOIP widget
     * @private
     */
    _blockOverlay: function (message) {
        this.$tabsPanel.block({message: message});
        this.$mainButtons.block();
    },
    /**
     * @private
     */
    _fold: function () {
        this.$el.animate({
            height: this.folded ? HEIGHT_FOLDED : HEIGHT_OPEN
        });
        if (this.folded) {
            this.$('.o_dial_fold').css("bottom", "25px");
            this.$('.o_dial_window_close').hide();
            this.$('.o_dial_unfold').show();
        } else {
            this.$('.o_dial_fold').css("bottom", 0);
            this.$('.o_dial_window_close').show();
            this.$('.o_dial_unfold').hide();
        }
    },
    /**
     * Hides the search input and the tabs.
     *
     * @private
     */
    _hideHeader: function () {
        this.$searchBar.hide();
        this.$tabs.hide();
    },
    /**
     * @private
     * @param  {String} number
     * @param {Object} phonecall if the event function already created a phonecall;
     *                           this phonecall is passed to the initPhonecall function
     *                           in order to not create a new one.
     */
    _makeCall: function (number, phonecall) {
        if (!this.inCall) {
            if (!number) {
                this.do_notify(_t('The phonecall has no number'),
                    _t('Please check if a phone number is given for the current phonecall'));
                return;
            }
            if (!this.shown || this.folded) {
                this._toggleDisplay();
            }
            this.activeTab.initPhonecall(phonecall);
            this.userAgent.makeCall(number);
            this.inCall = true;
        } else {
            this.do_notify(_t('You are already in a call'));
        }
    },
    /**
     * Refreshes the phonecall list of the active tab.
     *
     * @private
     */
    _refreshPhonecallsStatus: function () {
        if (!this.inCall) {
            this.activeTab.refreshPhonecallsStatus();
        }
    },
    /**
     * Shows the search input and the tabs.
     *
     * @private
     */
    _showHeader: function () {
        this.$searchBar.show();
        this.$tabs.show();
    },
    /**
     * @private
     */
    _toggleCallButton: function () {
        this.$callButton.addClass('o_dial_call_button');
        this.$callButton.removeClass('o_dial_hangup_button');
    },
    /**
     * @private
     */
    _toggleDisplay: function () {
        if (this.shown) {
            if (!this.folded) {
                this.$el.hide();
                this.shown = false;
            } else {
                this._onToggleFold(false);
            }
        } else {
            this.$el.show();
            this.shown = true;
            this.folded = false;
            this.$searchInput.focus();
        }
    },
    /**
     * @private
     */
    _toggleHangupButton: function () {
        this.$callButton.removeClass('o_dial_call_button');
        this.$callButton.addClass('o_dial_hangup_button');
    },
    /**
     * @private
     */
    _toggleKeypadInputDiv: function () {
        if (this.inCall) {
            this.$keypadInputDiv.hide();
        } else {
            this.$keypadInputDiv.show();
            this.$keypadInput.focus();
        }
    },
    /**
     * Unblock the VOIP widget
     * @private
     */
    _unblockOverlay: function () {
        this.$tabsPanel.unblock();
        this.$mainButtons.unblock();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Function called when a phonenumber is clicked in the activity widget.
     *
     * @param {Object} params
     * @param  {String} params.number
     * @param  {Integer} params.activityId
     */
    callFromActivityWidget: function (params) {
        if (!this.inCall) {
            var self = this;
            this.$('.o_dial_tabs > li.active, .tab-pane.active').removeClass('active');
            this.$('li.o_dial_activities_tab, .tab-pane.o_dial_next_activities').addClass('active');
            this.activeTab = this.tabs.nextActivities;
            this.activeTab.callFromActivityWidget(params).done(function () {
                self._makeCall(params.number);
            });
        } else {
            this.do_notify(_t('You are already in a call'));
        }
    },
    /**
     * Function called when widget phone is clicked.
     *
     * @param {Object} params
     * @param  {String} params.number
     * @param  {String} params.resModel
     * @param  {Integer} params.resId
     */
    callFromPhoneWidget: function (params) {
        if (!this.inCall) {
            var self = this;
            this.$('.o_dial_tabs > li.active, .tab-pane.active').removeClass('active');
            this.$('li.o_dial_recent_tab, .tab-pane.o_dial_recent').addClass('active');
            this.activeTab = this.tabs.recent;
            this.activeTab.callFromPhoneWidget(params).done(function (phonecall) {
                self._makeCall(params.number, phonecall);
            });
        } else {
            this.do_notify(_t('You are already in a call'));
        }
    },
    /**
     * Function called when a phone number is clicked
     */
    getPbxConfiguration: function () {
        return this.userAgent.getPbxConfiguration();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Method handeling the click on the call button.
     * If a phonecall detail is displayed, then call its first number.
     * If there is a search value, we call it.
     * If we are on the keypad and there is a value, we call it.
     *
     * @private
     */
    _onCallButtonClick: function () {
        if (!this.inCall) {
            var self = this;
            var number;
            if (this.$('.o_phonecall_details').is(':visible')) {
                this.activeTab.callFirstNumber();
            } else if (this.$tabsPanel.is(':visible')) {
                number = this.$searchInput.val();
                if (number) {
                    this.$('.o_dial_tabs > li.active, .tab-pane.active').removeClass('active');
                    this.$('li.o_dial_recent_tab, .tab-pane.o_dial_recent').addClass('active');
                    this.activeTab = this.tabs.recent;
                    this.activeTab.callFromNumber(number).done(function (phonecall) {
                        self.$searchInput.val('');
                        self._makeCall(number, phonecall);
                    });
                }
            } else {
                number = this.$keypadInput.val();
                if (number) {
                    this._onToggleKeypad();
                    this.$('.o_dial_tabs > li.active, .tab-pane.active').removeClass('active');
                    this.$('li.o_dial_recent_tab, .tab-pane.o_dial_recent').addClass('active');
                    this.activeTab = this.tabs.recent;
                    this.activeTab.callFromNumber(number).done(function (phonecall) {
                        self._makeCall(number, phonecall);
                        self.$keypadInput.val("");
                    });
                }
            }
        }
    },
    /**
     * @private
     * @param  {Object} ev
     */
    _onClickTab: function (ev) {
        ev.preventDefault();
        this.activeTab = this.tabs[ev.currentTarget.getAttribute("aria-controls")];
        this.$searchInput.val('');
        this._refreshPhonecallsStatus();
    },
    /**
     * @private
     */
    _onHangupButtonClick: function () {
        this.userAgent.hangup();
    },
    /**
     * @private
     */
    _onKeypadBackspaceClick: function () {
        if (!this.inCall) {
            var val = this.$keypadInput.val();
            this.$keypadInput.val(val.slice(0, -1));
        }
    },
    /**
     * @private
     * @param {String} number the keypad number clicked
     */
    _onKeypadButtonClick: function (number) {
        if (this.inCall) {
            this.userAgent.sendDtmf(number);
        } else {
            var val = this.$keypadInput.val();
            this.$keypadInput.val(val + number);
        }
    },
    /**
     * @private
     */
    _onMuteCall: function () {
        this.userAgent.muteCall();
    },
    /**
     * @private
     */
    _onNotifRefreshVoip: function () {
        if (!this.inCall) {
            if (this.activeTab === this.tabs.nextActivities) {
                this.activeTab.refreshPhonecallsStatus();
            }
        }
    },
    /**
     * @private
     */
    _onSearchChange: function (event) {
        var search = $(event.target).val();
        this.activeTab.searchPhonecall(search);
    },
    /**
     * @private
     */
    _onSipAccepted: function () {
        this.activeTab.onCallAccepted();
    },
    /**
     * @private
     */
    _onSipBye: function () {
        this.inCall = false;
        this._toggleCallButton();
        this.activeTab.hangupPhonecall();
    },
    /**
     * @private
     */
    _onSipCustomerUnavailable: function () {
        this.do_notify(_t('Customer unavailable'),
            _t('The customer is temporary unavailable. Please try later.'));
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onSipError: function (event) {
        var self = this;
        var message = event.data.msg;
        this.inCall = false;
        this._toggleCallButton();

        if (event.data.connecting){
            this._blockOverlay(message);
        } else if (event.data.temporary) {
            this._blockOverlay(message);
            this.$('.blockOverlay').on("click", function () {self._onSipErrorResolved();});
            this.$('.blockOverlay').attr('title', _t('Click to unblock'));
        } else {
            this._blockOverlay(message + '<br/><button type="button" class="btn btn-danger btn-configuration">Configuration</button>');

            this.$('.btn-configuration').on("click", function () {
                //Call in order to get the id of the user's preference view instead of the user's form view
                self._rpc({
                        model: 'ir.model.data',
                        method: 'xmlid_to_res_model_res_id',
                        args:["base.view_users_form_simple_modif"],
                    })
                    .then(function (data) {
                        self.do_action({
                            name: "Change My Preferences",
                            type: "ir.actions.act_window",
                            res_model: "res.users",
                            res_id: real_session.uid,
                            target: "new",
                            xml_id: "base.action_res_users_my",
                            views: [[data[1], 'form']],
                        });
                    });
            });
        }
    },
    /**
     * @private
     */
    _onSipErrorResolved: function () {
        this._unblockOverlay();
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onSipIncomingCall: function (event) {
        if (!this.inCall) {
            this.inCall = true;
            this.$('.o_dial_tabs > li.active, .tab-pane.active').removeClass('active');
            this.$('li.o_dial_recent_tab, .tab-pane.o_dial_recent').addClass('active');
            this.activeTab = this.tabs.recent;
            this._toggleHangupButton();
            this.activeTab.onIncomingCallAccepted(event.data);
        }
    },
    /**
     * @private
     */
    _onSipRejected: function () {
        this.inCall = false;
        this.activeTab.rejectPhonecall();
        this._toggleCallButton();
    },
    /**
     * @private
     */
    _onToggleDisplay: function () {
        this._toggleDisplay();
        this._refreshPhonecallsStatus();
    },
    /**
     * @private
     */
    _onToggleFold: function (fold) {
        if (!config.device.isMobile) {
            if (this.folded) {
                this._refreshPhonecallsStatus();
            }
            this.folded = _.isBoolean(fold) ? fold : !this.folded;
            this._fold();
        } else {
            this._onToggleDisplay();
        }
    },
    /**
     * @private
     */
    _onToggleHangupButton: function () {
        this._toggleHangupButton();
    },
    /**
     * @private
     */
    _onToggleKeypad: function () {
        if (this.$tabsPanel.is(":visible")) {
            this.$tabsPanel.hide();
            this.$keypad.show();
            this._toggleKeypadInputDiv();
        } else {
            this.$tabsPanel.show();
            this.$keypad.hide();
        }
    },
    /**
     * @private
     * @param {String} number
     */
    _onTransferCall: function (number) {
        this.userAgent.transfer(number);
    },
    /**
     * @private
     */
    _onUnmuteCall: function () {
        this.userAgent.unmuteCall();
    },
});

var transfer_call = function (parent, action) {
    var params = action.params || {};
    core.bus.trigger('transfer_call', params.number);
    return { type: 'ir.actions.act_window_close' };
};

core.action_registry.add("transfer_call", transfer_call);
var VoipTopButton = Widget.extend({
    template:'voip.switch_panel_top_button',
    events: {
        "click": "_onToggleDisplay",
    },

    // TODO remove and replace with session_info mechanism
    willStart: function () {
        var ready = this.getSession().user_has_group('base.group_user').then(
            function (is_employee) {
                if (!is_employee) {
                    return $.Deferred().reject();
                }
            });
        return $.when(this._super.apply(this, arguments), ready);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param  {MouseEvent} ev
     */
    _onToggleDisplay: function (ev) {
        ev.preventDefault();
        core.bus.trigger('voip_onToggleDisplay');
    },
});

// Insert the Voip widget button in the systray menu
SystrayMenu.Items.push(VoipTopButton);

/**
 * Override of FieldPhone to use the DialingPanel to perform calls on clicks.
 */
var Phone = basic_fields.FieldPhone;
Phone.include({
    events: _.extend({}, Phone.prototype.events, {
        'click': '_onClick',
    }),

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Uses the DialingPanel to perform the call.
     *
     * @private
     * @param {String} phoneNumber
     */
    _call: function (phoneNumber) {
        this.do_notify(_t('Start Calling'), _t('Calling ') + ' ' + phoneNumber);
        var params = {
            resModel: this.model,
            resId: this.res_id,
            number: phoneNumber,
        };
        this.trigger_up('voip_call', params);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when the phone number is clicked.
     *
     * @private
     * @param {MouseEvent} e
     */
    _onClick: function (e) {
        if (this.mode === 'readonly') {
            var pbxConfiguration;
            this.trigger_up('get_pbx_configuration', {
                callback: function (output) {
                    pbxConfiguration = output.pbxConfiguration;
                },
            });
            if (
                pbxConfiguration.mode !== "prod" ||
                (
                    pbxConfiguration.pbx_ip &&
                    pbxConfiguration.wsServer &&
                    pbxConfiguration.login &&
                    pbxConfiguration.password
                )
            ) {
                e.preventDefault();
                var phoneNumber = this.value;
                this._call(phoneNumber);
            }
        }
    },
});

WebClient.include({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    show_application: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.dialingPanel = new DialingPanel(self);
            self.dialingPanel.appendTo(self.$el);
            self.on('voip_call', self, self.proxy('_onVoipCall'));
            self.on('voip_activity_call', self, self.proxy('_onVoipActivityCall'));
            self.on('get_pbx_configuration', self, self.proxy('_onGetPbxConfiguration'));
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} event
     */
    _onVoipActivityCall: function (event) {
        this.dialingPanel.callFromActivityWidget(event.data);
    },
    /**
     * @private
     * @param {MouseEvent} event
     */
    _onVoipCall: function (event) {
        this.dialingPanel.callFromPhoneWidget(event.data);
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onGetPbxConfiguration: function (event) {
        event.data.callback({ pbxConfiguration: this.dialingPanel.getPbxConfiguration() });
    },
});

return {
    voipTopButton: new VoipTopButton(),
};

});
