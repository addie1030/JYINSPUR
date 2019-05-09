odoo.define('account_batch_payment.reconciliation', function (require) {
"use strict";

var ReconciliationClientAction = require('account.ReconciliationClientAction');
var ReconciliationModel = require('account.ReconciliationModel');
var ReconciliationRenderer = require('account.ReconciliationRenderer');
var core = require('web.core');

var _t = core._t;
var QWeb = core.qweb;

//--------------------------------------------------------------------------

var Action = {
    custom_events: _.defaults({
        select_batch: '_onAction',
    }, ReconciliationClientAction.StatementAction.prototype.custom_events),
};

ReconciliationClientAction.StatementAction.include(Action);
ReconciliationClientAction.ManualAction.include(Action);

//--------------------------------------------------------------------------

var Model = {
    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.batchPayments = [];
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     *
     * @param {Object} context
     * @param {number[]} context.statement_ids
     * @returns {Deferred}
     */
    load: function (context) {
        var self = this;
        return this._super(context).then(function () {
            self.batchPayments = self.statement && self.statement.batch_payments || [];
        });
    },
    /**
     *
     * @param {string} handle
     * @param {number} batchId
     * @returns {Deferred}
     */
    selectBatch: function(handle, batchId) {
        return this._rpc({
                model: 'account.reconciliation.widget',
                method: 'get_move_lines_by_batch_payment',
                args: [this.getLine(handle).id, batchId],
            })
            .then(this._addSelectedBatchLines.bind(this, handle, batchId));
    },

    /**
     * @override
     *
     * @param {(string|string[])} handle
     * @returns {Deferred<Object>} resolved with an object who contains
     *   'handles' key
     */
    validate: function (handle) {
        var self = this;
        return this._super(handle).then(function (data) {
            if (_.any(data.handles, function (handle) {
                    return !!self.getLine(handle).batch_payment_id;
                })) {
                return self._updateBatchPayments().then(function () {
                    return data;
                });
            }
            return data;
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     *
     * @private
     * @param {Object}
     * @returns {Deferred}
     */
    _computeLine: function (line) {
        if (line.st_line.partner_id) {
            line.relevant_payments = [];
        } else {
            // Batch Payments can only be used when there is no partner selected
            line.relevant_payments = this.batchPayments;
        }
        return this._super.apply(this, arguments);
    },
    /**
     *
     * @private
     * @param {string} handle
     * @param {number} batchId
     * @returns {Deferred}
     */
    _addSelectedBatchLines: function (handle, batchId, batchLines) {
        var line = this.getLine(handle);
        // Check if some lines are already selected in another reconciliation
        var selectedIds = [];
        for (var hand in this.lines) {
            if (handle === hand) {
                continue;
            }
            var rec = this.lines[hand].reconciliation_proposition || [];
            for (var k in rec) {
                if (!isNaN(rec[k].id)) {
                    selectedIds.push(rec[k].id);
                }
            }
        }
        selectedIds = _.filter(batchLines, function (batch_line) {
            return selectedIds.indexOf(batch_line.id) !== -1;
        });
        if (selectedIds.length > 0) {
            var message = _t("Some journal items from the selected batch payment are already selected in another reconciliation : ");
            message += _.map(selectedIds, function(l) { return l.name; }).join(', ');
            this.do_warn(_t("Incorrect Operation"), message, true);
            return;
        }

        // remove double
        if (line.reconciliation_proposition) {
            batchLines = _.filter(batchLines, function (batch_line) {
                return !_.any(line.reconciliation_proposition, function (prop) {
                    return prop.id === batch_line.id;
                });
            });
        }

        // add batch lines as proposition
        this._formatLineProposition(line, batchLines);
        for (var k in batchLines) {
            this._addProposition(line, batchLines[k]);
        }
        line.batch_payment_id = batchId;
        return $.when(this._computeLine(line), this._performMoveLine(handle));
    },
    /**
     * load data from
     * - 'account.bank.statement' fetch the batch payments data
     *
     * @param {number[]} statement_ids
     * @returns {Deferred}
     */
    _updateBatchPayments: function(statement_ids) {
        var self = this;
        return this._rpc({
                model: 'account.reconciliation.widget',
                method: 'get_batch_payments_data',
                args: [statement_ids],
            })
            .then(function (data) {
                self.batchPayments = data;
            });
    },
};

ReconciliationModel.StatementModel.include(Model);
ReconciliationModel.ManualModel.include(Model);

//--------------------------------------------------------------------------

var Renderer = {
    events: _.defaults({
        "click .batch_payment": "_onBatch",
    }, ReconciliationRenderer.LineRenderer.prototype.events),

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     *
     * @param {object} state - statement line
     */
    update: function (state) {
        this._super(state);
        this.$(".match_controls .batch_payments_selector").remove();
        if (state.relevant_payments.length) {
            this.$(".match_controls .filter").after(QWeb.render("batch_payments_selector", {
                batchPayments: state.relevant_payments,
            }));
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     *
     * @param {MouseEvent} event
     */
    _onBatch: function(e) {
        e.preventDefault();
        var batchId = parseInt(e.currentTarget.dataset.batch_payment_id);
        this.trigger_up('select_batch', {'data': batchId});
    },
};

ReconciliationRenderer.LineRenderer.include(Renderer);
ReconciliationRenderer.ManualLineRenderer.include(Renderer);

});
