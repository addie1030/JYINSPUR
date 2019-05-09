odoo.define('combined_statements.adjust_working_papers_project', function (require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	// var Widget = require('web.Widget');
	var utils = require('web.utils');
	var web_client = require('web.web_client');
	var session = require('web.session');
	var Dialog = require('web.Dialog');
	// var Model = require('web.Model');
	var AdjUtils = require('combined_statements.utils');

	// Jax
	var AbstractAction = require('web.AbstractAction')
	var rpc = require('web.rpc');

	var QWeb = core.qweb;
	var _t = core._t;

	var CombinedStatementsAdjustWorkingPaperDefine = AbstractAction.extend({
		events: {
			"click #btnSave": "save",
			"click #btnCarryOver": "adjcarryOver",
			"click #btnSetFormulas": "setDefaultFormulas",
			"click #btnRecalculate": "adjrecalculate",
		},
		template: 'combined_statements.working_papers_container',

		init: function (parent, params) {
			this._super.apply(this, arguments);
			// Jax
			// params.params.attributes
			if (!jQuery.isEmptyObject(params.params)) {
				this.attributes = params.params;
				localStorage.setItem('adjworking_papers_attributes', JSON.stringify(params.params.attributes));
				localStorage.setItem('adjworking_papers_id', this.attributes.id)
			}
		},

		start: function () {
			this._super.apply(this, arguments);
			this.initSpread();
		},

		/**
		 * 初始化Spread
		 * @param attributes
		 */
		initSpread: function () {
			let args = [parseInt(localStorage.getItem('adjworking_papers_id'))];
			rpc.query({
				model: 'ps.combined.statements.adjust.working.paper.project',
				method: 'get_adjust_working_papers_sheets',
				args: [args],
				context: {},
			}).then(function(result) {
				if (result) {
					let data = JSON.parse(result);
					localStorage.removeItem('working_papers');
					localStorage.setItem('working_papers', JSON.stringify(data.bindInfo));
					let spread = new GcSpread.Sheets.Spread(self.$('#ss')[0]);
					let spreadNS = GcSpread.Sheets;
					let fbx = new spreadNS.FormulaTextBox(self.$('#formulaBar')[0]);

					fbx.spread(spread);
					spread.isPaintSuspended(true);
					let serializationOption = {
						ignoreFormula: false,
						ignoreStyle: false,
						frozenColumnsAsRowHeaders: false,
						frozenRowsAsColumnHeaders: false,
						doNotRecalculateAfterLoad: false
					};
					spread.fromJSON(data.spread, serializationOption);

					spread.resizeZeroIndicator(GcSpread.Sheets.ResizeZeroIndicator.Enhanced);
					spread.isPaintSuspended(false);
				}
			});
			// new Model("ps.combined.statements.adjust.working.paper.project").call("get_adjust_working_papers_sheets", args, {context: this.session.user_context || {}}).then(function (result) {
			// 	if (result) {
			// 		let data = JSON.parse(result);
			// 		localStorage.removeItem('working_papers');
			// 		localStorage.setItem('working_papers', JSON.stringify(data.bindInfo));
			// 		let spread = new GcSpread.Sheets.Spread(self.$('#ss')[0]);
			// 		let spreadNS = GcSpread.Sheets;
			// 		let fbx = new spreadNS.FormulaTextBox(self.$('#formulaBar')[0]);
			//
			// 		fbx.spread(spread);
			// 		spread.isPaintSuspended(true);
			// 		let serializationOption = {
			// 			ignoreFormula: false,
			// 			ignoreStyle: false,
			// 			frozenColumnsAsRowHeaders: false,
			// 			frozenRowsAsColumnHeaders: false,
			// 			doNotRecalculateAfterLoad: false
			// 		};
			// 		spread.fromJSON(data.spread, serializationOption);
			//
			// 		spread.resizeZeroIndicator(GcSpread.Sheets.ResizeZeroIndicator.Enhanced);
			// 		spread.isPaintSuspended(false);
			// 	}
			// });
		},
		save: function () {
			let data = this.$el.find('#ss').data('spread');
			rpc.query({
				model: 'ps.combined.statements.adjust.working.paper.project',
				method: 'update_adjust_working_papers',
				args: [localStorage.getItem('adjworking_papers_id'), localStorage.getItem('working_papers'),data.toJSON({includeBindingSource: true}).sheets],
				context: {},
			}).then(function(result) {
				if (result) {
					new Dialog.confirm(this, result.message, {
						'title': _t("information")
					});
				}
			});
			// new Model('ps.combined.statements.adjust.working.paper.project').call('update_adjust_working_papers', [localStorage.getItem('adjworking_papers_id'), localStorage.getItem('working_papers'),data.toJSON({includeBindingSource: true}).sheets], {context: this.session.user_context || {}}).then(function (result) {
			// 	if (result) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': _t("information")
			// 		});
			// 	}
			// });
		},

		/**
		 * 结转
		 */
		adjcarryOver: function () {

			let save = function () {
				let data = this.$el.find("input[name='carry_over']").val();
				rpc.query({
					model: 'ps.combined.statements.adjust.working.paper.project',
					method: 'adj_carry_over',
					args: [parseInt(localStorage.getItem('adjworking_papers_id')), data],
					context: {},
				}).then(function(result) {
					if (result.status) {
						new Dialog.confirm(this, result.message, {
							'title': '提示'
						});
					}
				});
				// new Model('ps.combined.statements.adjust.working.paper.project').call('adj_carry_over', [parseInt(localStorage.getItem('adjworking_papers_id')), data], {context: this.session.user_context || {}}).then(function (result) {
				// 	if (result.status) {
				// 		new Dialog.confirm(this, result.message, {
				// 			'title': '提示'
				// 		});
				// 	}
				// });
			};
			new Dialog(this, {
				title: "结转",
				size: 'medium',
				buttons: [
					{
						text: "结转",
						classes: 'btn-primary',
						close: true,
						click: save
					}, {
						text: _t("Cancel"),
						close: true
					}
				],
				$content: $(QWeb.render('carryOver'))
			}).open();
		},
		/**
		 * 公式设置
		 */
		setDefaultFormulas: function () {
			let spread = this.$el.find('#ss').data('spread');
			let activeSheet = spread.getActiveSheet();

			for (let i = 0; i < activeSheet.getRowCount(); i++) {
				// =IF(C4="借",F4+G4-H4, F44-G44+H44)
				let row_index = (i + 1).toString();
				let col_index = activeSheet.getColumnCount();
				let sumValue = AdjUtils.numToString(col_index - 4).concat(row_index);     // 合计数
				let debitValue = AdjUtils.numToString(col_index - 3).concat(row_index); // 抵消分录 借方
				let creditValue = AdjUtils.numToString(col_index - 2).concat(row_index); // 抵消分录 贷方
				let mergeFormula = '=IF(C1="借",'.concat(sumValue).concat('+').concat(debitValue).concat('-').concat(creditValue).concat(',').concat(sumValue).concat('-').concat(debitValue).concat('+').concat(creditValue).concat(')');
				activeSheet.setFormula(i, col_index - 1, mergeFormula)

			}
		},
		/**
		 * 重新计算
		 */
		adjrecalculate: function () {
			let attributes = JSON.parse(localStorage.getItem('adjworking_papers_attributes'));
			rpc.query({
				model: 'ps.combined.statements.adjust.working.paper.project',
				method: 'adjrecalculate',
				args: [attributes.id],
				context: {},
			}).then(function(result) {
				new Dialog.confirm(this, result.message, {
					'title': '提示'
				});
			});
			// new Model('ps.combined.statements.adjust.working.paper.project').call('adjrecalculate', [attributes.id], {context: this.session.user_context || {}}).then(function (result) {
			// 	new Dialog.confirm(this, result.message, {
			// 		'title': '提示'
			// 	});
			// })
		},


	});

	/**
	 * open adjust working papers duide
	 */
	function open_adjust_wording_papers_wizard_action() {
		web_client.action_manager.do_action({
			name: "调整工作底稿",
			type: "ir.actions.act_window",
			res_model: "ps.adjust.working.papers.generate.wizard",
			target: 'new',
			xml_id: 'combined_statements.adjust_working_papers_generate_wizard_form',
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
				this.$buttons.on('click', '.o_button_open', open_adjust_wording_papers_wizard_action.bind(this));
			}
		},

		/**
		 * Overrides the system open method
		 * @param index : index
		 * @param id : id
		 * @param dataset : DataSet
		 * @param view: view
		 */
		do_activate_record: function (index, id, dataset, view) {
			if (this.model === 'ps.combined.statements.adjust.working.paper.project') {
				let record = this.records.get(id);
				this.do_action({
					type: "ir.actions.client",
					tag: 'adjust.working.papers',
					params: record,
				});
			} else {
				this._super.apply(this, arguments);
			}
		}
	});

	// Jax
	// 实现内容：点击行信息跳转自定义页面，调整工作底稿查询
	var ListRenderer = require('web.ListRenderer');

	ListRenderer.include({
		_onRowClicked: function (event) {
			if (this.state.model === 'ps.combined.statements.adjust.working.paper.project') {
				// let record = this.state.data[event.currentTarget.rowIndex-1].data;
				let record = this.state.data.find(record => record.id === $(event.currentTarget).data('id')).data;
				this.do_action({
					type: "ir.actions.client",
					tag: 'adjust.working.papers',
					params: record
				});
			}else{
				this._super.apply(this, arguments);
			}
		}
	});

	core.action_registry.add('adjust.working.papers', CombinedStatementsAdjustWorkingPaperDefine);
	return CombinedStatementsAdjustWorkingPaperDefine;

});