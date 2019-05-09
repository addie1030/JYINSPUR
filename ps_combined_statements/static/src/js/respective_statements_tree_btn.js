odoo.define('respective_statements_tree_btn', function(require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	var session = require('web.session');
	var ajax = require("web.ajax");
	var Dialog = require('web.Dialog');

	var QWeb = core.qweb;
	var _t = core._t;

	/**
	 * 打开报表
	 */
	function execute_open_action() {

		// 获取当前界面选择的所有行
		let checked_ids = this.sidebar.getParent().get_selected_ids();

		if (checked_ids === undefined || checked_ids.length === 0) {
			Dialog.alert(this, "请选择要打开的记录。");
			return;
		} else if (checked_ids.length > 1) {
			Dialog.alert(this, "打开功能只能选择一条记录。");
			return;
		} else if (checked_ids.length !== 1) {
			Dialog.alert(this, "不可预期的错误，请刷新界面重试。");
			return;
		}

		let ctx = session.user_context;
		ctx['active_ids'] = checked_ids;

		// 获取选择的数据
		let record = this.records.get(checked_ids[0]);

		this.do_action({
			type: 'ir.actions.client',
			tag: 'check.respective.statements',
			context: {
				'repective': record.get('id'),
				'org_name': record.get('app_company')[1],
				'org_code': record.get('app_company_code'),
				'unit': null,
				'project_id': record.get('project_id'),
				'app_company': record.get('app_company')[0],
				'app_user': record.get('app_user')[1],
				'period': record.get('period')
			}
		}, {
			on_reverse_breadcrumb: function() {
				return this.reload();
			}
		});
	}

	/**
	 * Extend the render_buttons function of ListView by adding an event listener
	 * on the import button.
	 * @return {jQuery} the rendered buttons
	 */
	ListView.include({
		render_buttons: function() {
			let add_button = false;
			if (!this.$buttons) {
				add_button = true;
			}
			this._super.apply(this, arguments);
			if (add_button) {
				this.$buttons.on('click', '.o_list_respective_button_open', execute_open_action.bind(this));    // 打开报表
			}
		}
	});

});