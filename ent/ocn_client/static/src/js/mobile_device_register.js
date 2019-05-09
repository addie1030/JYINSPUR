odoo.define('mail_push.fcm', function (require) {
"use strict";

var mobile = require('web_mobile.rpc');
var ajax = require('web.ajax');

//Send info only if client is mobile
if (mobile.methods.getFCMKey) {
    var sessionInfo = odoo.session_info;
    if (sessionInfo.fcm_project_id) {
        mobile.methods.getFCMKey({
            project_id: sessionInfo.fcm_project_id,
            inbox_action: sessionInfo.inbox_action,
        }).then(function (response) {
            if (response.success) {
                ajax.rpc('/web/dataset/call_kw/res.config.settings/register_device', {
                    model: 'res.config.settings',
                    method: 'register_device',
                    args: [response.data.subscription_id, response.data.device_name],
                    kwargs: {},
                });
            }
        });
    }
}

if (mobile.methods.hashChange) {
    var currentHash;
    $(window).bind('hashchange', function (event) {
        var hash = event.getState();
        if (!_.isEqual(currentHash, hash)) {
            mobile.methods.hashChange(hash);
        }
        currentHash = hash;
    });
}

});
