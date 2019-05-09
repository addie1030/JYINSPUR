odoo.define('web_mobile.FormRenderer', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');

var ContactSync = require('web_mobile.ContactSync');

/**
 * Include the FormRenderer to instanciate widget ContactSync.
 * The method will be automatically called to replace the tag <contactsync>.
 */
FormRenderer.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _renderTagContactsync: function () {
        var widget = new ContactSync(this, {
            res_id: this.state.res_id,
            res_model: this.state.model,
        });
        widget.appendTo($('<div>'));
        return widget.$el;
    },
});

});
