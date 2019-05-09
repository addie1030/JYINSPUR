odoo.define('voip.onsip', function(require) {
"use strict";

var VoipUserAgent = require('voip.user_agent');

VoipUserAgent.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getUaConfig: function (result) {
        return {
            uri: result.login +'@'+result.pbx_ip,
            wsServers: result.wsServer || null,
            authorizationUser: result.onsip_auth_user,
            password: result.password,
            log: {builtinEnabled: false},
        };
    },
});

});
