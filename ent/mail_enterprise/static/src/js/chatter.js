odoo.define('mail_enterprise.chatter', function (require) {
"use strict";

var Chatter = require('mail.Chatter');

Chatter.include({
    custom_events: _.extend({}, Chatter.prototype.custom_events, {
        preview_attachment: '_onAttachmentPreview',
    }),

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onAttachmentPreview: function (ev) {
        if (this._areAttachmentsLoaded){
            ev.data.attachments = this.attachments;
        } else {
            ev.stopPropagation();
            return this._fetchAttachments().then(this.trigger_up.bind(this, 'preview_attachment'));
        }
    },
});
});
