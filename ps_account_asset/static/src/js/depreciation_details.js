odoo.define('ps_account_asset.depreciation_details_report', function(require) {
	'use strict'

	var core = require('web.core');
	var account_report = require('account_reports.account_report');
	var _t = core._t;

	var depreciation_details_report = account_report.extend({
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
		render_searchview_buttons: function () {
			var self = this;
			if(self.report_options.account_analytic){
				this.$searchview_buttons
				.find('.js_account_asset_account_analytic')
				.select2()
				if (self.report_options.account_analytic.account_analytic_from) {
					self.$searchview_buttons
						.find('[data-filter="account_analytic_from"]')
						.select2('val', self.report_options.account_analytic.account_analytic_from)
				}
				this.$searchview_buttons
					.find('.js_account_asset_account_analytic_filter')
					.click(function(event) {
						console.log(self.$searchview_buttons.find('[data-filter="account_analytic_from"]'))
						self.report_options.account_analytic.account_analytic_from = self.$searchview_buttons
							.find('[data-filter="account_analytic_from"]')
							.val()
						return self.reload()
					})
			}
			console.log(self.report_options)

			if(self.report_options.asset_type){
				this.$searchview_buttons
				.find('.js_asset_type')
				.select2()
				if (self.report_options.asset_type.asset_type_from) {
					self.$searchview_buttons
						.find('[data-filter="asset_type_from"]')
						.select2('val', self.report_options.asset_type.asset_type_from)
				}
				this.$searchview_buttons
					.find('.js_asset_type_filter')
					.click(function(event) {
						self.report_options.asset_type.asset_type_from = self.$searchview_buttons
							.find('[data-filter="asset_type_from"]')
							.val()
						return self.reload()
					})
			}

			return this._super()
        }
	})

	core.action_registry.add('depreciation_details_report', depreciation_details_report)
	return depreciation_details_report
})