odoo.define('ps_account_asset.asset_analysis_report', function(require) {
	'use strict'

	var core = require('web.core');
	var account_report = require('account_reports.account_report');
	var _t = core._t;

	var asset_analysis_report = account_report.extend({
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
		render_searchview_buttons: function () {
			var self = this;
			console.log(self.report_options)
			console.log(11111111)
			if(self.report_options.analytic_increase_style){
				this.$searchview_buttons
				.find('.js_analytic_increase_style')
				.select2()
				if (self.report_options.analytic_increase_style.analytic_increase_style_para) {
					self.$searchview_buttons
						.find('[data-filter="analytic_increase_style_para"]')
						.select2('val', self.report_options.analytic_increase_style.analytic_increase_style_para)
				}
				this.$searchview_buttons
					.find('.js_analytic_increase_style_filter')
					.click(function(event) {
						console.log(3333333)
						console.log(self.$searchview_buttons.find('[data-filter="analytic_increase_style_para"]'))
						self.report_options.analytic_increase_style.analytic_increase_style_para = self.$searchview_buttons
							.find('[data-filter="analytic_increase_style_para"]')
							.val()
						return self.reload()
					})
			}
			// console.log(self.report_options)
			//
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

	core.action_registry.add('asset_analysis_report', asset_analysis_report)
	return asset_analysis_report
})