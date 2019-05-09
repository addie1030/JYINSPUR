odoo.define('mail_enterprise.ThreadField', function (require) {
"use strict";

var ThreadField = require('mail.ThreadField');

ThreadField.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
    * Override the thread rendering to warn the FormRenderer about attachments.
    * This is used by the FormRenderer to display an attachment preview.
    *
    * @override
    * @private
    */
    _fetchAndRenderThread: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            if (self._threadWidget.attachments.length) {
                self.trigger_up('preview_attachment');
            }
        });
    },
});

});
