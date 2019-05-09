odoo.define('web_enterprise.ControlPanel', function (require) {
"use strict";

var config = require('web.config');
var ControlPanel = require('web.ControlPanel');

ControlPanel.include({
    _render_breadcrumbs_li: function (bc, index, length) {
        var $bc = this._super.apply(this, arguments);

        var is_last = (index === length-1);
        var is_before_last = (index === length-2);

        $bc.toggleClass('d-none d-md-inline-block', !is_last && !is_before_last)
           .toggleClass('o_back_button', is_before_last)
           .toggleClass('btn btn-secondary', is_before_last && config.device.isMobile);

        return $bc;
    },
    _update_search_view: function(searchview, is_hidden) {
        this._super.apply(this, arguments);

        if (config.device.isMobile) {
            this.$el.addClass('o_breadcrumb_full');
        }
    },
});

return ControlPanel;

});
