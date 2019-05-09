odoo.define('website_crm_score.set_score', function (require) {
"use strict";

var CustomizeMenu = require('website.customizeMenu');
var rpc = require('web.rpc');
var Widget = require('web.Widget');

var TrackPage = Widget.extend({
    template: 'website_crm_score.track_page',
    xmlDependencies: ['/website_crm_score/static/src/xml/track_page.xml'],
    events: {
        'change #switch-track-page': '_onTrackChange',
    },
    track: null,
    start: function () {
        var self = this;
        this.$input = this.$('#switch-track-page');
        this._is_tracked().then(function (data) {
            if (data[0]['track']) {
                self.track = true;
                self.$input.attr('checked','checked');
            } else {
                self.track = false;
            }
        });
    },
    _is_tracked: function (val) {
        var viewid = $('html').data('viewid');
        if (!viewid) {
            return $.Deferred().reject();
        } else {
            return rpc.query({
                model: 'ir.ui.view',
                method: 'read',
                args: [[viewid], ['track']],
            });
        }
    },
    _onTrackChange: function (ev) {
        var checkbox_value = this.$input.is(':checked');
        if (checkbox_value !== this.track) {
            this.track = checkbox_value;
            this._trackPage(checkbox_value);
        }
    },
    _trackPage: function (val) {
        var viewid = $('html').data('viewid');
        if (!viewid) {
            return $.Deferred().reject();
        } else {
            return rpc.query({
                model: 'ir.ui.view',
                method: 'write',
                args: [[viewid], {track: val}],
            });
        }
    },
});

CustomizeMenu.include({
    _loadCustomizeOptions: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        return def.then(function () {
            if (!self.__trackpageLoaded) {
                self.__trackpageLoaded = true;
                self.trackPage = new TrackPage(self);
                self.trackPage.appendTo(self.$el.children('.dropdown-menu'));
            }
        });
    },
});

});
