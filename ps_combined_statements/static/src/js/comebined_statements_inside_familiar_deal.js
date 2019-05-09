odoo.define('combined_statements_inside_familiar_deal_tree_btn', function (require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	var Model = require('web.Model');
	var session = require('web.session');
	var ajax = require("web.ajax");
	var Dialog = require('web.Dialog');

	var QWeb = core.qweb;
	var _t = core._t;

	/**
	 * 常见内部交易创建数据创建数据
	 */
	function execute_open_action() {
		let build_data = function () {
			let organization = $("#organization_option").val()
			let period = $("#period").val()
			new Model('ps.combined.statements.inside.familiar.deal').call('build_inside_familiar_deal', [organization, period]).then(function (result) {
				if (result) {
					new Dialog.confirm(this, result.message, {
						'title': _t("information")
					});
				}
			});

		};

		new Model("ps.combined.statements.organization").query(['name', 'code']).filter([['is_entity_company', '=', true]]).all().then(function (result) {
			if (result) {
				new Dialog(this, {
					title: "创建数据",
					size: 'medium',
					buttons: [
						{
							text: _t("Save"),
							classes: 'btn-primary',
							close: true,
							click: build_data
						}, {
							text: _t("Cancel"),
							close: true
						}
					],
					$content: $(QWeb.render('InsideFamiliarDealInfo', {widget: this, data: result}))
				}).open();
			}
		});
	}


	/**
	 * Extend the render_buttons function of ListView by adding an event listener
	 * on the import button.
	 * @return {jQuery} the rendered buttons
	 */
	ListView.include({
		render_buttons: function () {
			let add_button = false;
			if (!this.$buttons) {
				add_button = true;
			}
			this._super.apply(this, arguments);
			if (add_button) {
				this.$buttons.on('click', '.o_list_inside_familiar_deal', execute_open_action.bind(this));
			}
		}
	});

});