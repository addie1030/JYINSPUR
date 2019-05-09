odoo.define('combined_statements_inside_credit_debit_tree_btn', function (require) {
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
	 * 内部债权债务表创建数据
	 */
	function execute_open_action() {
		let build_data = function () {
			let organization = $("#organization_option").val()
			let period = $("#period").val()
			new Model('ps.combined.statements.inside.credit.debt').call('build_inside_credit_debit', [organization, period]).then(function (result) {
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
					$content: $(QWeb.render('InsideCreditDebtInfo', {widget: this, data: result}))
				}).open();
			}
		});
	}

	/**
	 * 内部债权债务表期初结转
	 */
	function carry_open_action(){
		let carry_data = function () {
			let organization = $("#organization_option").val();
			let period = $("#period").val();
			let carry_period = $("#carry_period").val();
			let is_all = $('#is_all').is(":checked");
			new Model('ps.combined.statements.inside.credit.debt').call('carry_inside_credit_debit', [organization, period, carry_period, is_all]).then(function (result) {
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
					title: "结转期初",
					size: 'medium',
					buttons: [
						{
							text: _t("Save"),
							classes: 'btn-primary',
							close: true,
							click: carry_data
						}, {
							text: _t("Cancel"),
							close: true
						}
					],
					$content: $(QWeb.render('InsideCreditDebtCarryInfo', {widget: this, data: result}))
				}).open();
			}
		});
	}


	/**
	 * 内部债权债务表对账
	 */
	function check_open_action() {
		let check_data = function () {
			let organization = $("#organization_option").val();
			let period = $("#period").val();
			new Model('ps.combined.statements.inside.credit.debt').call('check_inside_credit_debit', [organization, period]).then(function (result) {
				if (result) {
					new Dialog(this, {
						title: "对账结果",
						size: 'medium',
						buttons: [
							{
								text: "确认",
								classes: 'btn-primary',
								close: true,
							}, {
								text: _t("Cancel"),
								close: true
							}
						],
						$content: $(QWeb.render('InsideCreditDebtCheckInfo', {widget: this, data: result}))
					}).open();

				}
			});

		};

		new Model("ps.combined.statements.organization").query(['name', 'code']).filter([['is_entity_company', '=', false]]).all().then(function (result) {
			if (result) {
				new Dialog(this, {
					title: "结转期初",
					size: 'medium',
					buttons: [
						{
							text: _t("Save"),
							classes: 'btn-primary',
							close: true,
							click: check_data
						}, {
							text: _t("Cancel"),
							close: true
						}
					],
					$content: $(QWeb.render('InsideCreditDebtInfo', {widget: this, data: result}))
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
				this.$buttons.on('click', '.o_list_inside_credit_debit', execute_open_action.bind(this));
				this.$buttons.on('click', '.o_list_inside_credit_debit_carry', carry_open_action.bind(this));
				this.$buttons.on('click', '.o_list_inside_credit_debit_check', check_open_action.bind(this));
			}
		}
	});

});