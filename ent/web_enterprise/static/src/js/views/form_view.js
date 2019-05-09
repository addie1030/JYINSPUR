odoo.define('web_enterprise.FormView', function (require) {
"use strict";

/**
 * The purpose of this file is to make the FormView use a special FormRenderer
 * in mobile, implementing some tweaks to improve the UX in mobile.
 */

var config = require('web.config');
var FormView = require('web.FormView');
var MobileFormRenderer = require('web_enterprise.MobileFormRenderer');

if (!config.device.isMobile) {
    return;
}

FormView.include({
    config: _.extend({}, FormView.prototype.config, {
        Renderer: MobileFormRenderer,
    }),
});

});
