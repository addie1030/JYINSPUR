odoo.define('documents.systray.ActivityMenu', function (require) {
"use strict";

var ActivityMenu = require('mail.systray.ActivityMenu');

ActivityMenu.include({
    events: _.extend({}, ActivityMenu.prototype.events, {
        'click .o_sys_documents_request': '_onRequestDocument',
    }),

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {MouseEvent} ev
     */
   _onRequestDocument: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this.do_action('documents.action_request_form');
    },
});
});
