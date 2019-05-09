odoo.define('accountReportsFollowup.FollowupFormController', function (require) {
"use strict";

var core = require('web.core');
var FollowupFormController = require('accountReports.FollowupFormController');

var QWeb = core.qweb;

FollowupFormController.include({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    renderButtons: function ($node) {
        this.$buttons = $(QWeb.render("CustomerStatements.buttonsWithLevels", {
            widget: this,
            action_name: this.model.get(this.handle).data.followup_level.manual_action_note
        }));
        this.$buttons.on('click', '.o_account_reports_followup_print_letter_button',
            this._onPrintLetter.bind(this));
        this.$buttons.on('click', '.o_account_reports_followup_send_mail_button',
            this._onSendMail.bind(this));
        this.$buttons.on('click', '.o_account_reports_followup_manual_action_button',
            this._onManualAction.bind(this));
        this.$buttons.on('click', '.o_account_reports_followup_do_it_later_button',
            this._onDoItLater.bind(this));
        this.$buttons.on('click', '.o_account_reports_followup_done_button',
            this._onDone.bind(this));
        this.$buttons.appendTo($node);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     * @private
     */
    _update: function () {
        this._updateButtons();
        return this._super.apply(this, arguments);
    },
    /**
     * Update the buttons according to followup_level.
     *
     * @private
     */
    _updateButtons: function () {
        if (!this.$buttons) {
            return;
        }
        var followupLevel = this.model.get(this.handle).data.followup_level;
        if (followupLevel.print_letter) {
            this.$buttons.find('button.o_account_reports_followup_print_letter_button')
                .removeClass('btn-secondary').addClass('btn-primary');
        } else {
            this.$buttons.find('button.o_account_reports_followup_print_letter_button')
                .removeClass('btn-primary').addClass('btn-secondary');
        }
        if (followupLevel.send_email) {
            this.$buttons.find('button.o_account_reports_followup_send_mail_button')
                .removeClass('btn-secondary').addClass('btn-primary');
        } else {
            this.$buttons.find('button.o_account_reports_followup_send_mail_button')
                .removeClass('btn-primary').addClass('btn-secondary');
        }
        if (followupLevel.manual_action) {
            this.$buttons.find('button.o_account_reports_followup_manual_action_button')
                .html(followupLevel.manual_action_note);
            if (!followupLevel.manual_action_done) {
                this.$buttons.find('button.o_account_reports_followup_manual_action_button')
                    .removeClass('btn-secondary').addClass('btn-primary');
            } else {
                this.$buttons.find('button.o_account_reports_followup_manual_action_button')
                    .removeClass('btn-primary').addClass('btn-secondary');
            }
        } else {
            this.$buttons.find('button.o_account_reports_followup_manual_action_button').hide();
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * When the user click on the manual action button, we need to update it
     * in the backend.
     *
     * @private
     */
    _onManualAction: function () {
        var self = this;
        var partnerID = this.model.get(this.handle).res_id;
        var followupLevel = this.model.get(this.handle).data.followup_level.id;
        var options = {
            partner_id: partnerID
        };
        this.model.doManualAction(this.handle);
        if (followupLevel) {
            options['followup_level'] = followupLevel;
        }
        this._rpc({
            model: 'account.followup.report',
            method: 'do_manual_action',
            args: [options]
        })
        .then(function () {
            self.renderer.chatter.trigger_up('reload_mail_fields', {
                activity: true,
                thread: true,
                followers: true
            });
            self._displayDone();
        });
    },
    /**
     * Print the customer statement.
     *
     * @private
     */
    _onPrintLetter: function () {
        this.model.doPrintLetter(this.handle);
        this._super.apply(this, arguments);
    },
    /**
     * Send the mail server-side.
     *
     * @private
     */
    _onSendMail: function () {
        this.model.doSendMail(this.handle);
        this._super.apply(this, arguments);
    },
});
});