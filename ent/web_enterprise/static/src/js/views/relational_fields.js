odoo.define('web_enterprise.relational_fields', function (require) {
"use strict";

/**
 * In this file, we override some relational fields to improve the UX in mobile.
 */

var config = require('web.config');
var core = require('web.core');
var relational_fields = require('web.relational_fields');

var FieldStatus = relational_fields.FieldStatus;
var qweb = core.qweb;

var _t = core._t;

FieldStatus.include({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _render: function () {
        if (config.device.isMobile) {
            this.$el.html(qweb.render("FieldStatus.content.mobile", {
                selection: this.status_information,
                status: _.findWhere(this.status_information, {selected: true}),
                clickable: this.isClickable,
            }));
        } else {
            return this._super.apply(this, arguments);
        }
    },
});

});
