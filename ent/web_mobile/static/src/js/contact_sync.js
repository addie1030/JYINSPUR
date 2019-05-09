odoo.define('web_mobile.ContactSync', function (require) {
"use strict";

var Widget = require('web.Widget');

var mobile = require('web_mobile.rpc');

var ContactSync = Widget.extend({
    template: 'ContactSync',
    events: {
        'click': '_onClick',
    },
    /**
     * @constructor
     */
    init: function (parent, params) {
        this.res_id = params.res_id;
        this.res_model = params.res_model;
        this.is_mobile = mobile.methods.addContact;
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onClick: function () {
        var fieldNames = [
            'name', 'image', 'parent_id', 'phone', 'mobile', 'email',
            'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
            'website', 'function', 'title',
        ];
        this._rpc({
            model: this.res_model,
            method: 'read',
            args: [this.res_id, fieldNames],
        }).then(function (r) {
            mobile.methods.addContact(r[0]);
        });
    },
});

return ContactSync;

});
