odoo.define('combined_statements_elimination_entry_tree_btn', function (require) {
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
	 * 抵消分录删除
	 */
	function execute_open_action() {
		let delete_data = function () {
				let organization = $("#organization_option").val();
				let entry_type = $("#entry_type").val();
				let period = $("#period").val()
				new Model('ps.combined.statements.elimination.entry').call('delete_elimination_entry', [organization, entry_type, period]).then(function (result) {
					if (result.status) {
						new Dialog.confirm(this, result.message, {
							'title': '消息'
						});
					}
				});
			};

		new Model("ps.combined.statements.elimination.entry").call('get_delete_data').then(function (result) {
			if (result) {
				new Dialog(this, {
					title: "抵消分录批量删除",
					size: 'medium',
					buttons: [
						{
							text: "确定",
							classes: 'btn-primary',
							close: true,
							click: delete_data
						}, {
							text: "取消",
							close: true
						}
					],
					$content: $(QWeb.render('EliminationEntryInfo', {widget: this, data: result}))
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
				this.$buttons.on('click', '.o_list_elimination_entry', execute_open_action.bind(this));
			}
		}
	});
});