odoo.define('quality_mrp_iot.iot_picture', function (require) {
"use strict";

var registry = require('web.field_registry');
var MrpWorkorderWidgets = require('mrp_workorder.update_kanban');
var TabletImage = MrpWorkorderWidgets.TabletImage;
var IotValueFieldMixin = require('iot.widgets').IotValueFieldMixin;
var Dialog = require('web.Dialog');
var core = require('web.core');
var _t = core._t;

var TabletImageIot = TabletImage.extend(IotValueFieldMixin, {
    events: _.extend({}, TabletImage.prototype.events, {
        'click .o_input_file': '_onButtonClick',
    }),

    /**
     * @private
     */
    _getDeviceInfo: function() {
        this.test_type = this.record.data.test_type;
        if (this.test_type === 'picture') {
            this.ip = this.record.data.ip;
            this.identifier = this.record.data.identifier;
        }
        return Promise.resolve();
    },

    _onButtonClick: function (ev) {
        ev.stopImmediatePropagation();
        if (this.record.data.ip) {
            ev.preventDefault();
            console.log(this);
            this.do_notify(_t('Capture image...'));
            this.call(
                'iot_longpolling',
                'action',
                this.ip,
                this.identifier,
                '',
                this._onActionSuccess.bind(this),
                this._onActionFail.bind(this)
            );
        }
    },
    /**
     * When the camera change state (after a action that call to take a picture) this function render the picture to the right owner
     *
     * @param {Object} data.owner
     * @param {Object} data.session_id
     * @param {Object} data.message
     * @param {Object} data.image in base64
     */
    _onValueChange: function (data){
        if (data.owner && data.owner === data.session_id) {
            this.do_notify(data.message);
            if (data.image){
                this._setValue(data.image);
            }
        }
    },
    /**
     * After a request to make action on camera and this call don't return true in the result
     * this means that the IoT Box can't connect to camera
     *
     * @param {Object} data.result
     */
    _onActionSuccess: function (data){
        if (!data.result) {
            var $content = $('<p/>').text(_t('Please check if the camera is still connected.'));
            var dialog = new Dialog(this, {
                title: _t('Connection to Camera failed'),
                $content: $content,
            });
            dialog.open();
        }
    },
    /**
     * After a request to make action on camera and this call fail
     * this means that the customer browser can't connect to IoT Box
     */
    _onActionFail: function () {
        var $content = $('<p/>').text(_t('Please check if the IoT Box is still connected.'));
        var dialog = new Dialog(this, {
            title: _t('Connection to IoT Box failed'),
            $content: $content,
        });
        dialog.open();
    },
});

registry.add('iot_picture', TabletImageIot);

return TabletImageIot;
});