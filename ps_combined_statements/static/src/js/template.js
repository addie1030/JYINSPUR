var namespace = {};
odoo.define('combined.statements.journaling', function(require) {
	"use strict";

	var core = require('web.core');
	// var Widget = require('web.Widget');
	// var Model = require('web.Model');
	var AbstractAction = require('web.AbstractAction')
	var rpc = require('web.rpc');
	var time = require('web.time');
	var Dialog = require('web.Dialog');
	var session = require('web.session');
	var spreadNS = GcSpread.Sheets;
	var localStorage = require('web.local_storage');

	var QWeb = core.qweb;
	var _t = core._t;

	var CombinedStatementsJournaling = AbstractAction.extend({
		events: {
			"click #btnSave": "save",
			"click #btnReportProperties": "btnReportProperties_on_click",
			"click #btnPrint": "print_on_click",
			"click #btnSaveastemplate": "Save_template_on_click",
			"click #btnLoadtemplate": "loadTemplateOnClick",
			"click #btnFormulaGuide": "btnFormulaGuide",
			"click #btnDelReport": "DelSpreadSheet",
			"click #btnColumnDefine": "ColumnDefine",
			"click #btnAddSheet": "AddSpreadSheet",
			"click #btnValidateRules": "btnValidateRules_on_click"
		},
		template: 'journaling_template',
		/**
		 * 初始化方法
		 * @param parent 父级节点
		 * @param params 参数
		 */
		init: function(parent, params) {
			this._super.apply(this, arguments);
			this.project_id = params.params.project_id; // 项目ID
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
				context.SetAsyncResult("{".concat(args[0]).concat("}"));
//				if (args.length === 1 && (args.includes('originator') || args.includes('period') || args.includes('month') || args.includes('org_name') || args.includes('org_code') || args.includes('unit'))) {
//					context.SetAsyncResult("{" + args[0] + "}");
//				} else if (args.length > 1) {
//					context.SetAsyncResult("{".concat(args[0]).concat("}"));
//				}
			};
			namespace.AsyncFormulas = AsyncFormulas;
			return this._super();
		},

		start: function() {
			this._super.apply(this, arguments);
			console.log("Journaling start.......");

			let intfunc = this.initSpread;
			// 获取报表项目工作簿
			// Jax
			rpc.query({
				model: 'ps.combined.statements.project',
				method: 'get_sheets',
				args: [this.project_id],
				context: {},
			}).then(function(result){
					if (result) {
						let data = JSON.parse(result);
						intfunc(data);
						localStorage.setItem('ValidateRules', JSON.stringify(data.ValidateRules));
						if (!jQuery.isEmptyObject(data.sheets_info)) {
							localStorage.setItem('template_define', JSON.stringify(data.sheets_info));
						} else {
							localStorage.setItem('template_define', '{}');  // 如果是新增则需要用一个默认的代替
						}
					} else {
						localStorage.setItem('ValidateRules', '[]');
						intfunc(false);
					}
			});
			// new Model('ps.combined.statements.project').call('get_sheets', [this.project_id], {context: this.session.user_context || {}}).then(function(result) {
			// 	if (result) {
			// 		let data = JSON.parse(result);
			// 		intfunc(data);
			// 		localStorage.setItem('ValidateRules', JSON.stringify(data.ValidateRules));
			// 		if (!jQuery.isEmptyObject(data.sheets_info)) {
			// 			localStorage.setItem('template_define', JSON.stringify(data.sheets_info));
			// 		} else {
			// 			localStorage.setItem('template_define', '{}');  // 如果是新增则需要用一个默认的代替
			// 		}
			// 	} else {
			// 		localStorage.setItem('ValidateRules', '[]');
			// 		intfunc(false);
			// 	}
			// });

			// 绑定Jquery右键菜单，显示出弹出菜单
			this.$el.find('#ss').bind("contextmenu", processSpreadContextMenu);
			this.$el.find("ul li a").click(processContextMenuClicked);
		},

		/**
		 * 初始化Spread
		 * @param data Json
		 */
		initSpread: function(data) {
			let fbx = new spreadNS.FormulaTextBox($('#formulaBar')[0]);
			let spread = new GcSpread.Sheets.Spread($('#ss')[0]);

			// 表格序列化选项参数
			let serializationOption = {
				ignoreFormula: false,
				ignoreStyle: false,
				frozenColumnsAsRowHeaders: false,
				frozenRowsAsColumnHeaders: false,
				doNotRecalculateAfterLoad: false
			};
			spread.isPaintSuspended(true);
			if (data) {
				spread.fromJSON(data.report, serializationOption);
			} else {
				spread.addCustomFunction(new namespace.AsyncFormulas());
			}

			fbx.spread(spread);

			// 默认样式
			let defaultStyle = new spreadNS.Style();
			defaultStyle.foreColor = "Red";
			defaultStyle.formatter = "0.00";
			defaultStyle.hAlign = spreadNS.HorizontalAlign.center;
			defaultStyle.vAlign = spreadNS.VerticalAlign.center;
			defaultStyle.borderLeft = new spreadNS.LineBorder("Green");
			defaultStyle.borderTop = new spreadNS.LineBorder("Green");
			defaultStyle.borderRight = new spreadNS.LineBorder("Green");
			defaultStyle.borderBottom = new spreadNS.LineBorder("Green");
			spread.resizeZeroIndicator(spreadNS.ResizeZeroIndicator.Enhanced);

			spread.tabEditable(false);
			spread.newTabVisible(false);

			spread.isPaintSuspended(false);
		},

		// 公式定义
		btnFormulaGuide: function() {
			// Jax
			rpc.query({
				model: 'ps.combined.statements.formulas',
				method: 'get_combined_statements_formulas_data',
				args: [],
			}).then(function (result) {
				this.dialog = new Dialog(this, {
					title: '公式定义',
					size: 'large',
					buttons: [{text: _t("Save"), classes: 'btn-primary', close: true}, {text: _t("Cancel"), close: true}],
					$content: $(QWeb.render('JournalingFormulaDefineInfo', {widget: this, data: result}))
				}).open();
				let spreadtemp = GcSpread.Sheets.findControl(document.getElementById('ss'));
				let sheet = spreadtemp.getActiveSheet();
				let selectedRanges = sheet.getSelections();
				let selectedrow = selectedRanges[0].row;
				let selectedrowcount = selectedRanges[0].rowCount;
				let selectedcol = selectedRanges[0].col;
				let selectedcolcount = selectedRanges[0].colCount;
				let rangestartrow = "";
				if (selectedrow === -1) {
					rangestartrow = 1;
				} else {
					rangestartrow = selectedrow + 1;
				}
				let rangeendrow = rangestartrow + selectedrowcount - 1;
				let rangestartcol = sheet.getText(0, selectedcol, GcSpread.Sheets.SheetArea.colHeader);
				let rangeendcol = sheet.getText(0, selectedcol + selectedcolcount - 1, GcSpread.Sheets.SheetArea.colHeader);
				let selectedrange = rangestartcol + rangestartrow + ":" + rangeendcol + rangeendrow;
				$("#formula_Range").val(selectedrange);

				let addelement = function() {
					this.result = result;
					// 处理选中的下拉框值
					for (let i = 0; i < this.result.length; i++) {
						if (this.result[i]['id'] === $("#formula_option").val()) {
							this.result = this.result[i];
							break;
						}
					}
					$(".formula_params_ids").remove();
					let formula_params_ids = '';
					// 动态添加公式参数
					for (let i = 0; i < this.result['formula_params_ids'].length; i++) {
						formula_params_ids += '<div class="col-md-4 formula_params_ids"><div class="form-group"><span>' + this.result['formula_params_ids'][i]['name'] + '</span><input type="text"' +
							' class="form-control" t-att-index="' + this.result['formula_params_ids'][i]['id'] + '"/></div></div>';
					}
					$("#FormulaDefineInfotwo").append(formula_params_ids);
				};
				this.dialog.$content.on('change', '#formula_option', result, addelement);
			});

		},

		// 销毁当前窗口小部件
		destroy: function() {
			console.log("Journaling destroy.......");
			this._super.apply(this, arguments);
		},

		// 保存报表
		save: function() {
			// 获取界面数据
			let data = this.$el.find('#ss').data('spread');
			console.log(data.toJSON());
			let spreadJSON = data.toJSON();

			let template_define = JSON.parse(localStorage.getItem('template_define'));
			let validate_rules = JSON.parse(localStorage.getItem('ValidateRules'));
			let parm = [
				this.project_id,
				spreadJSON.sheets,
				spreadJSON.newTabVisible,
				spreadJSON.tabEditable,
				spreadJSON.customFunctions,
				template_define,
				validate_rules
			];
			// Jax
			rpc.query({
				model: 'ps.combined.statements.project',
				method: 'save',
				args: [
					this.project_id,
					spreadJSON.sheets,
					spreadJSON.newTabVisible,
					spreadJSON.tabEditable,
					spreadJSON.customFunctions,
					template_define,
					validate_rules
				],
				context: {},
			}).then(function (result) {
				if (result) {
					new Dialog.confirm(this, result.message, {
						'title': _t("information")
					});
				}
			});

			// new Model('ps.combined.statements.project').call('save', parm, {context: this.session.user_context || {}}).then(function(result) {
			// 	if (result) {
			// 		new Dialog.confirm(this, result.message, {
			// 			'title': _t("information")
			// 		});
			// 	}
			// });
		},

		// 添加Sheet
		AddSpreadSheet: function() {
			let template_define = JSON.parse(localStorage.getItem('template_define'));
			let save = function() {
				let _name = this.$el.find("input[name='report_name']").val();
				let _head_count = this.$el.find("input[name='titlerows']").val();
				let _row_count = this.$el.find("input[name='rowcount']").val();
				let _tail_count = this.$el.find("input[name='tailrows']").val();
				let _col_offset = this.$el.find("input[name='coloffset']").val();
				let _uom = this.$el.find("select[name='uom'] option:selected").val();
				let _column_count = this.$el.find("input[name='columncount']").val();
				let _protected = this.$el.find("input[name='protected']").prop("checked");

				let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
				let sheet = new GcSpread.Sheets.Sheet();
				// Jax 样表名称判断
				for(let template in template_define){
					if(template === _name){
						// dialog没作用，暂用alert
						alert('存在重复名称的页签！');
						Dialog.confirm(this, "存在重复名称的页签！",{'title': '警告'});
						return
					}
				}
				if (_name.length == 0){
					// dialog没作用，暂用alert
					alert('样表名称不能为空');
					Dialog.confirm(this, "样表名称不能为空！",{'title': '警告'});
				} else {
					sheet.setName(_name);
					sheet.setRowCount(_row_count);
					sheet.setColumnCount(_column_count);
					sheet.setIsProtected(_protected);
					spread.addSheet(spread.getSheetCount(), sheet);
					spread.setActiveSheetIndex(spread.getSheetCount() - 1);

					template_define[_name] = {
						'name': _name,
						'cols_info': [],
						'head_count': _head_count,
						'row_count': _row_count,
						'tail_count': _tail_count,
						'col_offset': _col_offset,
						'column_count': _column_count,
						'uom': _uom,
						'is_protected': _protected
					};
					localStorage.setItem('template_define', JSON.stringify(template_define));
				}

			};
			new Dialog(this, {
				title: "报表设置",
				size: 'large',
				buttons: [{text: _t("Save"), classes: 'btn-primary', close: true, click: save}, {text: _t("Cancel"), close: true}],
				$content: $(QWeb.render('JournalingProperties', {
					widget: this, data: {'name': "", 'head_count': 1, 'tail_count': 1, 'uom': 'yuan', 'is_protected': false, 'row_count': 10, 'column_count': 5}
				}))
			}).open();
		},

		// 删除Sheet
		DelSpreadSheet: function(e) {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			let template_define = JSON.parse(localStorage.getItem('template_define'));
			let messae = "您确定要删除 [ " + spread.getActiveSheet().getName() + " ] 吗？";
			let options = {
				title: "警告",
				size: "medium",
				buttons: [{
					text: "确定",
					close: true,
					classes: 'btn-primary',
					click: function() {
						// Jax 只有一个页签时删除报错处理 spread.getSheetCount() > 0
						if (spread.getSheetCount() > 1) {
							spread.removeSheet(spread.getActiveSheetIndex());
							delete template_define[spread.getActiveSheet().getName()];
							localStorage.setItem('template_define', JSON.stringify(template_define));
						}
					}
				},
					{text: _t("Cancel"), close: true}]
			};
			if (spread.getSheetCount() > 1) {
				Dialog.confirm(this, messae, options);
			} else if (spread.getSheetCount() == 1) {
				Dialog.confirm(this, "只有一个页签不允许删除操作！");
			}

		},

		// 样表列信息定义
		ColumnDefine: function(e) {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			let sheet = spread.getActiveSheet();
			let column_count = sheet.getColumnCount();
			let template_define = JSON.parse(localStorage.getItem('template_define'));

			if (!Object.keys(template_define).includes(sheet.getName())) {
				Dialog.confirm(this, "请配置Sheet属性。", {'title': "警告"});
				return;
			}

			let put_define = function() {
				let cols_info = [];
				for (let i = 0; i < column_count; i++) {
					cols_info.push({
						'col_index': this.$el.find("input[index='" + i + "']").val(),
						'col_type': this.$el.find("select[index='" + i + "']").val()
					});
				}
				template_define[sheet.getName()].cols_info = cols_info;
				localStorage.setItem('template_define', JSON.stringify(template_define));
			};

			if (Object.keys(template_define[sheet.getName()]).includes('cols_info')) {
				let infos = template_define[sheet.getName()].cols_info;

				// 对于初始未保存的Sheet，构建默认列信息
				if (infos.length === 0) {
					for (let i = 0; i < column_count; i++) {
						infos.push({
							'col_index': i
						});
					}
				}
				// Jax
				rpc.query({
					model:"ps.combined.statements.journaling.template.columntype",
					method: 'get_all_template_columntype',
				}).then(function(result) {
					if (result) {
						new Dialog(this, {
							title: "列定义",
							size: 'medium',
							buttons: [
								{
									text: _t("Save"),
									classes: 'btn-primary',
									close: true,
									click: put_define
								}, {
									text: _t("Cancel"),
									close: true
								}
							],
							$content: $(QWeb.render('JournalingColumnInfo', {widget: this, data: infos, o_items: result}))
						}).open();
					}
				});

				// new Model("ps.combined.statements.journaling.template.columntype").query(['name']).all().then(function(result) {
				// 	if (result) {
				// 		new Dialog(this, {
				// 			title: "列定义",
				// 			size: 'medium',
				// 			buttons: [
				// 				{
				// 					text: _t("Save"),
				// 					classes: 'btn-primary',
				// 					close: true,
				// 					click: put_define
				// 				}, {
				// 					text: _t("Cancel"),
				// 					close: true
				// 				}
				// 			],
				// 			$content: $(QWeb.render('JournalingColumnInfo', {widget: this, data: infos, o_items: result}))
				// 		}).open();
				// 	}
				// });
			}

		},

		// 保存模板
		Save_template_on_click: function() {
			let data = this.$el.find('#ss').data('spread');
			let spreadJSON = data.toJSON();
			let template_define = JSON.parse(localStorage.getItem('template_define'));
			let validate_rules = JSON.parse(localStorage.getItem('ValidateRules'));
			let save_template_func = function() {
				let template_name = this.$el.find("input[name='template_name']").val();
				let warning = this.$el.find('p');
				warning.hide();
				if (template_name === "" || template_name === undefined || template_name === null) {
					warning.html('请填写模板名称。').show();
					return false;
				} else if (jQuery.isEmptyObject(spreadJSON) || jQuery.isEmptyObject(template_define)) {
					warning.html("数据异常，请重新载入数据后重试。").show();
					return false;
				}

				let parameters = [];
				parameters.push(template_name);
				parameters.push(spreadJSON);
				parameters.push(template_define);
				parameters.push(validate_rules);
				// Jax
                rpc.query({
                    model: 'ps.combined.statements.project.template',
                    method: 'save_template',
                    args: [template_name,spreadJSON,template_define,validate_rules],
                    context: {},
                }).then(function (result) {
                    if (result) {
                        if (result) {
                            // alert(result);
                        }
                    }
                });
				// new Model('ps.combined.statements.project.template').call('save_template', parameters, {context: this.session.user_context || {}}).then(function(result) {
				// 	if (result) {
				// 		Dialog.confirm(this, result.message, {'title': "信息"});
				// 	}
				// });
			};

			new Dialog(this, {
				title: "保存模板",
				size: 'small',
				buttons: [
					{
						text: _t("Save"),
						classes: 'btn-primary',
						close: true,
						click: save_template_func
					}, {
						text: _t("Cancel"),
						close: true
					}
				],
				$content: $(QWeb.render('JournalingTemplateDialog', {widget: this}))
			}).open();

		},

		// 加载模板
		loadTemplateOnClick: function() {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			// Jax
            rpc.query({
					model:"ps.combined.statements.project.template",
					method: 'get_all_project_template',
				}).then(function(result) {
				if (result) {
					let dialog = new Dialog(this, {
						title: "加载模板",
						size: 'large',
						buttons: [{
							text: '关闭',
							classes: 'btn-primary',
							close: true
						}],
						$content: $(QWeb.render('JournalingTemplateLoadDialog', {Widget: this, data: result}))
					}).open();

					// 绑定按钮事件
					dialog.$content.on('click', 'button', function(e) {
						let id = e.currentTarget.parentElement.id;
						// Jax
						rpc.query({
							model:"ps.combined.statements.project.template",
							method: 'get_all_project_template_then',
							args: [id],
						}).then(function(res) {
							spread.clearSheets();
							spread.fromJSON(JSON.parse(res.data));
							localStorage.setItem('ValidateRules', res.validate_rules);
							localStorage.setItem('template_define', res.define_infos);
						}).then(function(){
							dialog.close();
						})
						// new Model('ps.combined.statements.project.template').query(['data','define_infos','validate_rules']).filter([['id', '=', id]]).first().then(function(res) {
						// 	spread.clearSheets();
						// 	spread.fromJSON(JSON.parse(res.data));
						// 	localStorage.setItem('ValidateRules', res.validate_rules);
						// 	localStorage.setItem('template_define', res.define_infos);
						// })
					});
				}
			});

			// new Model('ps.combined.statements.project.template').query(['name', 'storage_time']).filter().all().then(function(result) {
			// 	if (result) {
			// 		let dialog = new Dialog(this, {
			// 			title: "加载模板",
			// 			size: 'large',
			// 			buttons: [{
			// 				text: '关闭',
			// 				classes: 'btn-primary',
			// 				close: true
			// 			}],
			// 			$content: $(QWeb.render('JournalingTemplateLoadDialog', {Widget: this, data: result}))
			// 		}).open();
			//
			// 		// 绑定按钮事件
			// 		dialog.$content.on('click', 'button', function(e) {
			// 			let id = e.currentTarget.parentElement.id;
			// 			new Model('ps.combined.statements.project.template').query(['data','define_infos','validate_rules']).filter([['id', '=', id]]).first().then(function(res) {
			// 				spread.clearSheets();
			// 				spread.fromJSON(JSON.parse(res.data));
			// 				localStorage.setItem('ValidateRules', res.validate_rules);
			// 				localStorage.setItem('template_define', res.define_infos);
			// 			})
			// 		});
			// 	}
			// });

		},

		// 报表属性
		btnReportProperties_on_click: function(event) {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			let sheet = spread.getActiveSheet();
			let j_name = sheet.getName();
			// Jax
			// localStorage.removeItem('template_define');
			let template_define = JSON.parse(localStorage.getItem('template_define'));
			let result = {};
			if (template_define !== null) {
				result = Object.keys(template_define).includes(j_name) ? template_define[j_name] : undefined;
			}

			if (template_define === null) {
				let obj = {
					'name': sheet.getName(),
					'head_count': 0,
					'cols_info': [],
					'row_count': sheet.getRowCount(),
					'tail_count': 0,
					'col_offset': 0,
					'column_count': sheet.getColumnCount(),
					'uom': this.uom,
					'is_protected': false
				};
				template_define = {};
				template_define[j_name] = obj;
				result = obj;
			}

			let update = function() {
				let _name = this.$el.find("input[name='report_name']").val();
				let _head_count = this.$el.find("input[name='titlerows']").val();
				let _row_count = this.$el.find("input[name='rowcount']").val();
				let _tail_count = this.$el.find("input[name='tailrows']").val();
				let _col_offset = this.$el.find("input[name='coloffset']").val();
				let _uom = this.$el.find("select[name='uom'] option:selected").val();
				let _column_count = this.$el.find("input[name='columncount']").val();
				let _protected = this.$el.find("input[name='protected']").prop("checked");

				result['name'] = _name;
				result['head_count'] = parseInt(_head_count);
				result['row_count'] = parseInt(_row_count);
				result['tail_count'] = parseInt(_tail_count);
				result['col_offset'] = parseInt(_col_offset);
				result['column_count'] = parseInt(_column_count);
				result['uom'] = _uom;
				result['is_protected'] = _protected;

				if (sheet.getColumnCount() !== parseInt(_column_count)) {
					sheet.setColumnCount(parseInt(_column_count));
				}

				if (sheet.getRowCount() !== parseInt(_row_count)) {
					sheet.setRowCount(parseInt(_row_count));
				}

				sheet.setIsProtected(_protected);

				// 更新前端临时存储的数据
				if (!Object.keys(template_define).includes(_name)) {
					template_define[_name] = result;
				}
				sheet.setName(_name);
				localStorage.setItem('template_define', JSON.stringify(template_define));  // 更新缓存
			};

			new Dialog(this, {
				title: '报表属性',
				size: 'large',
				buttons: [
					{
						text: _t("Save"),
						classes: 'btn-primary',
						close: true,
						click: update
					}, {
						text: _t("Cancel"),
						close: true
					}
				],
				$content: $(QWeb.render('JournalingProperties', {widget: this, data: result}))
			}).open();
		},

		// 数据校验
		btnValidateRules_on_click: function() {

			let ValidateRules = JSON.parse(localStorage.getItem('ValidateRules'));

			// 重置序号
			function recalculate() {
				ValidateRules.forEach(function(value, index) {
					value.index = index + 1;
				});
				localStorage.setItem('ValidateRules', JSON.stringify(ValidateRules));
			}

			// 检查规则是否重复
			function exist(str) {
				let result = true;
				ValidateRules.forEach(function(val) {
					if (val.value === str) result = false;
				});
				return result;
			}

			let dialog = new Dialog(this, {
				title: '数据校验规则',
				size: 'medium',
				buttons: [
					{
						text: '增加',
						classes: 'btn-primary',
						close: false,
						click: function() {
							let _rule = this.$el.find("textarea[name='rule']").val();
							if (!_rule || !exist(_rule)) return;
							let lastRule = ValidateRules[ValidateRules.length - 1];
							let NewValidateRules = [{index: lastRule ? lastRule.index : 1, value: _rule}];
							let append_element = $(QWeb.render('ValidateRulesTableTr', {widget: this, data: NewValidateRules}));
							// let last_element = this.$el.find('tbody > tr:last-child');
							let tbody = this.$el.find('tbody');
							tbody.append(append_element);
							ValidateRules.push.apply(ValidateRules, NewValidateRules);
							recalculate();
						}
					}, {
						text: '保存',
						classes: 'btn-primary',
						close: true
					}
				],
				$content: $(QWeb.render('ValidateRulesDialog', {widget: this, data: ValidateRules}))
			}).open();

			// 绑定表格按钮事件
			dialog.$content.on('click', 'button', function(e) {
				let id = e.currentTarget.id;
				if (id === 'modify_validate_rule') {
					e.delegateTarget.getElementsByTagName('textarea')[0].value = e.currentTarget.parentNode.parentNode.children[1].innerText;
				}else if (id==='update_validate_rule') {
					let textarea = e.delegateTarget.getElementsByTagName('textarea')[0].value;
					if (!textarea) return;
					let index = e.currentTarget.parentElement.parentElement.rowIndex - 1;
					let rule = ValidateRules[index];
					rule.value = textarea;
					e.currentTarget.parentElement.parentElement.children[1].innerText = textarea;
					recalculate();
				} else {
					ValidateRules.splice(e.currentTarget.parentElement.parentElement.rowIndex - 1, 1);
//					ValidateRules.findIndex(value => value.index = e.currentTarget.parentElement.parentElement.rowIndex - 1);
					e.currentTarget.parentElement.parentElement.remove();
					recalculate();
				}
			});
		},

		// 打印
		print_on_click: function() {
			let spread = GcSpread.Sheets.findControl(document.getElementById('ss'));
			let sheet = spread.getActiveSheet();
			let printInfo = sheet.printInfo();
			printInfo.showRowHeader(GcSpread.Sheets.PrintVisibilityType.Show);
			printInfo.showColumnHeader(GcSpread.Sheets.PrintVisibilityType.Show);
			spread.print(spread.getActiveSheetIndex());
		}

	});

	core.action_registry.add('journaling.design', CombinedStatementsJournaling);
	return CombinedStatementsJournaling;
});
