var namespace = {};
odoo.define('respective.statements.journaling', function(require) {
	"use strict";

	var core = require('web.core');
	// Jax
	// var Widget = require('web.Widget');
	// var Model = require('web.Model');
	var AbstractAction = require('web.AbstractAction')
	var rpc = require('web.rpc');
	var Dialog = require('web.Dialog');
	var time = require('web.time');
	var localStorage = require('web.local_storage');
	var utils = require('combined_statements.utils');
	var spreadNS = GcSpread.Sheets;

	var QWeb = core.qweb;
	var _t = core._t;
	var success_id = -1;

	var RespectiveStatementsJournaling = AbstractAction.extend({
		events: {
			"click #btnSave": "save",
			"click #btnMonetaryUnitAdjust": "reported_data",
			"click #btnInitialization": "recall",
			"click #btnDataValidate": "btnDataValidate_on_click",
			"click #btnPrint": "print_on_click"
			// "click #btnInitialization": "Initialization_journaling"
		},
		template: 'respective_statements',

		/**
		 * 初始化方法
		 * @param parent 父级节点
		 * @param params 参数
		 */
		init: function(parent, params) {

			let widget = parent.inner_widget;

			if (widget != null && widget.$el.find('#ss').length > 0) {
				parent.inner_widget.destroy();
			}
			this._super.apply(this, arguments);

			if (Object.keys(params.context).includes('org_name')) {
				localStorage.setItem('respective_statements_params', JSON.stringify(params.context));
			}

			this.project_id = params.params.project_id; // 套表模板ID
			this.period = params.params.period; // 期间
			this.app_company = params.params.app_company; // 公司
			this.state = params.params.state; //状态
			success_id = -1;
			this.respective_project = params.params.respective_project; //项目ID
			this.uom = params.params.unit;
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
						context: {context: respective_statements_params || {}},
					}).then(function(result) {
						context.SetAsyncResult(result);
					});
					// new Model("ps.combined.statements.formulas").call("get_value_by_async", [args, context], {context: respective_statements_params || {}} ).then(function(result) {
					// 	context.SetAsyncResult(result);
					// });
				}
			};
			namespace.AsyncFormulas = AsyncFormulas;
			return this._super();
		},

		start: function() {
			this._super.apply(this, arguments);
			let spread = new GcSpread.Sheets.Spread(this.$el.find('#ss')[0]);
			this.initSpread(spread);
		},
		/**
		 * 初始化Spread
		 * @param spread Object
		 */
		initSpread: function(spread) {

			let spreadNS = GcSpread.Sheets;
			let fbx = new spreadNS.FormulaTextBox(this.$el.find('#formulaBar_nodesign')[0]);
			fbx.spread(spread);

			spread.isPaintSuspended(true);

			spread.resizeZeroIndicator(GcSpread.Sheets.ResizeZeroIndicator.Enhanced);
			if (this.state === 'no') {
				// 获取报表项目工作簿
				// Jax
				rpc.query({
					model: 'ps.combined.statements.project',
					method: 'get_sheets',
					args: [this.project_id],
					context: {},
				}).then(function (result) {
					if (result) {
						let data = JSON.parse(result);
						spread.fromJSON(data.report);
						localStorage.setItem('IndividualReportValidateRules', JSON.stringify(data.ValidateRules));

					}
				})
				// new Model('ps.combined.statements.project').call('get_sheets', [this.project_id], {context: this.session.user_context || {}}).then(function(result) {
				// 	if (result) {
				// 		let data = JSON.parse(result);
				// 		spread.fromJSON(data.report);
				// 		localStorage.setItem('IndividualReportValidateRules', JSON.stringify(data.ValidateRules));
				//
				// 	}
				// });
			}
			if (this.state === 'yes') {
				// 获取报表项目工作簿
				// Jax
				rpc.query({
					model: 'ps.respective.statements.project',
					method: 'get_sheets',
					args: [this.respective_project],
					context: {},
				}).then(function (result) {
					if (result) {
						let data = JSON.parse(result);
						spread.fromJSON(data.report);
						localStorage.setItem('IndividualReportValidateRules', JSON.stringify(data.ValidateRules));
					}
				})
				// new Model('ps.respective.statements.project').call('get_sheets', [this.respective_project], {context: this.session.user_context || {}}).then(function(result) {
				// 	if (result) {
				// 		let data = JSON.parse(result);
				// 		spread.fromJSON(data.report);
				// 		localStorage.setItem('IndividualReportValidateRules', JSON.stringify(data.ValidateRules));
				// 	}
				// });
			}
			spread.isPaintSuspended(false);
			spread.newTabVisible(false);
		},

		/**
		 * 销毁当前窗口小部件
		 */
		destroy: function() {
			console.log("Journaling destroy.......");
			return this._super.apply(this, arguments);
		},

		/**
		 * 保存报表
		 */
		save: function() {
			// 获取界面数据
			if (!this.btnDataValidate_on_click()) return;
			let ValidateRulesCache = localStorage.getItem('IndividualReportValidateRules');
			let ValidateRules = JSON.parse(ValidateRulesCache);
			let data = this.$el.find('#ss').data('spread');
			let spreadJSON = data.toJSON();
			// Jax
			rpc.query({
				model: 'ps.respective.statements.project',
				method: 'save',
				args: [this.state, this.respective_project, this.project_id, this.period, this.app_company, data.toJSON().sheets, spreadJSON.customFunctions, ValidateRules],
				context: {},
			}).then(function (result) {
				if (result.status) {
					new Dialog.confirm(this, result.message, {
						'title': '消息'
					});
					success_id = result.id;
				}
			})
			// new Model('ps.respective.statements.project').call('save', [this.state, this.respective_project, this.project_id, this.period, this.app_company, data.toJSON().sheets, spreadJSON.customFunctions, ValidateRules], {context: this.session.user_context || {}}).then(function(result) {
			// 	if (result.status) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': '消息'
			// 		});
			// 		success_id = result.id;
			// 	}
			// });
		},

		/***
		 * 上报数据
		 **/
		reported_data: function() {
			if (!this.btnDataValidate_on_click()) return;
			// Jax
			rpc.query({
				model: 'ps.respective.statements.project',
				method: 'reported_data',
				args: [success_id],
				context: {},
			}).then(function (result) {
				if (result) {
					new Dialog.confirm(this, result.message, {
						'title': '消息'
					});
				}
			})
			// new Model('ps.respective.statements.project').call('reported_data', [success_id]).then(function(result) {
			// 	if (result) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': '消息'
			// 		});
			// 	}
			// });
		},
		/**
		 * 撤回上报
		 */
		recall: function() {
			// Jax
			rpc.query({
				model: 'ps.respective.statements.project',
				method: 'recall',
				args: [success_id],
				context: {},
			}).then(function (result) {
				if (result) {
					new Dialog.confirm(this, result.message, {
						'title': '消息'
					});
				}
			})
			// new Model('ps.respective.statements.project').call('recall', [success_id]).then(function(result) {
			// 	if (result) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': '消息'
			// 		});
			// 	}
			// });
		},

		// 数据校验
		btnDataValidate_on_click: function() {
			let ValidateRulesCache = localStorage.getItem('IndividualReportValidateRules');

			if (!ValidateRulesCache) {
				Dialog.confirm(this, "验证规则未定义。", {'title': '警告'});
			}

			let ValidateRules = JSON.parse(ValidateRulesCache);
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));

			let ValidateResult = [];
			let ValidateResultFlag = true;

			ValidateRules.forEach(function(rule) {
				// 匹配计算结果对应的公式(等号左边)
				let result_formula = rule.value.match('^[^=]*(?==)');
				// 匹配用于计算的公式(等号右边)
				let calculation_formula = rule.value.match('(?<==).*$');
				// 运算符
				let operator = calculation_formula[0].match('[\*\\+-]');

				let computeStr = '';
				let patten = RegExp(/[+-]/);
				if (!calculation_formula[0].match(patten) || (operator === undefined || operator.length === 0)) {
					let formula_str = calculation_formula[0].split('!');
					let result = utils.getCellValueWithSpread(spread, formula_str[0], formula_str[1]);
					result = utils.isNumber(result) ? result : 0;   // 校验数据是否为Number
					computeStr = result;
				} else {
					// 拆分公式
					let all_formula = calculation_formula[0].split(patten);

					all_formula.forEach(function(formula, index) {
						let formula_str = formula.split('!');
						let result = utils.getCellValueWithSpread(spread, formula_str[0], formula_str[1]);
						result = utils.isNumber(result) ? result : 0;   // 校验数据是否为Number

						if (index === 0) {
							computeStr = computeStr + result + operator[index];
						} else if (index === all_formula.length - 1) {
							computeStr = computeStr + result;
						} else {
							computeStr = computeStr + result + operator[(index%2) + 1];
						}
					});
				}
				let result_formula_arr = result_formula[0].split('!');
				let result_value = utils.getCellValueWithSpread(spread, result_formula_arr[0], result_formula_arr[1]);

				if (result_value !== eval(computeStr)) {
					ValidateResultFlag = false;
					ValidateResult.push({
						rule: rule.value,
						flag: '失败'
					});
				} else {
					ValidateResult.push({
						rule: rule.value,
						flag: '成功'
					});
				}

			});

			if (!ValidateResultFlag) {
				new Dialog(this, {
					title: '数据校验',
					size: 'medium',
					buttons: [{text: '关闭', close: true}],
					$content: $(QWeb.render('ValidateRulesResultDialog', {widget: this, data: ValidateResult}))
				}).open();
			}

			return ValidateResultFlag;
		},

		/**
		 * 打印
		 */
		print_on_click: function() {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			let sheet = spread.getActiveSheet();
			let printInfo = sheet.printInfo();
			printInfo.showRowHeader(GcSpread.Sheets.PrintVisibilityType.Show);
			printInfo.showColumnHeader(GcSpread.Sheets.PrintVisibilityType.Show);
			spread.print(spread.getActiveSheetIndex());
		}
	});

	core.action_registry.add('respective.statements', RespectiveStatementsJournaling);
	return RespectiveStatementsJournaling;
});