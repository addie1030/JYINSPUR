odoo.define('ps_account_center_reports.ps_account_center_report', function(require) {
	'use strict'

	var core = require('web.core');
	var account_report = require('account_reports.account_report');

	var _t = core._t;

	var ps_account_center_report = account_report.extend({
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		renderButtons: function() {
			var self = this
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
	})
	core.action_registry.add('ps_account_center_report', ps_account_center_report)
	return ps_account_center_report
})
