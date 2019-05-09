odoo.define('ps_account.account_china_report', function(require) {
	'use strict'

	var core = require('web.core');
	var account_report = require('account_reports.account_report');

	var _t = core._t;

	var account_china_report = account_report.extend({
		events: {
			'click tbody tr': '_onRowLinkClicked',
		},
		init: function(parent, action) {
			console.log(action)
			this._super.apply(this, arguments)
		},
		parse_reports_informations: function(values) {
			return this._super(values);
		},
		_onRowLinkClicked: function(event){
			var self=this;
            if(self.report_model=="account.china.tri.ledger.report"){
			    var date=$(event.currentTarget).children(":first").children(":first").html();
                var name=$(event.currentTarget).children().eq(1).children(":first").html();
                if(name){
                	self._rpc({
                        model: 'account.china.tri.ledger.report',
                        method: 'tri_ledger_link',
                        args: [date, name]
					}).then(function(result){
						self.do_action(result)
					})
				}
            }
            if(self.report_model=="account.china.general.ledger.report"){
                var date=$(event.currentTarget).children(":first").html();
                var text=$(event.currentTarget).parents()[2].children[0].innerHTML;
                var code = text.replace(/[^0-9]/ig,"");
                date = date.replace(/[^0-9]/ig,"");
                var name=$(event.currentTarget).children().eq(2).children(":first").html();
                if(name){
                	self._rpc({
						model: 'account.china.general.ledger.report',
						method: 'get_lines_link',
						args: [date]
					}).then(function(res){
						self.do_action({
							name: _t('Account ledger'),
							type: 'ir.actions.client',
							tag: 'account_china_report',
							context: {'model': 'account.china.tri.ledger.report'},
							ignore_session: "both",
							options: {"date": {"date_from": res[0],"date_to": res[1]},"subject": {"subject_from": code, "subject_to": code}}
						})
					})
				}
            }
		},
		render_searchview_buttons: function () {
			var self = this;
			_.each(
				this.$searchview_buttons.find('.js_account_china_report_account_state_filter'),
				function(k) {
					$(k).toggleClass(
						'selected',
						_.filter(self.report_options[$(k).data('filter')], function(el) {
							return '' + el.id == '' + $(k).data('id') && el.selected === true
						}).length > 0
					)
				}
			)
			this.$searchview_buttons
				.find('.js_account_china_report_style_filter')
				.click(function(event) {
                    this.style.background = "#00A09D";
                    this.style.color = "#FFFFFF";
					var option_value = $(this).data('filter')
					self.report_options.style.filter = option_value
					self.reload()
				})
			this.$searchview_buttons
				.find('.js_account_china_report_auxiliary_filter')
				.click(function(event) {
					var option_value = $(this).data('filter')
					self.report_options.auxiliary.filter = option_value
					self.reload();
				})
			this.$searchview_buttons
				.find('.js_account_china_report_account_state_filter')
				.click(function(event) {
					var option_value = $(this).data('filter')
					var option_id = $(this).data('id')
					_.filter(self.report_options[option_value], function(el) {
						if ('' + el.id == '' + option_id) {
							if (el.selected === undefined || el.selected === null) {
								el.selected = false
							}
							el.selected = !el.selected
						}
						return el
					})
					self.reload()
				})
			if(self.report_options.subject) {
                this.$searchview_buttons
                    .find('.js_account_china_reports_subject')
                    .select2()
                if (self.report_options.subject.subject_from && self.report_options.subject.subject_to) {
                    self.$searchview_buttons
                        .find('[data-filter="subject_from"]')
                        .select2('val', self.report_options.subject.subject_from)
                    self.$searchview_buttons
                        .find('[data-filter="subject_to"]')
                        .select2('val', self.report_options.subject.subject_to)
                }
                this.$searchview_buttons
                    .find('.js_account_china_report_subject_filter')
                    .click(function (event) {
                        self.report_options.subject.subject_from = self.$searchview_buttons
                            .find('[data-filter="subject_from"]')
                            .val()
                        self.report_options.subject.subject_to = self.$searchview_buttons
                            .find('[data-filter="subject_to"]')
                            .val()
                        return self.reload()

                    })
            }

			if(self.report_options.partner){
				this.$searchview_buttons
				.find('.js_account_china_reports_partner')
				.select2()
				if (self.report_options.partner.partner_from ) {
					self.$searchview_buttons
						.find('[data-filter="partner_from"]')
						.select2('val', self.report_options.partner.partner_from)
				}
				this.$searchview_buttons
					.find('.js_account_china_report_partner_filter')
					.click(function(event) {
						self.report_options.partner.partner_from = self.$searchview_buttons
							.find('[data-filter="partner_from"]')
							.val()
						return self.reload()
					})
			}

			if(self.report_options.unit){
				this.$searchview_buttons
				.find('.js_account_china_reports_unit')
				.select2()
				if (self.report_options.unit.unit_from && self.report_options.unit.unit_to) {
					self.$searchview_buttons
						.find('[data-filter="unit_from"]')
						.select2('val', self.report_options.unit.unit_from)
					self.$searchview_buttons
						.find('[data-filter="unit_to"]')
						.select2('val', self.report_options.unit.unit_to)
				}
				this.$searchview_buttons
					.find('.js_account_china_report_unit_filter')
					.click(function(event) {
						self.report_options.unit.unit_from = self.$searchview_buttons
							.find('[data-filter="unit_from"]')
							.val()
						self.report_options.unit.unit_to = self.$searchview_buttons
							.find('[data-filter="unit_to"]')
							.val()
						return self.reload()
					})
			}

			return this._super()
        }
	})

	core.action_registry.add('account_china_report', account_china_report)
	return account_china_report
})
