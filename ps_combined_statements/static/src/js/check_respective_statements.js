var namespace = {};
odoo.define('check.respective.statements.journaling', function (require) {
	"use strict";

	var core = require('web.core');
	var Widget = require('web.Widget');
	var Model = require('web.Model');
	var Dialog = require('web.Dialog');
	var _t = core._t;

	var CheckRespectiveStatementsJournaling = Widget.extend({
		template: 'respective_statements_search',

		/**
		 * 初始化方法
		 * @param parent 父级节点
		 * @param context
		 */
		init: function (parent, context) {
			this._super.apply(this, arguments);
			this.repective = context.context.repective;
			this.project_id = context.context.project_id;
			this.period_id = context.context.period;
			// this.company_id = context.context.company_id;

			if (Object.keys(context.context).includes('org_name')) {
				localStorage.setItem('check_respective_statements_params', JSON.stringify(context.context));
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
				let respective_statements_params = JSON.parse(localStorage.getItem('check_respective_statements_params'));
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
					new Model("ps.combined.statements.formulas").call("get_value_by_async", [args, context], {context: respective_statements_params || {}}).then(function(result) {
						context.SetAsyncResult(result);
					});
				}
			};
			namespace.AsyncFormulas = AsyncFormulas;
			return this._super();
		},

		start: function () {
			this._super.apply(this, arguments);
			let spread = new GcSpread.Sheets.Spread(this.$el.find('#ss')[0]);
			this.initSpread(spread);
		},

		/**
		 * 初始化Spread
		 * @param spread Object
		 */
		initSpread: function (spread) {

			let spreadNS = GcSpread.Sheets;
			let fbx = new spreadNS.FormulaTextBox(this.$el.find('#formulaBar')[0]);
			fbx.spread(spread);

			spread.isPaintSuspended(true);

			spread.resizeZeroIndicator(GcSpread.Sheets.ResizeZeroIndicator.Enhanced);

			// 获取报表项目工作簿
			new Model('ps.respective.statements.project').call('get_sheets', [this.repective], {context: this.session.user_context || {}}).then(function (result) {
				if (result) {
					let data = JSON.parse(result);
					spread.fromJSON(data.report);
					localStorage.setItem('IndividualReportValidateRules', JSON.stringify(data.ValidateRules));
					for (let i = 0; i < spread.sheets.length; i++) {
						spread.sheets[i].setIsProtected(true)
					}
				}
			});
			spread.isPaintSuspended(false);
			spread.newTabVisible(false);
		},

	});

	core.action_registry.add('check.respective.statements', CheckRespectiveStatementsJournaling);
	return CheckRespectiveStatementsJournaling;
});