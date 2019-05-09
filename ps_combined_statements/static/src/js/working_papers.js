var namespace = {};
odoo.define('combined_statements.working_papers', function(require) {
	"use strict";
	var core = require('web.core');
	var ListView = require('web.ListView');
	// var Widget = require('web.Widget');
	var web_client = require('web.web_client');
	var session = require('web.session');
	var Dialog = require('web.Dialog');
	// var Model = require('web.Model');
	var localStorage = require('web.local_storage');
	var utils = require('combined_statements.utils');
	// Jax
	var AbstractAction = require('web.AbstractAction')
	var rpc = require('web.rpc');
	var ListController = require('web.ListController');

	var QWeb = core.qweb;
	var _t = core._t;

	var CombinedStatementsWorkingPaperDefine = AbstractAction.extend({
		events: {
			"click #btnSave": "save",
			"click #btnCarryOver": "carryOver",
			"click #btnRecalculate": "recalculate",
			"click #btnSetFormulas": "setDefaultFormulas"
		},
		template: 'combined_statements.working_papers_container',

		init: function(parent, params) {
			this._super.apply(this, arguments);
			// Jax
			if (!jQuery.isEmptyObject(params.params)) {
				this.attributes = params.params;
				localStorage.setItem('working_papers_attributes', JSON.stringify(params.params));
				localStorage.setItem('working_papers_id', this.attributes.id);
			}
		},

		willStart: function() {
			// Define custom function (with namespace)
			function AsyncFormulas() {}

			AsyncFormulas.prototype = new GcSpread.Sheets.Calc.Functions.AsyncFunction('GET', 0, 255);
			AsyncFormulas.prototype.typeName = 'namespace.AsyncFormulas';
			AsyncFormulas.prototype.toJSON = function() {
				return {
					typeName: this.typeName,
					name: this.name,
					maxArgs: this.maxArgs,
					minArgs: this.minArgs
				};
			};
			AsyncFormulas.prototype.defaultValue = function() {
				return "Loading...";
			};

			// 异步请求返回数据
			AsyncFormulas.prototype.evaluateAsync = function(args, context) {
				let respective_statements_params = JSON.parse(localStorage.getItem('respective_statements_params'));
				if (args.length === 1 && !jQuery.isEmptyObject(respective_statements_params)) {
					if (args.includes('originator')) {
						context.SetAsyncResult(respective_statements_params.app_user);
					} else if (args.includes('period')) {
						context.SetAsyncResult(respective_statements_params.period);
					} else if (args.includes('month')) {
						let str = String(respective_statements_params.period);
						context.SetAsyncResult(str.substring(0, 7));
					} else if (args.includes('org_name')) {
						context.SetAsyncResult(respective_statements_params.org_name);
					} else if (args.includes('org_code')) {
						context.SetAsyncResult(respective_statements_params.org_code);
					} else if (args.includes('unit')) {
						context.SetAsyncResult(respective_statements_params.unit);
					}
				} else {
					// Jax
					rpc.query({
						model: 'ps.combined.statements.formulas',
						method: 'get_value_by_async',
						args: [args, context],
						context: {},
					}).then(function(result) {
						context.SetAsyncResult(result);
					});
					// new Model("ps.combined.statements.formulas").call("get_value_by_async", [args, context], {context: respective_statements_params || {}}).then(function(result) {
					// 	context.SetAsyncResult(result);
					// });
				}
			};
			namespace.AsyncFormulas = AsyncFormulas;
			return this._super();
		},

		start: function() {
			this._super.apply(this, arguments);
			this.initSpread();
		},

		/**
		 * 初始化Spread
		 */
		initSpread: function() {
			let args = [parseInt(localStorage.getItem('working_papers_id'))]; // 请求参数
			// Jax
			rpc.query({
				model: 'ps.combined.statements.working.paper.project',
				method: 'get_working_papers_sheets',
				args: [args],
				context: {},
			}).then(function(result) {
				if (result) {
					let data = JSON.parse(result);
					localStorage.removeItem('working_papers');
					localStorage.setItem('working_papers', JSON.stringify(data.bindInfo));
					let spreadNS = GcSpread.Sheets;
					let spread = new spreadNS.Spread($('#ss')[0]);
					let fbx = new spreadNS.FormulaTextBox($('#formulaBar')[0]);

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
			// new Model("ps.combined.statements.working.paper.project").call("get_working_papers_sheets", args, {context: this.session.user_context || {}}).then(function(result) {
			// 	if (result) {
			// 		let data = JSON.parse(result);
			// 		localStorage.removeItem('working_papers');
			// 		localStorage.setItem('working_papers', JSON.stringify(data.bindInfo));
			// 		let spreadNS = GcSpread.Sheets;
			// 		let spread = new spreadNS.Spread($('#ss')[0]);
			// 		let fbx = new spreadNS.FormulaTextBox($('#formulaBar')[0]);
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
		save: function() {
			let data = this.$el.find('#ss').data('spread');
			if(data){
				rpc.query({
					model: 'ps.combined.statements.working.paper.project',
					method: 'update_working_papers',
					args: [localStorage.getItem('working_papers_id'), localStorage.getItem('working_papers'), data.toJSON({includeBindingSource: true}).sheets],
					context: {},
				}).then(function(result){
					if (result) {
						new Dialog.confirm(this, result.message, {
							'title': "提示"
						});
					}
				});
			}else {
				new Dialog.confirm(this, '格式为空，无效的保存！', {
					'title': "提示"
				});
			}
//			console.log(data.toJSON());

			// new Model('ps.combined.statements.working.paper.project').call('update_working_papers', [localStorage.getItem('working_papers_id'), localStorage.getItem('working_papers'), data.toJSON({includeBindingSource: true}).sheets], {context: this.session.user_context || {}}).then(function(result) {
			// 	if (result) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': "提示"
			// 		});
			// 	}
			// });
		},

		/**
		 * 结转
		 */
		carryOver: function() {

			let save = function() {
				let data = this.$el.find("input[name='carry_over']").val();
				// Jax
				rpc.query({
					model: 'ps.combined.statements.working.paper.project',
					method: 'carry_over',
					args: [parseInt(localStorage.getItem('working_papers_id')), data],
					context: {},
				}).then(function(result) {
					if (result.status) {
						new Dialog.confirm(this, result.message, {
							'title': '信息'
						});
					}
				});
				// new Model('ps.combined.statements.working.paper.project').call('carry_over', [parseInt(localStorage.getItem('working_papers_id')), data], {context: this.session.user_context || {}}).then(function(result) {
				// 	if (result.status) {
				// 		new Dialog.confirm(this, result.message, {
				// 			'title': '信息'
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
		 * 重新计算数据
		 */
		recalculate: function() {
			let attributes = JSON.parse(localStorage.getItem('working_papers_attributes'));
			let args = [];
			args.push(attributes.id);
			rpc.query({
				model: 'ps.combined.statements.working.paper.project',
				method: 'recalculate',
				args: [args],
				context: {},
			}).then(function (result) {
				new Dialog.confirm(this, result.message, {
					'title': '提示'
				});
			})
			// new Model('ps.combined.statements.working.paper.project').call('recalculate', args, {context: this.session.user_context || {}}).then(function(result) {
			// 	new Dialog.confirm(this, result.message, {
			// 		'title': '提示'
			// 	});
			// })
		},

		setDefaultFormulas: function() {
			let spread = this.$el.find('#ss').data('spread');
			let activeSheet = spread.getActiveSheet();

			for (let i = 0; i < activeSheet.getRowCount(); i++) {
				// =IF(C4="借",F4+G4-H4, F44-G44+H44)
				let row_index = (i+1).toString();
				let col_index = activeSheet.getColumnCount();
				let sumValue = utils.numToString(col_index - 4).concat(row_index);     // 合计数
				let debitValue = utils.numToString(col_index - 3).concat(row_index); // 抵消分录 借方
				let creditValue = utils.numToString(col_index - 2).concat(row_index); // 抵消分录 贷方
				let mergeFormula = '=IF(C1="借",'.concat(sumValue).concat('+').concat(debitValue).concat('-').concat(creditValue).concat(',').concat(sumValue).concat('-').concat(debitValue).concat('+').concat(creditValue).concat(')');
				activeSheet.setFormula(i, col_index - 1, mergeFormula)
			}
		}
	});

	/**
	 * 打开工作底稿创建向导页面
	 */
	function open_wording_papers_wizard_action() {
		web_client.action_manager.do_action({
			name: "底稿定义",
			type: "ir.actions.act_window",
			res_model: "working.papers.define.wizard",
			target: 'new',
			xml_id: 'combined_statements.working_papers_define_wizard_form',
			views: [[false, 'form']]
		});
	}

	ListView.include({
		render_buttons: function($node) {
			let add_button = false;
			if (!this.$buttons) {
				add_button = true;
			}

			this._super.apply(this, arguments);

			if (add_button) {
				this.$buttons.on('click', '.o_button_open', open_wording_papers_wizard_action.bind(this));
			}
		},

		// 重写系统记录打开方法
		do_activate_record: function(index, id, dataset, view) {
			// 在odoo12中无效
			// if (this.model === 'ps.combined.statements.working.paper.project') {
			// 	let record = this.records.get(id);
			// 	alert('do_activate_record');
			// 	this.do_action({
			// 		type: "ir.actions.client",
			// 		tag: 'working.papers',
			// 		params: record
			// 	});
			// } else {
			// 	this._super.apply(this, arguments);
			// }
		}
	});
	// Jax
	// 实现内容：点击行信息跳转自定义页面，工作底稿查询
	var ListRenderer = require('web.ListRenderer');

	ListRenderer.include({
		_onRowClicked: function (event) {
			if (this.state.model === 'ps.combined.statements.working.paper.project') {
				// let record = this.state.data[event.currentTarget.rowIndex-1].data;
				let record = this.state.data.find(record => record.id === $(event.currentTarget).data('id')).data;
				console.log(record);
				this.do_action({
					type: "ir.actions.client",
					tag: 'working.papers',
					params: record
				});
			}else{
				this._super.apply(this, arguments);
			}
		}
	});

	core.action_registry.add('working.papers', CombinedStatementsWorkingPaperDefine);
	return CombinedStatementsWorkingPaperDefine;

});

// Jax
// 实现内容：点击行信息跳转自定义页面，工作底稿查询
// odoo.define('ps.web.ListRenderer', function (require) {
// "use strict";
// var ListRenderer = require('web.ListRenderer');
//
// 	ListRenderer.include({
// 		_onRowClicked: function (event) {
// 			if (this.state.model === 'ps.combined.statements.working.paper.project') {
// 				// let record = this.state.data[event.currentTarget.rowIndex-1].data;
// 				let record = this.state.data.find(record => record.id === $(event.currentTarget).data('id')).data;
// 				console.log(record);
// 				this.do_action({
// 					type: "ir.actions.client",
// 					tag: 'working.papers',
// 					params: record
// 				});
// 			}else{
// 				this._super.apply(this, arguments);
// 			}
// 		}
// 	});
// });

