odoo.define('voip.dialing_tab', function (require) {
"use strict";

var Phonecall = require('voip.phonecall');
var FieldUtils = require('web.field_utils')
var Widget = require('web.Widget');

var PhonecallTab = Widget.extend({
    template: "voip.DialingTab",
    events:{
    },
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.phonecalls = [];
        this.selectedPhonecall = null;
        this.currentPhonecall = null;
    },
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
    },
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * When the user clicks on the call button and the details are displayed,
     * the first number is called.
     */
    callFirstNumber: function () {
        var number = this.selectedPhonecall.phone || this.selectedPhonecall.mobile;
        if (number) {
            this.currentPhonecall = this.selectedPhonecall;
            this.trigger_up('callNumber', {number: number});
        }
    },
    /**
     * Triggers the hangup process then refreshes the tab.
     */
    hangupPhonecall: function () {
        if (this.currentPhonecall) {
            var self = this;
            this.currentPhonecall.hangup().then(function (){
                self.refreshPhonecallsStatus();
                self.phonecallDetails.hideCallDisplay();
            });
        }
    },
    /**
     * Function overriden by each tab. Called when a phonecall starts.
     */
    initPhonecall: function () {
        this.phonecallDetails.showCallDisplay();
        this.trigger_up('toggleHangupButton');
    },
    /**
     * Called when the call is answered and then no more ringing.
     */
    onCallAccepted: function () {
        this.phonecallDetails.activateInCallButtons();
    },
    /**
     * Called when the user accepts an incoming call.
     *
     * @param {Object} params
     * @param {String} params.number
     * @param {Int} params.partnerId
     */
    onIncomingCallAccepted: function (params) {
        var self = this;
        this._rpc({
            model: 'voip.phonecall',
            method: 'create_from_incoming_call',
            args: [params.number, params.partnerId],
        }).then(function (phonecall) {
            self._displayInQueue(phonecall).then(function (phonecallWidget) {
                self.currentPhonecall = phonecallWidget;
                self._selectCall(phonecallWidget);
                self.phonecallDetails.showCallDisplay();
                self.phonecallDetails.activateInCallButtons();
            });
        });
    },
    /**
     * Performs a rpc to get the phonecalls then call the parsing method.
     *
     * @return {Deferred}
     */
    refreshPhonecallsStatus: function () {
        return this._rpc({model: 'voip.phonecall', method: 'get_next_activities_list'})
            .then(_.bind(this._parsePhonecalls, this));
    },
    /**
     * Called when the current phonecall is rejected by the callee.
     */
    rejectPhonecall: function () {
        if (this.currentPhonecall) {
            var self = this;
            this.currentPhonecall.rejectPhonecall().then(function () {
                self.refreshPhonecallsStatus();
                self.phonecallDetails.hideCallDisplay();
            });
        }
    },
    /**
     * Hides the phonecall that doesn't match the search. Overriden in each tab.
     *
     * @param  {String} search
     */
    searchPhonecall: function (search) {
        return;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Binds the scroll event to the tab.
     *
     * @private
     */
    _bindScroll: function () {
        var self = this;
        this.offset = 0;
        this.lazyLoadFinished = false;
        this.isLazyLoading = false;
        this.$container = this.$el.closest('.tab-content');
        this.$phonecalls = this.$('.o_dial_phonecalls');
        this.$container.scroll(function () {
            if (!self.lazyLoadFinished && self.maxScrollHeight && self.scrollLimit) {
                var position = self.$container.scrollTop();
                if (!self.isLazyLoading && self.maxScrollHeight - position < self.scrollLimit) {
                    self.offset += self.limit;
                    self._lazyLoadPhonecalls();
                }
            }
        });
    },
    /**
     * Computes the scroll limit before triggering the lazy loading of the
     * phonecalls.
     *
     * @private
     */
    _computeScrollLimit: function () {
        var height = this.$el.outerHeight();
        var tabHeight = this.$container.height();
        this.maxScrollHeight =  height - tabHeight;
        if (this.maxScrollHeight > 0) {
            this.scrollLimit = this.maxScrollHeight/3;
        }
    },
    /**
     * Creates a phonecall widget
     *
     * @private
     * @param  {Object} phonecall
     * @return {Widget}
     */
    _createPhonecallWidget: function (phonecall) {
        if (phonecall.call_date) {
            var utcTime = FieldUtils.parse.datetime(phonecall.call_date, false, {isUTC: true});
            phonecall.call_date = utcTime.local().format("YYYY-MM-DD HH:mm:ss");
        }
        var widget = new Phonecall.PhonecallWidget(this, phonecall);
        widget.on("selectCall", this, this._onSelectCall);
        widget.on("removePhonecall", this, this._onRemovePhonecall);
        return widget;
    },
    /**
     * Diplays the phonecall in the tab list.
     *
     * @private
     * @param {Object} phonecall
     * @return {Deferred}
     */
    _displayInQueue: function (phonecall) {
        var widget = this._createPhonecallWidget(phonecall);
        this.phonecalls.push(widget);
        return widget.appendTo(this.$(".o_dial_phonecalls")).then(function () {
            return widget;
        });
    },
    /**
     * Goes through the phonecalls sent by the server and creates
     * a phonecall widget for each.
     *
     * @private
     * @param {Array[Object]} phonecalls
     */
    _parsePhonecalls: function (phonecalls) {
        var self = this;
        _.each(this.phonecalls, function (w) {
            w.destroy();
        });
        this.phonecalls = [];
        var phonecall_displayed = false;
        _.each(phonecalls, function (phonecall) {
            phonecall_displayed = true;
            self._displayInQueue(phonecall);
        });
        //Select again the selected phonecall before the refresh
        var previousSelection = this.selectedPhonecall &&
            _.findWhere(this.phonecalls, {id: this.selectedPhonecall.id});
        if (previousSelection) {
            this._selectCall(previousSelection);
        }
    },
    /**
     * Opens the details of a phonecall widget.
     *
     * @private
     * @param {Widget} phonecall
     */
    _selectCall: function (phonecall) {
        var $el = this.$el;
        if (this.selectedPhonecall) {
            $el = this.phonecallDetails.$el;
        }
        this.phonecallDetails = new Phonecall.PhonecallDetails(this, phonecall);
        this.phonecallDetails.replace($el);
        this.selectedPhonecall = phonecall;
        this.trigger_up('hidePanelHeader');
        this.phonecallDetails.on('closePhonecallDetails', this, function () {
            this.replace(this.phonecallDetails.$el);
            this.selectedPhonecall = false;
            this.trigger_up('showPanelHeader');
            this.refreshPhonecallsStatus();
        });
        this.phonecallDetails.on('clickOnNumber', this, function (ev) {
            this.currentPhonecall = this.selectedPhonecall;
            this.trigger_up('callNumber', {number: ev.data.number});
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Integer} phonecallId
     */
    _onRemovePhonecall: function (phonecallId) {
        var self = this;
        this._rpc({
            model: 'voip.phonecall',
            method: 'remove_from_queue',
            args: [phonecallId],
        }).then(function () {
            self.refreshPhonecallsStatus();
        });
    },
    /**
     * @private
     * @param {Integer} phonecallId
     */
    _onSelectCall: function (phonecall) {
        this._selectCall(phonecall);
    },
});

var ActivitiesTab = PhonecallTab.extend({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    initPhonecall: function () {
        if (this.currentPhonecall.id) {
            this._rpc({
                model: 'voip.phonecall',
                method: 'init_call',
                args: [this.currentPhonecall.id],
            }).then(this._super.bind(this));
        }
    },

    /**
     * Function called when a phonenumber is clicked in the activity widget.
     * If the phonecall with the activityId given in the parameter
     * can't be found in the displayed list, we make a rpc to get the
     * related phonecall.
     *
     * @param {Object} params
     * @param  {String} params.number
     * @param  {Integer} params.activityId
     */
    callFromActivityWidget: function (params) {
        var self = this;
        var def = new $.Deferred();
        this.currentPhonecall = _.find(this.phonecalls, function (phonecall) {
            return phonecall.activity_id === params.activityId;
        });
        if (this.currentPhonecall) {
            this._selectCall(this.currentPhonecall);
            def.resolve();
        } else {
            this._rpc({
                model: 'voip.phonecall',
                method: 'get_from_activity_id',
                args: [params.activityId]
            }).then(function (phonecall) {
                self._displayInQueue(phonecall).then(function (phonecallWidget) {
                    self.currentPhonecall = phonecallWidget;
                    self._selectCall(phonecallWidget);
                    def.resolve();
                });
            });
        }
        return def;
    },
    /**
     * @override
     */
    searchPhonecall: function (search) {
        // regular expression used to do a case insensitive search
        var escSearch = this.escapeRegExp(search)
        var expr = new RegExp(escSearch, 'i');
        // for each phonecall, check if the search is in phonecall name or the partner name
        _.each(this.phonecalls, function (phonecall) {
            var flagPartner = phonecall.partner_name &&
                phonecall.partner_name.search(expr) > -1;
            var flagName = false;
            if (phonecall.name) {
                flagName = phonecall.name.search(expr) > -1;
            }
            phonecall.$el.toggle(flagPartner || flagName);
        });
    },
    /**
     * Escape string in order to use it in a regex
     * source: https://stackoverflow.com/questions/3446170/escape-string-for-use-in-javascript-regex
     * 
     * @param {String} string
     */
    escapeRegExp: function (string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
      }
});

var RecentTab = PhonecallTab.extend({
    /**
     * @override
     */
    start: function () {
        this.limit = 10;
        this._bindScroll();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Creates a new phonecall in the db and in the tab list based on a number.
     *
     * @param  {String} number
     * @return {Deferred}
     */
    callFromNumber: function (number) {
        var self = this;
        var def = new $.Deferred();
        this._rpc({
            model: 'voip.phonecall',
            method: 'create_from_number',
            args: [number],
        }).then(function (phonecall) {
            self._displayInQueue(phonecall).then(function (phonecallWidget) {
                self.currentPhonecall = phonecallWidget;
                self._selectCall(phonecallWidget);
                def.resolve(phonecallWidget);
            });
        });
        return def;
    },
    /**
     * Function called when widget phone is clicked.
     *
     * @param {Object} params
     * @param  {String} params.number
     * @param  {String} params.resModel
     * @param  {Integer} params.resId
     * @return {Deferred}
     */
    callFromPhoneWidget: function (params) {
        var self = this;
        var def = new $.Deferred();
        this._rpc({
            model: 'voip.phonecall',
            method: 'create_from_phone_widget',
            args: [
                params.resModel,
                params.resId,
                params.number,
            ],
        }).then(function (phonecall) {
            self._displayInQueue(phonecall).then(function (phonecallWidget) {
                self.currentPhonecall = phonecallWidget;
                self._selectCall(phonecallWidget);
                def.resolve(phonecallWidget);
            });
        });
        return def;
    },
    /**
     * @override
     *
     * @param {Object} phonecall if given the functiondoesn't have to create a
     *                           new phonecall
     */
    initPhonecall: function (phonecall) {
        var self = this;
        var _super = this._super.bind(this);
        if (!phonecall) {
            this._rpc({
                model: 'voip.phonecall',
                method: 'create_from_recent',
                args: [
                    this.currentPhonecall.id,
                ],
            }).then(function (phonecall) {
                self._displayInQueue(phonecall).then(function (phonecallWidget) {
                    self.currentPhonecall = phonecallWidget;
                    self._selectCall(phonecallWidget);
                    _super();
                });
            });
        } else {
            _super();
        }
    },
    /**
     * @override
     */
    refreshPhonecallsStatus: function () {
        this.lazyLoadFinished = false;
        return this._rpc({
            model: 'voip.phonecall',
            method: 'get_recent_list',
            args: [false, 0, 10],
        }).then(_.bind(this._parsePhonecalls, this));
    },
    /**
     * @override
     */
    searchPhonecall: function (search) {
        if (search) {
            var self = this;
            this.searchExpr = search;
            this.offset = 0;
            this.lazyLoadFinished = false;
            this._rpc({
                model: 'voip.phonecall',
                method: 'get_recent_list',
                args: [search, this.offset, this.limit],
            }).then(function (phonecalls) {
                self._parsePhonecalls(phonecalls);
            });
        } else {
            this.searchExpr = false;
            this.refreshPhonecallsStatus();
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Gets the next phonecalls to display with the current offset
     *
     * @private
     */
    _lazyLoadPhonecalls: function () {
        var self = this;
        this.isLazyLoading = true;
        var search = this.searchExpr ? this.searchExpr : false;
        this._rpc({
            model: 'voip.phonecall',
            method: 'get_recent_list',
            args: [search, this.offset, this.limit],
        }).then(function (phonecalls) {
            if (!phonecalls.length) {
                self.lazyLoadFinished = true;
            }
            var deferreds = [];
            _.each(phonecalls, function (phonecall) {
                deferreds.push(self._displayInQueue(phonecall));
            });
            $.when.apply($, deferreds).then( function () {
                self._computeScrollLimit();
                self.isLazyLoading = false;
            });
        });
    },
    /**
     * @override
     */
    _parsePhonecalls: function (phonecalls) {
        _.map(phonecalls, function (phonecall) {
            phonecall.isRecent = true;
        });
        this._super.apply(this, arguments);
        this._computeScrollLimit();
    },
});

var ContactsTab = PhonecallTab.extend({
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.contacts = [];
    },
    /**
     * @override
     */
    start: function () {
        this.limit = 9;
        this._bindScroll();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    initPhonecall: function () {
        var self = this;
        var _super = this._super.bind(this);
        this._rpc({
            model: 'voip.phonecall',
            method: 'create_from_contact',
            args: [
                this.currentPhonecall.partner_id,
            ],
        }).then(function (phonecall) {
            self.currentPhonecall = self._createPhonecallWidget(phonecall);
            self._selectCall(self.currentPhonecall);
            _super();
        });
    },
    /**
     * @override
     */
    refreshPhonecallsStatus: function () {
        this.offset = 0;
        this.lazyLoadFinished = false;
        return this._rpc({
            model: 'res.partner',
            method: 'search_read',
            fields: ['id', 'display_name', 'phone', 'mobile', 'email', 'image_small'],
            limit: this.limit,
        }).then(_.bind(this._parseContacts, this));
    },
    /**
     * @override
     */
    searchPhonecall: function (search) {
        if (search) {
            var self = this;
            this.searchDomain = [
                '|',
                ['display_name', 'ilike', search],
                ['email', 'ilike', search]
            ];
            this.offset = 0;
            this.lazyLoadFinished = false;
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                domain: this.searchDomain,
                fields: ['id', 'display_name', 'phone', 'mobile', 'email', 'image_small'],
                limit: this.limit,
                offset: this.offset,
            }).then(function (contacts) {
                self._parseContacts(contacts);
            });
        } else {
            this.searchDomain = false;
            this.refreshPhonecallsStatus();
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Since the contact tab is based on res_partner and not voip_phonecall,
     * this method make the convertion between the models.
     *
     * @param  {Array[Object]} contacts
     * @return {Array[Object]}
     */
    _contactToPhonecall: function (contacts) {
        var phonecalls = [];
        _.each(contacts, function (contact) {
            phonecalls.push({
                partner_id: contact.id,
                partner_name: contact.display_name,
                partner_image_small: contact.image_small,
                partner_email: contact.email,
                phone: contact.phone,
                mobile: contact.mobile,
                isContact: true,
            });
        });
        return phonecalls;
    },
    /**
     * Gets the next phonecalls to display with the current offset
     *
     * @private
     */
    _lazyLoadPhonecalls: function () {
        var self = this;
        this.isLazyLoading = true;
        this._rpc({
            model: 'res.partner',
            method: 'search_read',
            domain: this.searchDomain ? this.searchDomain : false,
            fields: ['id', 'display_name', 'phone', 'mobile', 'email', 'image_small'],
            limit: this.limit,
            offset: this.offset
        }).then(function (contacts) {
            if (!contacts.length) {
                self.lazyLoadFinished = true;
            }
            var phonecalls = self._contactToPhonecall(contacts);
            var deferreds = [];
            _.each(phonecalls, function (phonecall) {
                deferreds.push(self._displayInQueue(phonecall));
            });
            $.when.apply($, deferreds).then( function () {
                self._computeScrollLimit();
                self.isLazyLoading = false;
            });
        });
    },
    /**
     * Parses the contacts to convert them and then calls the _parsePhonecalls.
     *
     * @param  {Array[Object]} contacts
     */
    _parseContacts: function (contacts) {
        var phonecalls = this._contactToPhonecall(contacts);
        this._parsePhonecalls(phonecalls);
        this._computeScrollLimit();
    },
});

return {
    ContactsTab: ContactsTab,
    ActivitiesTab: ActivitiesTab,
    RecentTab: RecentTab,
};

});