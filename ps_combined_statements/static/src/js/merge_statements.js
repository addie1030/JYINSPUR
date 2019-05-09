odoo.define('combined_statements.merge_statements', function (require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	// var Widget = require('web.Widget');
	var utils = require('web.utils');
	var web_client = require('web.web_client');
	var session = require('web.session');
	var Dialog = require('web.Dialog');
	// var Model = require('web.Model');

	// Jax
	var AbstractAction = require('web.AbstractAction')
	var rpc = require('web.rpc');

	var QWeb = core.qweb;
	var _t = core._t;

	var CombinedStatementsMergeStatementsDefine = AbstractAction.extend({
		events: {},
		template: 'respective_statements_search',

		/**
		 * Init
		 * @param parent 父级节点
		 * @param params 参数
		 */
		init: function (parent, params) {
			this._super.apply(this, arguments);
			// Jax
			this.attributes = params.params;
		},

		start: function () {
			this._super.apply(this, arguments);
			let spread = new GcSpread.Sheets.Spread(this.$el.find('#ss')[0]);
			this.initSpread(spread, this.attributes);

		},

		/**
		 * 初始化Spread
		 * @param spread
		 * @param attributes
		 */
		initSpread: function (spread, attributes) {
			let spreadNS = GcSpread.Sheets;
			let fbx = new spreadNS.FormulaTextBox(this.$el.find('#formulaBar')[0]);
			fbx.spread(spread);
			spread.resizeZeroIndicator(GcSpread.Sheets.ResizeZeroIndicator.Enhanced);
			spread.isPaintSuspended(true);
			let args = [attributes.id]; // 请求参数
			// Jax
			rpc.query({
				model: 'ps.combined.statements.merge.project',
				method: 'get_merge_statements',
				args: [args],
				context: {},
			}).then(function(result) {
				if (result) {
					spread.fromJSON(JSON.parse(result));
					for (var i = 0; i < spread.sheets.length; i++) {
						spread.sheets[i].setIsProtected(true)
					}
				}
			});
			// new Model("ps.combined.statements.merge.project").call("get_merge_statements", args, {context: this.session.user_context || {}}).then(function (result) {
			// 	if (result) {
			// 		spread.fromJSON(JSON.parse(result));
			// 		for (var i = 0; i < spread.sheets.length; i++) {
			// 			spread.sheets[i].setIsProtected(true)
			// 		}
			// 	}
			// });
			spread.isPaintSuspended(false);
			spread.newTabVisible(false);
		}
	});

	/**
	 * open merge statements duide
	 */
	function open_merge_statements_wizard_action() {
		web_client.action_manager.do_action({
			name: "合并报表",
			type: "ir.actions.act_window",
			res_model: "ps.merge.statements.generate.wizard",
			target: 'new',
			xml_id: 'combined_statements.merge_statements_generate_wizard_form',
			views: [[false, 'form']]
		});
	}

	ListView.include({
		render_buttons: function ($node) {
			let add_button = false;
			if (!this.$buttons) {
				add_button = true;
			}

			this._super.apply(this, arguments);

			if (add_button) {
				this.$buttons.on('click', '.o_button_open', open_merge_statements_wizard_action.bind(this));
			}
		},

		// 重写系统记录打开方法
		do_activate_record: function (index, id, dataset, view) {
			if (this.model === 'ps.combined.statements.merge.project') {
				let record = this.records.get(id);
				this.do_action({
					type: "ir.actions.client",
					tag: 'merge.statements',
					params: record,
				});
			} else {
				this._super.apply(this, arguments);
			}
		}
	});

	// Jax
	// 实现内容：点击行信息跳转自定义页面，合并报表查询
	var ListRenderer = require('web.ListRenderer');

	ListRenderer.include({
		_onRowClicked: function (event) {
			if (this.state.model === 'ps.combined.statements.merge.project') {
				// let record = this.state.data[event.currentTarget.rowIndex-1].data;
				let record = this.state.data.find(record => record.id === $(event.currentTarget).data('id')).data;
				this.do_action({
					type: "ir.actions.client",
					tag: 'merge.statements',
					params: record
				});
			}else{
				this._super.apply(this, arguments);
			}
		}
	});

	core.action_registry.add('merge.statements', CombinedStatementsMergeStatementsDefine);
	return CombinedStatementsMergeStatementsDefine;

});