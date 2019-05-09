odoo.define('web_enterprise.MobileFormRenderer', function (require) {
"use strict";

/**
 * This file defines the MobileFormRenderer, an extension of the FormRenderer
 * implementing some tweaks to improve the UX in mobile.
 * In mobile, this renderer is used instead of the classical FormRenderer.
 */

var core = require('web.core');
var FormRenderer = require('web.FormRenderer');

var qweb = core.qweb;

var MobileFormRenderer = FormRenderer.extend({
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * In mobile, buttons/widget tag displayed in the statusbar are folded in a dropdown.
     *
     * @override
     * @private
     */
    _renderHeaderButtons: function (node) {
        var $headerButtons = $();
        var self = this;
        var buttons = [];
        _.each(node.children, function (child) {
            if (child.tag === 'button') {
                buttons.push(self._renderHeaderButton(child));
            }
            if (child.tag === 'widget') {
                buttons.push(self._renderTagWidget(child));
            }
        });

        if (buttons.length) {
            $headerButtons = $(qweb.render('StatusbarButtons'));
            var $dropdownMenu = $headerButtons.find('.dropdown-menu');
            _.each(buttons, function ($button) {
                $dropdownMenu.append($button.addClass('dropdown-item'));
            });
        }

        return $headerButtons;
    },
});

return MobileFormRenderer;

});
