odoo.define('web_enterprise.SwitchCompanyMenu', function(require) {
"use strict";

/**
 * In mobile, there is no switch company menu in the systray. Instead, it is
 * available from the Burger menu.
 * The purpose of this file is to remove the SwitchCompanyMenu widget from the
 * SystrayMenu items, before the SystrayMenu starts to instantiates them.
 */

var config = require('web.config');
var SwitchCompanyMenu = require('web.SwitchCompanyMenu');
var SystrayMenu = require('web.SystrayMenu');

if (config.device.isMobile) {
    var index = SystrayMenu.Items.indexOf(SwitchCompanyMenu);
    SystrayMenu.Items.splice(index, 1);
}

});
