odoo.define('stock_account_china_center_stock_summary_reports.stock_account_china_center_stock_summary_report', function(require) {
	'use strict'

	var core = require('web.core');
	var account_report = require('account_reports.account_report');

	var _t = core._t;

	var stock_account_china_center_stock_summary_report = account_report.extend({
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		// hide the button
		renderButtons: function() {
			var self = this
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
	})
	core.action_registry.add('stock_account_china_center_stock_summary_report', stock_account_china_center_stock_summary_report)
	return stock_account_china_center_stock_summary_report
})
