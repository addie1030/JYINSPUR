odoo.define('web_mobile.relational_fields', function (require) {
"use strict";

var relational_fields = require('web.relational_fields');

var mobile = require('web_mobile.rpc');

/**
 * Override the Many2One to open a dialog in mobile.
 */

relational_fields.FieldMany2One.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Don't bind autocomplete in the mobile app as it uses a different mechanism
     * see @_invokeMobileDialog
     *
     * @private
     * @override
     */
    _bindAutoComplete: function () {
        if (mobile.methods.many2oneDialog) {
            return;
        }
        return this._super.apply(this, arguments);
    },
    /**
     * @private
     */
    _invokeMobileDialog: function (term) {
        var self = this;
        this._search(term).done(function (result) {
            self._callback_actions = {};

            _.each(result, function (r, i) {
                if (!r.hasOwnProperty('id')) {
                    self._callback_actions[i] = r.action;
                    result[i].action_id = i;
                }
            });
            mobile.methods.many2oneDialog({'records': result, 'label': self.string})
                .then(function (response) {
                    if (response.data.action === 'search') {
                        self._invokeMobileDialog(response.data.term);
                    }
                    if (response.data.action === 'select') {
                        self._setValue({id: response.data.value.id});
                    }
                    if (response.data.action === 'action') {
                        self._callback_actions[response.data.value.action_id]();
                    }
                });
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * We always open ManyToOne native dialog for select/update field value
     *
     * @override
     * @private
     */
    _onInputClick: function () {
        if (mobile.methods.many2oneDialog) {
            return this._invokeMobileDialog('');
        }
        this._super.apply(this, arguments);
    },
});

});
