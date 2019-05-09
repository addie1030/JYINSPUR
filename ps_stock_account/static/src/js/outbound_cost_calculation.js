odoo.define('stock_outbound_reports.outbound_cost_calculation_report', function(require) {
	'use strict'

	var core = require('web.core');
	var stock_outbound_reports = require('account_reports.account_report');
	var _t = core._t;
	var outbound_cost_calculation_report = stock_outbound_reports.extend({
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
	})
	core.action_registry.add('outbound_cost_calculation_widget', outbound_cost_calculation_report);
	return outbound_cost_calculation_report
});
