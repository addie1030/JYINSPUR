odoo.define('accountReportsFollowup.FollowupFormModel', function (require) {
"use strict";

var FollowupFormModel = require('accountReports.FollowupFormModel');
var session = require('web.session');

FollowupFormModel.include({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Save the fact that the user has execute a manual action for this record.
     *
     * @param {string} handle Local resource id of a record
     */
    doManualAction: function (handle) {
        var level = this.localData[handle].data.followup_level;
        if (level && level.manual_action) {
            level.manual_action_done = true;
        }
    },
    /**
     * Save the fact that the user has print a letter for this record.
     *
     * @param {string} handle Local resource id of a record
     */
    doPrintLetter: function (handle) {
        var level = this.localData[handle].data.followup_level;
        if (level && level.print_letter) {
            level.print_letter = false;
        }
    },
   /**
    * Save the fact that the user has send a mail for this record.
    *
    * @param {string} handle Local resource id of a record
    */
    doSendMail: function (handle) {
        var level = this.localData[handle].data.followup_level;
        if (level && level.send_email) {
            level.send_email = false;
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Fetch the html of the followup.
     *
     * @override
     * @private
     */
    _fetch: function (id) {
        var self = this;
        var params = {};
        if (this.localData[id].data.report_manager_id !== undefined) {
            params.keep_summary = true;
        }
        return this._rpc({
            model: 'account.followup.report',
            method: 'get_followup_informations',
            args: [this.localData[id].res_id, params],
            kwargs: {context: session.user_context},
        }).then(function (data) {
            self.localData[id].data.report_manager_id = data.report_manager_id;
            self.localData[id].data.followup_html = data.html;
            if (!params.keep_summary) {
                self.localData[id].data.followup_level = data.followup_level;
                if (!data.followup_level) {
                    self.localData[id].data.followup_level = {};
                }
            }
            if (data.next_action) {
                self.localData[id].data.next_action = data.next_action.type;
                self.localData[id].data.next_action_date = data.next_action.date;
                self.localData[id].data.next_action_date_auto = data.next_action.date_auto;
            }
            return self.localData[id].id;
        });
    },
});
});
