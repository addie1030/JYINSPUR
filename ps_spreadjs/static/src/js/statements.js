odoo.define('statements_sheet',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var _t = core._t;
    var framework = require('web.framework');
    var crash_manager = require('web.crash_manager');
    var localStorage = require('web.local_storage');
    var HomePage=AbstractAction.extend({
        template: 'statements_template',
        //初始化实例
        init: function(parent,context){
            console.log(context)
            this._super(parent,context);
            this.name="statements";
            this.isnew = context.context.isnew;//是否新建报表
            this.code = context.context.report_code;//报表编号
            this.sheetname = context.context.report_name;//报表名称
            this.date = context.context.report_date;//报表日期
            this.category = context.context.category;//编报时间
            this.titlerows = context.context.titlerows;//标题行数
            this.headrows = context.context.headrows;//表头行数
            this.bodyrows = context.context.bodyrows;//表体行数
            this.tailrows = context.context.tailrows;//表尾行数
            this.bodycols = context.context.bodycols;//列数

            this.cellinfos = [];   //单元格信息
            this.defineformulas = [];
            this.insertrows = [];
            this.insertcols = [];
            this.deleterows = [];
            this.deletecols = [];
            this.colsproperties = [];

            if (this.code == undefined || this.sheetname == undefined || this.date == undefined)
            {
                this.code = localStorage.getItem('code');
                this.sheetname = localStorage.getItem('sheetname');
                this.date = localStorage.getItem('date');
            }
            else{
                localStorage.setItem('code', this.code );
                localStorage.setItem('sheetname', this.sheetname );
                localStorage.setItem('date', this.date );
            }
        },
        //事件声明
        events:{
            //报表操作
            'click button#btnPrint': 'print',//菜单-报表打印
            'click button#btnCalculate': 'calculate',//菜单-报表计算
            'click button#btnSave': 'save',//菜单-报表保存
            'click button#btnExport': 'export',//菜单-转出格式
            'click button#btnImport': 'import',//菜单-转入格式
            'click button#btnOutput': 'output',//菜单-导出数据
            // 'click button#btnInput': 'input',
            // 'click button#btnMonthEnd': 'monthend',//菜单-月末存档
            'click button#btnFormula': 'formulastate',//菜单-公式状态
            'click button#btnReplace': 'replaceformula',//菜单-公式替换
            'click button#btnPivotDefine': 'pivotdefine',//菜单-数据透视定义
            'click button#btnPivot': 'pivot',//菜单-数据透视
            'click button#btnMonetaryUnitAdjust': 'monetaryunitadjust',//菜单-金额单位调整
            'click button#btnReportProperties':'reportproperties',//菜单-报表属性
            //格式操作
            'click button#btnFontSet':'fontset',//菜单-字体
            'click button#btnFontBold': 'fontbold',//菜单-粗体
            'click button#btnFontItalic': 'fontitalic',//菜单-斜体
            'click button#btnCopy': 'copyt',//菜单-复制
            'click button#btnCut': 'cutt',//菜单-剪切
            'click button#btnPaste': 'pastet',//菜单-粘贴
            'click button#btnUndo': 'undo',//菜单-撤销
            'click button#btnRedo': 'redo',//菜单-恢复
            'click button#btnMerge': 'mergecell',//菜单-合并后居中
            'click button#btnMergeCellNoAlign': 'merge',//菜单-合并单元格
            'click button#btnDeleteSpan': 'deletespan',//菜单-取消合并
            'click button#btnBorderLine': 'borderline',//菜单-全边框
            'click button#btnBorderLeft': 'borderleft',//菜单-左边框
            'click button#btnBorderRight': 'borderright',//菜单-右边框
            'click button#btnBorderTop': 'bordertop',//菜单-上边框
            'click button#btnBorderBottom': 'borderbottom',//菜单-下边框
            'click button#btnBorderInside': 'borderinside',//菜单-内边框
            'click button#btnBorderOutline': 'borderoutline',//菜单-外边框
            'click button#btnTxtUnderline': 'textdecorationunderline',//菜单-下划线
            'click button#btnTxtLineThrough': 'textdecorationlinethrough',//菜单-删除线
            // 'click button#btnCldecoration':'cleardecoration',//菜单-复制
            'click button#btnLeftAlign':'leftalign',//菜单-水平左对齐
            'click button#btnCenterAlign':'centeralign',//菜单-水平居中对齐
            'click button#btnRightAlign':'rightalign',//菜单-水平右对齐
            'click button#btnVLeft':'vleft',//菜单-垂直上对齐
            'click button#btnVCenter':'vcenter',//菜单-垂直居中对齐
            'click button#btnVRight':'vright',//菜单-垂直下对齐
            'click button#btnInsertRow': 'insertrow',//菜单-插入行
            'click button#btnDeleteRow': 'deleterow',//菜单-删除行
            'click button#btnShowR':'showrow',//菜单-显示行
            'click button#btnHideR':'hiderow',//菜单-隐藏行
            'click button#btnInsertCol': 'insertcol',//菜单-插入列
            'click button#btnDeleteCol': 'deletecol',//菜单-删除列
            //右键操作
            'click a#cut': 'cut',//右键-剪切
            'click a#copy': 'copy',//右键-复制
            'click a#paste': 'paste',//右键-粘贴
            'click a#merge': 'merge',//右键-合并单元格
            'click a#unmerge': 'unmerge',//右键-取消合并
            'click a#cleardata': 'cleardata',//右键-清除内容
            'click a#clearformula': 'clearformula',//右键-清除公式
            'click a#clearstyle': 'clearstyle',//右键-清除格式
            'click a#clearall': 'clearall',//右键-全部清除
            'click a#insertrow': 'insertrow',//右键-插入行
            'click a#insertcol': 'insertcol',//右键-插入列
            'click a#deleterow': 'deleterow',//右键-删除行
            'click a#deletecol': 'deletecol',//右键-删除列
            'click a#calculateselectedrange': 'calculateselectedrange',//右键-计算选中区域
            'click a#celldatacomposition': 'celldatacomposition',//右键-单元格数据构成
            //公式状态操作
            'click button#btnNewFormula': 'newformula',//公式状态-新增公式
            'click button#btnSaveFormula': 'saveformula',//公式状态-保存公式
            'click button#btnDeleteFormula': 'deleteformula',//公式状态-删除公式
            'keydown .inputformula': "inputformulakeydown",//公式状态-公式编辑回车
            'click button#btnReplaceFormula': 'replaceformulaatformulastate',//公式状态-公式替换
            //其他操作
            'change .date_change': 'datechange',//改变会计区间
            'click button#btnFormulaGuide': 'rightmenu_formula_guide',//公式定义向导
            'keydown .formulaBar': "formulaeditkeydown",//公式栏回车
        },
        //自动调用
        start: function(){
            var fiscaldate = this.date;
            var self = this;

            //新建报表
            if (self.isnew == "1")
            {
                var company = "my company";
                var defcompany = this._rpc({model: 'ps.statement.statements',method: 'get_statement_company',args: []}).then(function (result)
                {
                    if (result)
                    {
                        company = result;
                    }
                });
                var defstart = this._rpc({model: 'ps.statement.statements',method: 'get_statement',args: [self.code,self.date]}).then(function (result)
                {
                    // self.cellinfos = result[1];
                    // self.colsproperties = result[3];
                    if (result[0].length == 0)
                    {
                        var spread = new GcSpread.Sheets.Spread(document.getElementById('statements_sheet'), {sheetCount: 1});
                        spread.isPaintSuspended(true);
                        var sheet = spread.getActiveSheet();
                        sheet.setRowCount(parseInt(self.titlerows)+parseInt(self.headrows)+parseInt(self.bodyrows)+parseInt(self.tailrows));
                        sheet.setColumnCount(parseInt(self.bodycols));
                        sheet.setName(self.sheetname);
                        sheet.addSpan(0, 0, 1, parseInt(self.bodycols));
                        sheet.setRowHeight(0, 50);
                        sheet.getCells(0, 0, 0, parseInt(self.bodycols)).text(self.sheetname).font("24pt Calibri").textIndent(4);
                        sheet.getCells(0, 0, 0, parseInt(self.bodycols)).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                        sheet.getCells(0, 0, 0, parseInt(self.bodycols)).vAlign(GcSpread.Sheets.VerticalAlign.center);
                        sheet.setColumnWidth(0, 160);
                        sheet.setColumnWidth(parseInt(self.bodycols)/2, 100);
                        sheet.setColumnWidth(parseInt(self.bodycols)-1, 160);
                        sheet.getCell(1, parseInt(self.bodycols)-1).text("会小企01表");
                        sheet.getCell(1, parseInt(self.bodycols)-1).hAlign(GcSpread.Sheets.HorizontalAlign.right);
                        sheet.getCell(2, 0).text("单位名称："+company);
                        sheet.getCell(2, parseInt(self.bodycols)/2).text(fiscaldate.substring(0,4)+"年"+fiscaldate.substring(4,6)+"月");
                        sheet.getCell(2, parseInt(self.bodycols)-1).text("金额单位：元");
                        sheet.getCell(2, parseInt(self.bodycols)-1).hAlign(GcSpread.Sheets.HorizontalAlign.right);

                        sheet.getCells(4,1,33,9).formatter("#,##0.00;[Red]#,##0.00");
                        var range = new GcSpread.Sheets.Range(parseInt(self.titlerows)+parseInt(self.headrows) - 1, 0, 1, parseInt(self.titlerows)+parseInt(self.headrows)+parseInt(self.bodyrows)+parseInt(self.tailrows));
                        sheet.setBorder(range,new GcSpread.Sheets.LineBorder("Black", GcSpread.Sheets.LineStyle.medium), {
                            all: true
                        });
                        var range1 = new GcSpread.Sheets.Range(parseInt(self.titlerows)+parseInt(self.headrows), 0, parseInt(self.bodyrows), parseInt(self.bodycols));
                        sheet.setBorder(range1,new GcSpread.Sheets.LineBorder("Black", GcSpread.Sheets.LineStyle.thin), {
                            all: true
                        });
                        spread.isPaintSuspended(false);
                        spread.newTabVisible(false);

                        //获取单元格信息
                        var activeSheet = spread.getSheet(0);
                        var celldatasets = [];
                        var row = 0;
                        var col = 0;

                        //增加tips
                        var TipCellType = function () {};
                        TipCellType.prototype = new GcSpread.Sheets.TextCellType();
                        TipCellType.prototype.getHitInfo = function (x, y, cellStyle, cellRect, context) {
                            return {
                                x: x,
                                y: y,
                                row: context.row,
                                col: context.col,
                                cellStyle: cellStyle,
                                cellRect: cellRect,
                                sheetArea: context.sheetArea
                            };
                        };
                        TipCellType.prototype.processMouseEnter = function (hitinfo)
                        {
                            if (!this._toolTipElement)
                            {
                                var div = document.createElement("div");
                                $(div).css("position", "absolute")
                                .css("border", "1px #C0C0C0 solid")
                                .css("box-shadow", "1px 2px 5px rgba(0,0,0,0.4)")
                                .css("font", "9pt Arial")
                                .css("background", "white")
                                .css("padding", 5);

                                this._toolTipElement = div;
                            }
                            var formula = "";
                            var row = 0;
                            var col = 0;
                            var rowoffset = 0;
                            var coloffset = 0;
                            var rangerow = 0;
                            var rangecol = 0;
                            if(self.cellinfos == undefined || self.cellinfos == null)
                            {
                                $(this._toolTipElement).text("")
                                .css("top", hitinfo.y + 150)
                                .css("left", hitinfo.x - 20);
                                $(this._toolTipElement).hide();
                                document.body.insertBefore(this._toolTipElement, null);
                                $(this._toolTipElement).show("fast");
                                return;
                            }
                            for (var cellline = 0; cellline < self.cellinfos.length; cellline++)
                            {
                                row = self.cellinfos[cellline]["row"];
                                col = self.cellinfos[cellline]["col"];
                                rowoffset = self.cellinfos[cellline]["rowoffset"];
                                coloffset = self.cellinfos[cellline]["coloffset"];

                                if (rowoffset > 0 || coloffset > 0)
                                {
                                    if ((hitinfo.row >= parseInt(row) && hitinfo.row <= parseInt(row) + rowoffset) && (hitinfo.col >= parseInt(col) && hitinfo.col <= parseInt(col) + coloffset))
                                    {
                                        formula = self.cellinfos[cellline]["formula"];
                                        if (formula.length > 0)
                                        {
                                            if (formula.indexOf("=") != 0)
                                            {
                                                formula = "=" + formula;
                                            }
                                            rangerow = parseInt(row);
                                            rangecol = parseInt(col);
                                            break;
                                        }
                                    }
                                }
                                else
                                {
                                    if (hitinfo.row == parseInt(row) && hitinfo.col == parseInt(col) )
                                    {
                                        formula = self.cellinfos[cellline]["formula"];
                                        if (formula.length > 0)
                                        {
                                            if (formula.indexOf("=") != 0)
                                            {
                                                formula = "=" + formula;
                                            }
                                            rangerow = parseInt(row);
                                            rangecol = parseInt(col);
                                            break;
                                        }
                                    }
                                }
                            }

                            var text = "";
                            if (formula.length > 0)
                            {
                                var startrow = 0;
                                var startcol = 0;
                                var endrow = 0;
                                var endcol = 0;

                                startrow = rangerow + 1;
                                startcol = rangecol;
                                endrow = rangerow + rowoffset + 1;
                                endcol = rangecol + coloffset;

                                var s = "";
                                var e = "";
                                var colcoordinate = activeSheet.getText(0, startcol,GcSpread.Sheets.SheetArea.colHeader);
                                s = colcoordinate+startrow;
                                var colcoordinate = activeSheet.getText(0, endcol,GcSpread.Sheets.SheetArea.colHeader);
                                e = colcoordinate+endrow;

                                if(rowoffset > 0 || coloffset > 0)
                                {
                                    text = "作用范围["+s+":"+e+"]\n区域公式["+formula+"]"
                                }
                                else
                                {
                                    text = "作用范围["+s+":"+e+"]\n单元公式["+formula+"]"
                                }
                                $(this._toolTipElement).text(text)
                                .css("top", hitinfo.y + 150)
                                .css("left", hitinfo.x - 20);
                                $(this._toolTipElement).hide();
                                document.body.insertBefore(this._toolTipElement, null);
                                $(this._toolTipElement).show("fast");
                            }
                            else {
                                text = activeSheet.getValue(hitinfo.row,hitinfo.col);
                                $(this._toolTipElement).text(text)
                                .css("top", hitinfo.y + 150)
                                .css("left", hitinfo.x - 20);
                                $(this._toolTipElement).hide();
                                document.body.insertBefore(this._toolTipElement, null);
                                if(text)
                                {
                                    $(this._toolTipElement).show("fast");
                                }
                            }
                        };
                        TipCellType.prototype.processMouseLeave = function (hitinfo) {
                            if (this._toolTipElement) {
                                document.body.removeChild(this._toolTipElement);
                                this._toolTipElement = null;
                            }
                        };

                        var defaultStyle = activeSheet.getDefaultStyle();
                        defaultStyle.cellType = new TipCellType();
                        activeSheet.setDefaultStyle(defaultStyle);

                        activeSheet.bind(GcSpread.Sheets.Events.CellClick, function (sender, args)
                        {
                            celldatasets = self.cellinfos;
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.colHeader)
                            {
                            }
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader)
                            {
                            }
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.corner)
                            {
                            }
                            var rowid = args.row;
                            var colid = args.col;

                            var existformula = false;
                            for(var cellline = 0;cellline < celldatasets.length;cellline++)
                            {
                                var formula = "";
                                row = celldatasets[cellline]["row"];
                                col = celldatasets[cellline]["col"];
                                if (row == String(rowid) && col == String(colid))
                                {
                                    formula = celldatasets[cellline]["formula"];

                                    if (formula.length > 0)
                                    {
                                        if (formula.indexOf("=") != 0)
                                        {
                                            formula = "=" + formula;
                                        }
                                    }

                                    var formulaBar = document.getElementById('formulaBar');
                                    formulaBar.innerHTML = formula;
                                    existformula = true;
                                    break;
                                }
                            }

                            if(!existformula)
                            {
                                var formulaBar = document.getElementById('formulaBar');
                                if(formulaBar.innerHTML.length > 0)
                                {
                                    formulaBar.innerHTML = "";
                                }
                            }
                        });

                        activeSheet.bind(GcSpread.Sheets.Events.CellDoubleClick, function (sender, args)
                        {
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.colHeader)
                            {
                            }
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader)
                            {
                            }
                            if(args.sheetArea === GcSpread.Sheets.SheetArea.corner)
                            {
                            }
                        });
                    };
                    if(result[1] == null || result[1] == undefined || result[1].length == 0)
                    {
                        var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                        var activeSheet = spreadtemp.getSheet(0);
                        for (var i = 0; i < activeSheet.getRowCount(); i++)
                        {
                            for (var j = 0; j < activeSheet.getColumnCount(); j++)
                            {
                                var data = activeSheet.getValue(i, j);
                                if (data == "" || data == undefined || data == null)
                                {
                                    data = 0;
                                }

                                var celldata = {};
                                celldata["row"] = String(i);
                                celldata["col"] = String(j);
                                celldata["rowoffset"] = 0;
                                celldata["coloffset"] = 0;
                                celldata["data"] = data;
                                celldata["text"] = "";
                                celldata["formula"] = "";                   //四则运算的整体公式
                                celldata["formulaitems"] = [];              //四则运算的分解公式
                                celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                celldata["formulaoperators"] = [];          //四则运算的运算符
                                celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                celldata["newformula"] = "0";               //新增公式
                                self.cellinfos.push(celldata);
                            }
                        }
                    }
                    else
                    {
                        self.cellinfos = result[1]
                    }

                    if(result[3] == null || result[3] == undefined || result[3].length == 0)
                    {
                        var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                        var activeSheet = spreadtemp.getSheet(0);
                        for (var i = 0; i < activeSheet.getColumnCount(); i++)
                        {
                            self.colsproperties.push({"report_code":self.code,
                                                    "report_date":self.date,
                                                    "col_name":"",
                                                    "col_order":i,
                                                    "col_coordinate":i,
                                                    "col_isnumber":'0',
                                                    "col_isamount":'0',
                                                    "col_isadjust":'0',
                                                    "col_isitem":'0',
                                                    });
                        }
                    }
                    else
                    {
                        self.colsproperties = result[3]
                    }

                    var setctions = document.querySelectorAll("section");
                    setctions[0].childNodes[3].value = fiscaldate.substring(0,4)+"-"+fiscaldate.substring(4,6);
                    var h2s = document.querySelectorAll("h2");
                    h2s[0].innerText = self.sheetname;
                });
            }
            else {
                //默认报表
                if (this.date == "" || this.date == undefined || this.date == null || this.date == "000000")
                {
                    var date = new Date();
                    var month = date.getMonth() + 1;
                    // var self = this;
                    if (month >= 1 && month <= 9) {
                        month = "0" + month;
                    }
                    var currentdate = date.getFullYear() + month;
                    var deffiscal = this._rpc({
                        model: 'ps.statement.statements',
                        method: 'get_fiscalperiod'
                    }).then(function (result)
                    {
                        if (result)
                        {
                            currentdate = result;
                            document.getElementById('user_date').value = currentdate.substring(0, 4) + "-" + currentdate.substring(4, 6);
                        }
                        else {
                            alert('没有找到对应的会计期间，请首先到财务会计中维护会计期间！');
                            self.do_action({
                                name: '财务报表',
                                type: 'ir.actions.act_window',
                                res_model: 'ps.statement.statements',
                                views: [[false, 'list']],
                                view_type: 'list',
                                view_mode: 'list',
                                target: 'current',
                            });

                            return;
                        }
                    }).then(function (result) {
                        var defstart = self._rpc({
                            model: 'ps.statement.statements',
                            method: 'get_statement',
                            args: [self.code, currentdate]
                        }).then(function (result)
                        {
                            // if (result)
                            // {
                            //     var jsonStr = result[0];
                            //     var jsonOptions = {
                            //         ignoreFormula: false, // indicate to ignore style when convert json to workbook, default value is false
                            //         ignoreStyle: false, // indicate to ignore the formula when convert json to workbook, default value is false
                            //         frozenColumnsAsRowHeaders: false, // indicate to treat the frozen columns as row headers when convert json to workbook, default value is false
                            //         frozenRowsAsColumnHeaders: false, // indicate to treat the frozen rows as column headers when convert json to workbook, default value is false
                            //         doNotRecalculateAfterLoad: false //  indicate to forbid recalculate after load the json, default value is false
                            //     };
                            //
                            //     var spread = new GcSpread.Sheets.Spread(document.getElementById('statements_sheet'), {sheetCount: 1});
                            //     spread.isPaintSuspended(true);
                            //     spread.fromJSON(JSON.parse(jsonStr), jsonOptions);
                            //     spread.isPaintSuspended(false);
                            //     spread.newTabVisible(false);
                            //     var activeSheet = spread.getSheet(0);
                            //
                            //     if (result[2] == "1") {
                            //         activeSheet.setIsProtected(true);
                            //         $("#btnCalculate").attr("disabled", true);
                            //         $("#btnInsertRow").attr("disabled", true);
                            //         $("#btnInsertCol").attr("disabled", true);
                            //         $("#btnDeleteRow").attr("disabled", true);
                            //         $("#btnDeleteCol").attr("disabled", true);
                            //         $("#btnReplace").attr("disabled", true);
                            //         $("#btnNewFormula").attr("disabled", true);
                            //         $("#btnDeleteFormula").attr("disabled", true);
                            //         $("#btnReplaceFormula").attr("disabled", true);
                            //         $("#btnFormulaGuide").attr("disabled", true);
                            //         $("#formulaBar").attr("contenteditable", false);
                            //     }
                            //     //获取单元格信息
                            //     var celldatasets = result[1];//所有单元格的信息
                            //     var row1 = 0;
                            //     var col1 = 0;
                            //     var row2 = 0;
                            //     var col2 = 0;
                            //
                            //     var cellinfos = [];
                            //     for (var i = 0; i < activeSheet.getRowCount(); i++)
                            //     {
                            //         for (var j = 0; j < activeSheet.getColumnCount(); j++) {
                            //             var data = activeSheet.getValue(i, j);
                            //             if (data == "" || data == undefined || data == null) {
                            //                 data = 0;
                            //             }
                            //
                            //             var celldata = {};
                            //             celldata["row"] = String(i);
                            //             celldata["col"] = String(j);
                            //             celldata["rowoffset"] = 0;
                            //             celldata["coloffset"] = 0;
                            //             celldata["data"] = data;
                            //             celldata["text"] = "";
                            //             celldata["formula"] = "";                   //四则运算的整体公式
                            //             celldata["formulaitems"] = [];              //四则运算的分解公式
                            //             celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                            //             celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                            //             celldata["formulaoperators"] = [];          //四则运算的运算符
                            //             celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                            //             celldata["newformula"] = "0";               //新增公式
                            //             cellinfos.push(celldata);
                            //         }
                            //     }
                            //
                            //     for (var cellline1 = 0; cellline1 < cellinfos.length; cellline1++) {
                            //         row1 = cellinfos[cellline1]["row"];
                            //         col1 = cellinfos[cellline1]["col"];
                            //         for (var cellline2 = 0; cellline2 < celldatasets.length; cellline2++) {
                            //             row2 = celldatasets[cellline2]["row"];
                            //             col2 = celldatasets[cellline2]["col"];
                            //
                            //             if (row1 == row2 && col1 == col2) {
                            //                 cellinfos[cellline1]["rowoffset"] = celldatasets[cellline2]["rowoffset"];
                            //                 cellinfos[cellline1]["coloffset"] = celldatasets[cellline2]["coloffset"];
                            //                 cellinfos[cellline1]["formula"] = celldatasets[cellline2]["formula"];                   //四则运算的整体公式
                            //                 cellinfos[cellline1]["formulaitems"] = celldatasets[cellline2]["formulaitems"];              //四则运算的分解公式
                            //                 cellinfos[cellline1]["formulaitemsbak"] = celldatasets[cellline2]["formulaitemsbak"];           //四则运算的分解公式备份
                            //                 cellinfos[cellline1]["formulaitemsvalue"] = celldatasets[cellline2]["formulaitemsvalue"];         //四则运算的分解公式的值
                            //                 cellinfos[cellline1]["formulaoperators"] = celldatasets[cellline2]["formulaoperators"];          //四则运算的运算符
                            //                 cellinfos[cellline1]["formulaitemscalculated"] = celldatasets[cellline2]["formulaitemscalculated"];    //四则运算的分解公式是否已经计算
                            //             }
                            //         }
                            //     }
                            //
                            //     self.cellinfos = cellinfos;
                            //     self.colsproperties = result[3];
                            //     //增加tips
                            //     var TipCellType = function () {};
                            //     TipCellType.prototype = new GcSpread.Sheets.TextCellType();
                            //     TipCellType.prototype.getHitInfo = function (x, y, cellStyle, cellRect, context) {
                            //         return {
                            //             x: x,
                            //             y: y,
                            //             row: context.row,
                            //             col: context.col,
                            //             cellStyle: cellStyle,
                            //             cellRect: cellRect,
                            //             sheetArea: context.sheetArea
                            //         };
                            //     };
                            //     TipCellType.prototype.processMouseEnter = function (hitinfo)
                            //     {
                            //         if (!this._toolTipElement)
                            //         {
                            //             var div = document.createElement("div");
                            //             $(div).css("position", "absolute")
                            //             .css("border", "1px #C0C0C0 solid")
                            //             .css("box-shadow", "1px 2px 5px rgba(0,0,0,0.4)")
                            //             .css("font", "9pt Arial")
                            //             .css("background", "white")
                            //             .css("padding", 5);
                            //
                            //             this._toolTipElement = div;
                            //         }
                            //         var formula = "";
                            //         var row = 0;
                            //         var col = 0;
                            //         var rowoffset = 0;
                            //         var coloffset = 0;
                            //         var rangerow = 0;
                            //         var rangecol = 0;
                            //         if(self.cellinfos == undefined || self.cellinfos == null)
                            //         {
                            //             $(this._toolTipElement).text("")
                            //             .css("top", hitinfo.y + 150)
                            //             .css("left", hitinfo.x - 20);
                            //             $(this._toolTipElement).hide();
                            //             document.body.insertBefore(this._toolTipElement, null);
                            //             $(this._toolTipElement).show("fast");
                            //             return;
                            //         }
                            //         for (var cellline = 0; cellline < self.cellinfos.length; cellline++)
                            //         {
                            //             row = self.cellinfos[cellline]["row"];
                            //             col = self.cellinfos[cellline]["col"];
                            //             rowoffset = self.cellinfos[cellline]["rowoffset"];
                            //             coloffset = self.cellinfos[cellline]["coloffset"];
                            //
                            //             if (rowoffset > 0 || coloffset > 0)
                            //             {
                            //                 if ((hitinfo.row >= parseInt(row) && hitinfo.row <= parseInt(row) + rowoffset) && (hitinfo.col >= parseInt(col) && hitinfo.col <= parseInt(col) + coloffset))
                            //                 {
                            //                     formula = self.cellinfos[cellline]["formula"];
                            //                     if (formula.length > 0)
                            //                     {
                            //                         if (formula.indexOf("=") != 0)
                            //                         {
                            //                             formula = "=" + formula;
                            //                         }
                            //                         rangerow = parseInt(row);
                            //                         rangecol = parseInt(col);
                            //                         break;
                            //                     }
                            //                 }
                            //             }
                            //             else
                            //             {
                            //                 if (hitinfo.row == parseInt(row) && hitinfo.col == parseInt(col) )
                            //                 {
                            //                     formula = self.cellinfos[cellline]["formula"];
                            //                     if (formula.length > 0)
                            //                     {
                            //                         if (formula.indexOf("=") != 0)
                            //                         {
                            //                             formula = "=" + formula;
                            //                         }
                            //                         rangerow = parseInt(row);
                            //                         rangecol = parseInt(col);
                            //                         break;
                            //                     }
                            //                 }
                            //             }
                            //         }
                            //
                            //         var text = "";
                            //         if (formula.length > 0)
                            //         {
                            //             var startrow = 0;
                            //             var startcol = 0;
                            //             var endrow = 0;
                            //             var endcol = 0;
                            //
                            //             startrow = rangerow + 1;
                            //             startcol = rangecol;
                            //             endrow = rangerow + rowoffset + 1;
                            //             endcol = rangecol + coloffset;
                            //
                            //             var s = "";
                            //             var e = "";
                            //             var colcoordinate = activeSheet.getText(0, startcol,GcSpread.Sheets.SheetArea.colHeader);
                            //             s = colcoordinate+startrow;
                            //             var colcoordinate = activeSheet.getText(0, endcol,GcSpread.Sheets.SheetArea.colHeader);
                            //             e = colcoordinate+endrow;
                            //
                            //             if(rowoffset > 0 || coloffset > 0)
                            //             {
                            //                 text = "作用范围["+s+":"+e+"]\n区域公式["+formula+"]"
                            //             }
                            //             else
                            //             {
                            //                 text = "作用范围["+s+":"+e+"]\n单元公式["+formula+"]"
                            //             }
                            //             $(this._toolTipElement).text(text)
                            //             .css("top", hitinfo.y + 150)
                            //             .css("left", hitinfo.x - 20);
                            //             $(this._toolTipElement).hide();
                            //             document.body.insertBefore(this._toolTipElement, null);
                            //             $(this._toolTipElement).show("fast");
                            //         }
                            //         else {
                            //             text = activeSheet.getValue(hitinfo.row,hitinfo.col);
                            //             $(this._toolTipElement).text(text)
                            //             .css("top", hitinfo.y + 150)
                            //             .css("left", hitinfo.x - 20);
                            //             $(this._toolTipElement).hide();
                            //             document.body.insertBefore(this._toolTipElement, null);
                            //             if(text)
                            //             {
                            //                 $(this._toolTipElement).show("fast");
                            //             }
                            //         }
                            //     };
                            //     TipCellType.prototype.processMouseLeave = function (hitinfo) {
                            //         if (this._toolTipElement) {
                            //             document.body.removeChild(this._toolTipElement);
                            //             this._toolTipElement = null;
                            //         }
                            //     };
                            //
                            //     var defaultStyle = activeSheet.getDefaultStyle();
                            //     defaultStyle.cellType = new TipCellType();
                            //     activeSheet.setDefaultStyle(defaultStyle);
                            //
                            //     activeSheet.bind(GcSpread.Sheets.Events.CellClick, function (sender, args) {
                            //         celldatasets = self.cellinfos;
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader)
                            //         {
                            //         }
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader)
                            //         {
                            //         }
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.corner)
                            //         {
                            //         }
                            //
                            //         var rowid = args.row;
                            //         var colid = args.col;
                            //
                            //         var existformula = false;
                            //         var row = 0;
                            //         var col = 0;
                            //         for (var cellline = 0; cellline < celldatasets.length; cellline++) {
                            //             var formula = "";
                            //             row = celldatasets[cellline]["row"];
                            //             col = celldatasets[cellline]["col"];
                            //             if (row == String(rowid) && col == String(colid)) {
                            //                 formula = celldatasets[cellline]["formula"];
                            //
                            //                 if (formula.length > 0) {
                            //                     if (formula.indexOf("=") != 0) {
                            //                         formula = "=" + formula;
                            //                     }
                            //                 }
                            //
                            //                 var formulaBar = document.getElementById('formulaBar');
                            //                 formulaBar.innerHTML = formula;
                            //                 existformula = true;
                            //                 break;
                            //             }
                            //         }
                            //
                            //         if (!existformula) {
                            //             var formulaBar = document.getElementById('formulaBar');
                            //             if (formulaBar.innerHTML.length > 0) {
                            //                 formulaBar.innerHTML = "";
                            //             }
                            //         }
                            //     });
                            //
                            //     activeSheet.bind(GcSpread.Sheets.Events.CellDoubleClick, function (sender, args) {
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader)
                            //         {
                            //         }
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader)
                            //         {
                            //         }
                            //         if (args.sheetArea === GcSpread.Sheets.SheetArea.corner)
                            //         {
                            //         }
                            //     });
                            // }
                        });
                    });
                }
                else {
                    //选中报表
                    var defstart = this._rpc({
                        model: 'ps.statement.statements',
                        method: 'get_statement',
                        args: [this.code, this.date]
                    }).then(function (result) {
                        if (result)
                        {
                            var jsonStr = result[0];
                            var jsonOptions = {
                                ignoreFormula: false, // indicate to ignore style when convert json to workbook, default value is false
                                ignoreStyle: false, // indicate to ignore the formula when convert json to workbook, default value is false
                                frozenColumnsAsRowHeaders: false, // indicate to treat the frozen columns as row headers when convert json to workbook, default value is false
                                frozenRowsAsColumnHeaders: false, // indicate to treat the frozen rows as column headers when convert json to workbook, default value is false
                                doNotRecalculateAfterLoad: false //  indicate to forbid recalculate after load the json, default value is false
                            };

                            var spread = new GcSpread.Sheets.Spread(document.getElementById('statements_sheet'), {sheetCount: 1});
                            spread.fromJSON(JSON.parse(jsonStr), jsonOptions);
                            spread.newTabVisible(false);

                            var activeSheet = spread.getSheet(0);

                            if (result[2] == "1")
                            {
                                activeSheet.setIsProtected(true);
                                $("#btnCalculate").attr("disabled", true);
                                $("#btnInsertRow").attr("disabled", true);
                                $("#btnInsertCol").attr("disabled", true);
                                $("#btnDeleteRow").attr("disabled", true);
                                $("#btnDeleteCol").attr("disabled", true);
                                $("#btnReplace").attr("disabled", true);
                                $("#btnNewFormula").attr("disabled", true);
                                $("#btnDeleteFormula").attr("disabled", true);
                                $("#btnReplaceFormula").attr("disabled", true);
                                $("#btnFormulaGuide").attr("disabled", true);
                                $("#formulaBar").attr("contenteditable", false);
                            }

                            //获取单元格信息
                            var celldatasets = result[1];//所有单元格的信息
                            var row1 = 0;
                            var col1 = 0;
                            var row2 = 0;
                            var col2 = 0;

                            var cellinfosbak = [];
                            for (var i = 0; i < activeSheet.getRowCount(); i++)
                            {
                                for (var j = 0; j < activeSheet.getColumnCount(); j++)
                                {
                                    var data = activeSheet.getValue(i, j);
                                    var text = "";
                                    if (data == "" || data == undefined || data == null)
                                    {
                                        data = 0;
                                    }

                                    if (isNaN(data))
                                    {
                                        text = data;
                                        data = 0;
                                    }

                                    var celldata = {};
                                    celldata["row"] = String(i);
                                    celldata["col"] = String(j);
                                    celldata["rowoffset"] = 0;
                                    celldata["coloffset"] = 0;
                                    celldata["data"] = data;
                                    celldata["text"] = text;
                                    celldata["formula"] = "";                   //四则运算的整体公式
                                    celldata["formulaitems"] = [];              //四则运算的分解公式
                                    celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                    celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                    celldata["formulaoperators"] = [];          //四则运算的运算符
                                    celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                    celldata["newformula"] = "0";               //新增公式
                                    cellinfosbak.push(celldata);
                                }
                            }
                            for (var cellline1 = 0; cellline1 < cellinfosbak.length; cellline1++)
                            {
                                row1 = cellinfosbak[cellline1]["row"];
                                col1 = cellinfosbak[cellline1]["col"];
                                for (var cellline2 = 0; cellline2 < celldatasets.length; cellline2++)
                                {
                                    row2 = celldatasets[cellline2]["row"];
                                    col2 = celldatasets[cellline2]["col"];

                                    if (row1 == row2 && col1 == col2) {
                                        cellinfosbak[cellline1]["rowoffset"] = celldatasets[cellline2]["rowoffset"];
                                        cellinfosbak[cellline1]["coloffset"] = celldatasets[cellline2]["coloffset"];
                                        cellinfosbak[cellline1]["formula"] = celldatasets[cellline2]["formula"];                   //四则运算的整体公式
                                        cellinfosbak[cellline1]["formulaitems"] = celldatasets[cellline2]["formulaitems"];              //四则运算的分解公式
                                        cellinfosbak[cellline1]["formulaitemsbak"] = celldatasets[cellline2]["formulaitemsbak"];           //四则运算的分解公式备份
                                        cellinfosbak[cellline1]["formulaitemsvalue"] = celldatasets[cellline2]["formulaitemsvalue"];         //四则运算的分解公式的值
                                        cellinfosbak[cellline1]["formulaoperators"] = celldatasets[cellline2]["formulaoperators"];          //四则运算的运算符
                                        cellinfosbak[cellline1]["formulaitemscalculated"] = celldatasets[cellline2]["formulaitemscalculated"];    //四则运算的分解公式是否已经计算
                                    }
                                }
                            }

                            self.cellinfos = cellinfosbak;
                            self.colsproperties = result[3];
                            //增加tips
                            var TipCellType = function () {};
                            TipCellType.prototype = new GcSpread.Sheets.TextCellType();
                            TipCellType.prototype.getHitInfo = function (x, y, cellStyle, cellRect, context) {
                                return {
                                    x: x,
                                    y: y,
                                    row: context.row,
                                    col: context.col,
                                    cellStyle: cellStyle,
                                    cellRect: cellRect,
                                    sheetArea: context.sheetArea
                                };
                            };
                            TipCellType.prototype.processMouseEnter = function (hitinfo)
                            {
                                if (!this._toolTipElement)
                                {
                                    var div = document.createElement("div");
                                    $(div).css("position", "absolute")
                                    .css("border", "1px #C0C0C0 solid")
                                    .css("box-shadow", "1px 2px 5px rgba(0,0,0,0.4)")
                                    .css("font", "9pt Arial")
                                    .css("background", "white")
                                    .css("padding", 5);

                                    this._toolTipElement = div;
                                }
                                var formula = "";
                                var row = 0;
                                var col = 0;
                                var rowoffset = 0;
                                var coloffset = 0;
                                var rangerow = 0;
                                var rangecol = 0;
                                if(self.cellinfos == undefined || self.cellinfos == null)
                                {
                                    $(this._toolTipElement).text("")
                                    .css("top", hitinfo.y + 150)
                                    .css("left", hitinfo.x - 20);
                                    $(this._toolTipElement).hide();
                                    document.body.insertBefore(this._toolTipElement, null);
                                    $(this._toolTipElement).show("fast");
                                    return;
                                }
                                for (var cellline = 0; cellline < self.cellinfos.length; cellline++)
                                {
                                    row = self.cellinfos[cellline]["row"];
                                    col = self.cellinfos[cellline]["col"];
                                    rowoffset = self.cellinfos[cellline]["rowoffset"];
                                    coloffset = self.cellinfos[cellline]["coloffset"];

                                    if (rowoffset > 0 || coloffset > 0)
                                    {
                                        if ((hitinfo.row >= parseInt(row) && hitinfo.row <= parseInt(row) + rowoffset) && (hitinfo.col >= parseInt(col) && hitinfo.col <= parseInt(col) + coloffset))
                                        {
                                            formula = self.cellinfos[cellline]["formula"];
                                            if (formula.length > 0)
                                            {
                                                if (formula.indexOf("=") != 0)
                                                {
                                                    formula = "=" + formula;
                                                }
                                                rangerow = parseInt(row);
                                                rangecol = parseInt(col);
                                                break;
                                            }
                                        }
                                    }
                                    else
                                    {
                                        if (hitinfo.row == parseInt(row) && hitinfo.col == parseInt(col) )
                                        {
                                            formula = self.cellinfos[cellline]["formula"];
                                            if (formula.length > 0)
                                            {
                                                if (formula.indexOf("=") != 0)
                                                {
                                                    formula = "=" + formula;
                                                }
                                                rangerow = parseInt(row);
                                                rangecol = parseInt(col);
                                                break;
                                            }
                                        }
                                    }
                                }

                                var text = "";
                                if (formula.length > 0)
                                {
                                    var startrow = 0;
                                    var startcol = 0;
                                    var endrow = 0;
                                    var endcol = 0;

                                    startrow = rangerow + 1;
                                    startcol = rangecol;
                                    endrow = rangerow + rowoffset + 1;
                                    endcol = rangecol + coloffset;

                                    var s = "";
                                    var e = "";
                                    var colcoordinate = activeSheet.getText(0, startcol,GcSpread.Sheets.SheetArea.colHeader);
                                    s = colcoordinate+startrow;
                                    var colcoordinate = activeSheet.getText(0, endcol,GcSpread.Sheets.SheetArea.colHeader);
                                    e = colcoordinate+endrow;

                                    if(rowoffset > 0 || coloffset > 0)
                                    {
                                        text = "作用范围["+s+":"+e+"]\n区域公式["+formula+"]"
                                    }
                                    else
                                    {
                                        text = "作用范围["+s+":"+e+"]\n单元公式["+formula+"]"
                                    }
                                    $(this._toolTipElement).text(text)
                                    .css("top", hitinfo.y + 150)
                                    .css("left", hitinfo.x - 20);
                                    $(this._toolTipElement).hide();
                                    document.body.insertBefore(this._toolTipElement, null);
                                    $(this._toolTipElement).show("fast");
                                }
                                else {
                                    text = activeSheet.getValue(hitinfo.row,hitinfo.col);
                                    $(this._toolTipElement).text(text)
                                    .css("top", hitinfo.y + 150)
                                    .css("left", hitinfo.x - 20);
                                    $(this._toolTipElement).hide();
                                    document.body.insertBefore(this._toolTipElement, null);
                                    if(text)
                                    {
                                        $(this._toolTipElement).show("fast");
                                    }
                                }
                            };
                            TipCellType.prototype.processMouseLeave = function (hitinfo) {
                                if (this._toolTipElement) {
                                    document.body.removeChild(this._toolTipElement);
                                    this._toolTipElement = null;
                                }
                            };

                            var defaultStyle = activeSheet.getDefaultStyle();
                            defaultStyle.cellType = new TipCellType();
                            activeSheet.setDefaultStyle(defaultStyle);

                            activeSheet.bind(GcSpread.Sheets.Events.CellClick, function (sender, args)
                            {
                                celldatasets = self.cellinfos;
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader) {
                                }
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader) {
                                }
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.corner) {
                                }

                                var rowid = args.row;
                                var colid = args.col;

                                var existformula = false;
                                var row = 0;
                                var col = 0;
                                for (var cellline = 0; cellline < celldatasets.length; cellline++) {
                                    var formula = "";
                                    row = celldatasets[cellline]["row"];
                                    col = celldatasets[cellline]["col"];
                                    if (row == String(rowid) && col == String(colid)) {
                                        formula = celldatasets[cellline]["formula"];
                                        if (formula.length > 0) {
                                            if (formula.indexOf("=") != 0) {
                                                formula = "=" + formula;
                                            }
                                        }

                                        var formulaBar = document.getElementById('formulaBar');
                                        formulaBar.innerHTML = formula;
                                        existformula = true;
                                        break;
                                    }
                                }

                                if (!existformula) {
                                    var formulaBar = document.getElementById('formulaBar');
                                    if (formulaBar.innerHTML.length > 0) {
                                        formulaBar.innerHTML = "";
                                    }
                                }
                            });

                            activeSheet.bind(GcSpread.Sheets.Events.CellDoubleClick, function (sender, args) {
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader) {
                                }
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader) {
                                }
                                if (args.sheetArea === GcSpread.Sheets.SheetArea.corner) {
                                }
                            });
                        };
                        var setctions = document.querySelectorAll("section");
                        setctions[0].childNodes[3].value = fiscaldate.substring(0, 4) + "-" + fiscaldate.substring(4, 6);
                        var h2s = document.querySelectorAll("h2");
                        h2s[0].innerText = self.sheetname;
                    });
                }
            }
        },
        //打印预览
        print: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var printInfo = sheet.printInfo();
            printInfo.orientation(GcSpread.Sheets.PrintPageOrientation.portrait);
            printInfo.showRowHeader(GcSpread.Sheets.PrintVisibilityType.Hide);
            printInfo.showColumnHeader(GcSpread.Sheets.PrintVisibilityType.Hide);
            printInfo.margin({top:0, bottom:0, left:0, right:0, header:0, footer:0});
            spreadtemp.print(0);
        },
        //保存报表
        save: function(){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);

            var serializationOption = {
               ignoreFormula: false, // indicate to ignore the style when convert workbook to json, default value is false
               ignoreStyle: false, // indicate to ignore the formula when convert workbook to json, default value is false
               rowHeadersAsFrozenColumns: false, // indicate to treat the row headers as frozen columns when convert workbook to json, default value is false
               columnHeadersAsFrozenRows: false // indicate to treat the column headers as frozen rows when convert workbook to json, default value is false
            };

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var jsonStr = JSON.stringify(spreadtemp.toJSON(serializationOption));

            // 删除掉已有的重新保存有没有问题？20180713
            // 需要根据插入删除的行和列去处理表格的行数和列数的增加或者减少，比如标题行数，表头行数，表体行数，列数
            // 需要根据插入或者删除的行和列去处理表格中定义的公式，比如BB公式的坐标会变化，控件自带公式的坐标会变化
            // self.category,self.titlerows,self.headrows,self.bodyrows,self.tailrows,self.bodycols,
            var titlerows = self.titlerows;
            var headrows = self.headrows;
            var bodyrows = self.bodyrows;
            var tailrows = self.tailrows;
            var bodycols = self.bodycols;

            var category = "month";
            if (self.category == '1')
            {
                category = 'month';
            }

            if (self.category == '2')
            {
                category = 'year';
            }

            if (self.category == '3')
            {
                category = 'day';
            }

            if (self.category == '4')
            {
                category = 'quarter';
            }

            if (self.insertcols.length > 0)
            {
                for (var i = 0; i < self.insertcols.length; i++)
                {
                    //报表属性专用
                    self.colsproperties.push({"report_code":self.code,
                                                "report_date":self.date,
                                                "col_name":"",
                                                "col_isnumber":'0',
                                                "col_isamount":'0',
                                                "col_isadjust":'0',
                                                "col_isitem":'0',
                                                });
                }
            }

            //保存前再获取一下数据
            var activeSheet = spreadtemp.getSheet(0);
            var cellinfosbak = [];
            for (var i = 0; i < activeSheet.getRowCount(); i++)
            {
                for (var j = 0; j < activeSheet.getColumnCount(); j++)
                {
                    var data = activeSheet.getValue(i, j);
                    var text = "";
                    if (data == "" || data == undefined || data == null)
                    {
                        data = 0;
                    }

                    if (isNaN(data))
                    {
                        text = data;
                        data = 0;
                    }

                    var celldata = {};
                    celldata["row"] = String(i);
                    celldata["col"] = String(j);
                    celldata["rowoffset"] = 0;
                    celldata["coloffset"] = 0;
                    celldata["data"] = data;
                    celldata["text"] = text;
                    celldata["formula"] = "";                   //四则运算的整体公式
                    celldata["formulaitems"] = [];              //四则运算的分解公式
                    celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                    celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                    celldata["formulaoperators"] = [];          //四则运算的运算符
                    celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                    celldata["newformula"] = "0";               //新增公式
                    cellinfosbak.push(celldata);
                }
            }

            var row1 = 0;
            var col1 = 0;
            var row2 = 0;
            var col2 = 0;
            var celldatasets = [];
            celldatasets = self.cellinfos;
            for (var cellline1 = 0; cellline1 < cellinfosbak.length; cellline1++)
            {
                row1 = cellinfosbak[cellline1]["row"];
                col1 = cellinfosbak[cellline1]["col"];
                for (var cellline2 = 0; cellline2 < celldatasets.length; cellline2++)
                {
                    row2 = celldatasets[cellline2]["row"];
                    col2 = celldatasets[cellline2]["col"];

                    if (row1 == row2 && col1 == col2) {
                        cellinfosbak[cellline1]["rowoffset"] = celldatasets[cellline2]["rowoffset"];
                        cellinfosbak[cellline1]["coloffset"] = celldatasets[cellline2]["coloffset"];
                        cellinfosbak[cellline1]["formula"] = celldatasets[cellline2]["formula"];                   //四则运算的整体公式
                        cellinfosbak[cellline1]["formulaitems"] = celldatasets[cellline2]["formulaitems"];              //四则运算的分解公式
                        cellinfosbak[cellline1]["formulaitemsbak"] = celldatasets[cellline2]["formulaitemsbak"];           //四则运算的分解公式备份
                        cellinfosbak[cellline1]["formulaitemsvalue"] = celldatasets[cellline2]["formulaitemsvalue"];         //四则运算的分解公式的值
                        cellinfosbak[cellline1]["formulaoperators"] = celldatasets[cellline2]["formulaoperators"];          //四则运算的运算符
                        cellinfosbak[cellline1]["formulaitemscalculated"] = celldatasets[cellline2]["formulaitemscalculated"];    //四则运算的分解公式是否已经计算
                    }
                }
            }
            self.cellinfos = cellinfosbak;

            // 如果进行过插入行插入列删除行删除列,那么公式已经包含到celldatasets中
            var args = [self.code,self.sheetname,currentdate,category,self.titlerows,self.headrows,self.bodyrows,self.tailrows,self.bodycols,jsonStr,self.cellinfos,self.colsproperties];
            var defsave = this._rpc({model: 'ps.statement.statements',method: 'save',args: args}).then(function (result)
            {
                if (result)
                {
                    if (result[0])
                    {
                        self.isnew = "0";
                        self.defineformulas = [];
                        self.insertrows = [];
                        self.insertcols = [];
                        self.deleterows = [];
                        self.deletecols = [];
                        self.cellinfos = result[1];
                        // alert("保存成功。");
                    }
                    else
                    {
                        alert("保存失败，请检查。");
                    }
                }
            });
        },
        //计算报表
        calculate: function(){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);

            var serializationOption = {
               ignoreFormula: false, // indicate to ignore the style when convert workbook to json, default value is false
               ignoreStyle: false, // indicate to ignore the formula when convert workbook to json, default value is false
               rowHeadersAsFrozenColumns: false, // indicate to treat the row headers as frozen columns when convert workbook to json, default value is false
               columnHeadersAsFrozenRows: false // indicate to treat the column headers as frozen rows when convert workbook to json, default value is false
            };

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var jsonStr = JSON.stringify(spreadtemp.toJSON(serializationOption));
            var deffiscal = this._rpc({model: 'ps.statement.statements',method: 'get_fiscalperiod'}).then(function (result)
            {
                if (result)
                {
                    currentdate = result;
                }
                else {
                    return;
                }
            });

            var sheet = spreadtemp.getSheet(0);

            // 然后将刚定义未保存的公式信息更新单元格存在信息
            // 区域公式只存放在最左上角的单元格
            // var formulas = this.defineformulas;
            //计算过程的新新定义公式需要从defineformulas迁移到cellinfos，待处理完保存后再处理，20180718
            var args = [self.code,currentdate,self.cellinfos,"NOTBB"];
            var defcalculate = this._rpc({model: 'ps.statement.statements',method: 'calculate',args: args}).then(function (result)
            {
                if (result)
                {
                    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    spreadtemp.isPaintSuspended(true);
                    var sheet = spreadtemp.getSheet(0);

                    var row = 0;
                    var col = 0;
                    var data = 0;
                    var formula = "";
                    for(var i=0;i<result.length;i++)
                    {
                        row = result[i].row;
                        col = result[i].col;
                        data = result[i].data;
                        formula = result[i].formula;

                        if(data == undefined || data == null)
                        {
                            data = 0;
                        }

                        if (formula)
                        {
                            if (data == 0)
                            {
                                sheet.setValue(parseInt(row),parseInt(col),"");
                            }
                            else {
                                sheet.setValue(parseInt(row),parseInt(col),data);
                            }
                        }
                    }
                    spreadtemp.isPaintSuspended(false);

                    var celldatasets = [];
                    for(var i=0;i<sheet.getRowCount();i++)
                    {
                        for(var j=0;j<sheet.getColumnCount();j++)
                        {
                            var data = sheet.getValue(i,j);
                            if(data == "" || data == undefined || data == null)
                            {
                                data = 0;
                            }
                            for(var ii=0;ii<result.length;ii++)
                            {
                                row = result[ii].row;
                                col = result[ii].col;
                                // 已经存在则更新，不存在则插入
                                if (parseInt(row) == i && parseInt(col) == j)
                                {
                                    if (isNaN(data))
                                    {
                                        result[ii]["data"] = 0;
                                        result[ii]["text"] = data;
                                    }
                                    else {
                                        result[ii]["data"] = data;
                                        result[ii]["text"] = "";
                                    }
                                    break;
                                }
                            }
                        }
                    }
                    self.cellinfos = result;
                    var setctions = document.querySelectorAll("section");
                    var date = setctions[0].childNodes[3].value;
                    var currentdate = date.substring(0,4)+date.substring(5,7);
                    var args = [self.code,currentdate,self.cellinfos,"BB"];
                    var defcalculate = self._rpc({model: 'ps.statement.statements',method: 'calculate',args: args}).then(function (result)
                    {
                       if (result)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            spreadtemp.isPaintSuspended(true);
                            var sheet = spreadtemp.getSheet(0);

                            var row = 0;
                            var col = 0;
                            var data = 0;
                            for(var i=0;i<result.length;i++)
                            {
                                row = result[i].row;
                                col = result[i].col;
                                data = result[i].data;
                                formula = result[i].formula;

                                if (data == undefined || data == null)
                                {
                                    data = 0;
                                }

                                if (formula)
                                {
                                    if (data == 0) {
                                        sheet.setValue(parseInt(row), parseInt(col), "");
                                    }
                                    else {
                                        sheet.setValue(parseInt(row), parseInt(col), data);
                                    }
                                }
                                var tmpformula = "";
                                for(var j =0;j <result[i].formulaitemsbak.length;j++ )
                                {
                                    if(result[i].formulaitemsbak[j].indexOf("BB") >=0)
                                    {
                                        if (j ==0)
                                        {
                                            tmpformula = result[i].formulaitems[j];
                                        }
                                        else{
                                             tmpformula = tmpformula + result[i].formulaoperators[j - 1] + result[i].formulaitems[j];
                                        }
                                    }
                                }
                                sheet.setFormula(parseInt(row),parseInt(col),tmpformula);
                            }
                            self.cellinfos = result;
                            spreadtemp.isPaintSuspended(false);
                        };
                    });
                };
            });
        },
        //转出格式
        export: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var json = JSON.stringify(spreadtemp.toJSON());

            var blob = new Blob([json],{type : 'application/json'});
            saveAs(blob, this.code + "_" + this.date + "_" + this.sheetname + ".ssjson");
            return;



            // if (json.length == 0)
            // {
            //     alert("传递的JSON字符串为空，请检查。");
            //     return;
            // }else{
            //     var myForm = document.createElement("form");
            //     myForm.method = "post";
            //     myForm.target="_blank"
            //     // myForm.action = "http://115.28.63.151：8199/SpreadJsExcel.aspx";
            //     // myForm.action = "http://10.24.11.163/SpreadJsExcel.aspx";
            //     myForm.action = "http://10.24.18.60:8069/SpreadJsExcel.aspx";
            //     var myInputcode = document.createElement("input");
            //     myInputcode.setAttribute("type", 'hidden');
            //     myInputcode.setAttribute("name", 'report_code');
            //     myInputcode.setAttribute("value", '0001');
            //     myForm.appendChild(myInputcode);
            //     var myInputname = document.createElement("input");
            //     myInputname.setAttribute("type", 'hidden');
            //     myInputname.setAttribute("name", 'report_name');
            //     myInputname.setAttribute("value", '资产负债表');
            //     myForm.appendChild(myInputname);
            //     var myInputjson = document.createElement("input");
            //     myInputjson.setAttribute("type", 'hidden');
            //     myInputjson.setAttribute("name", 'SpreadjsExcel');
            //     myInputjson.setAttribute("value", json);
            //     myForm.appendChild(myInputjson);
            //     document.body.appendChild(myForm);
            //     myForm.submit();
            //     document.body.removeChild(myForm);
            // }

            // framework.blockUI();
            // this.getSession().get_file({
            //     url: '/statement/export',
            //     data: {data: '{"version":"11.1.0","allowContextMenu":false,"sheets":{"资产负债表":{"name":"资产负债表","rowCount":38,"columnCount":8,"theme":"Office2007","data":{"dataTable":{"0":{"0":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"1":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"2":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"3":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"4":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"5":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"6":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}},"7":{"value":"资产负债表","style":{"hAlign":1,"vAlign":1,"font":"bold 32px Calibri","textIndent":0}}},"1":{"7":{"value":"会小企01表","style":{"hAlign":2}}},"2":{"0":{"value":"单位名称：My Company"},"3":{"value":"2018年05月"},"7":{"value":"单位：元","style":{"hAlign":2}}},"3":{"0":{"value":"资产","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"1":{"value":"行次","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"2":{"value":"期末余额","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"3":{"value":"年初余额","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"4":{"value":"负债和所有者权益(或股东权益)","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"5":{"value":"行次","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"6":{"value":"期末余额","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}},"7":{"value":"年初余额","style":{"hAlign":1,"font":"bold 13.3333px Calibri","borderLeft":{"color":"Black","style":2},"borderTop":{"color":"Black","style":2},"borderRight":{"color":"Black","style":2},"borderBottom":{"color":"Black","style":2}}}},"4":{"0":{"value":"流动资产：","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"流动负债：","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"5":{"0":{"value":"    货币资金","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":1,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    短期借款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":31,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"6":{"0":{"value":"    短期投资","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":2,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应付票据","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":32,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"7":{"0":{"value":"    应收票据","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":3,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应付账款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":33,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"8":{"0":{"value":"    应收账款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":4,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    预收账款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":34,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"9":{"0":{"value":"    预付账款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":5,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应付职工薪酬","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":35,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"10":{"0":{"value":"    应收股利","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":6,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应交税费","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":36,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"11":{"0":{"value":"    应收利息","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":7,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应付利息","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":37,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"12":{"0":{"value":"    其他应收款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":8,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    应付利润","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":38,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"13":{"0":{"value":"    存货","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":9,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    其他应付款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":39,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"14":{"0":{"value":"其中:原材料","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":10,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    其他流动负债","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":40,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"15":{"0":{"value":"        在产品","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":11,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    流动负债合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":41,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(G5:G14)"},"7":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(H5:H14)"}},"16":{"0":{"value":"        库存商品","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":12,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"非流动负债：","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"17":{"0":{"value":"        周转材料","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":13,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    长期借款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":42,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"18":{"0":{"value":"    其他流动资产","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":14,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    长期应付款","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":43,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"19":{"0":{"value":"    流动资产合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":15,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(C5:C13)+C18"},"3":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(D5:D13)+D18"},"4":{"value":"    递延收益","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":44,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"20":{"0":{"value":"非流动资产：","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    其他非流动负债","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":45,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"21":{"0":{"value":"    长期债券投资","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":16,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    非流动负债合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":46,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(G17:G20)"},"7":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(H17:H20)"}},"22":{"0":{"value":"    长期股权投资","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":17,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"负债合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":47,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"G15+G21"},"7":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"H15+H21"}},"23":{"0":{"value":"    固定资产原价","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":18,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"24":{"0":{"value":"    减：累计折旧","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":19,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"25":{"0":{"value":"    固定资产账面价值","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":20,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"C23-C24"},"3":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"D23+D24"},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"26":{"0":{"value":"    在建工程","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":21,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"27":{"0":{"value":"    工程物资","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":22,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"28":{"0":{"value":"    固定资产清理","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":23,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"29":{"0":{"value":"    生产性生物资产","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":24,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"所有者权益（或股东权益）","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"30":{"0":{"value":"    无形资产","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":25,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    实收资本（或股本）","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":48,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"31":{"0":{"value":"    开发支出","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":26,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    资本公积","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":49,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"32":{"0":{"value":"    长期待摊费用","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":27,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    盈余公积","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":50,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"33":{"0":{"value":"    其他非流动资产","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":28,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"3":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"4":{"value":"    未分配利润","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":51,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"7":{"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}}},"34":{"0":{"value":"    非流动资产合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":29,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(C21:C22)+SUM(C25:C33)"},"3":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(D21:D22)+SUM(D25:D33)"},"4":{"value":"    所有者权益（或股东权益）合计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":52,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(G30:G33)"},"7":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"SUM(H30:H33)"}},"35":{"0":{"value":"    资产总计","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"1":{"value":30,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"2":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"C19+C34"},"3":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"D19+D34"},"4":{"value":"    负债和所有者权益（或股东权益）总计\n","style":{"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"5":{"value":53,"style":{"hAlign":1,"borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}}},"6":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"G22+G34"},"7":{"value":0,"style":{"hAlign":2,"formatter":"#,##0.00","borderLeft":{"color":"Black","style":1},"borderTop":{"color":"Black","style":1},"borderRight":{"color":"Black","style":1},"borderBottom":{"color":"Black","style":1}},"formula":"H22+H34"}}},"defaultDataNode":{"style":{"themeFont":"Body"}}},"rowHeaderData":{"defaultDataNode":{"style":{"themeFont":"Body"}}},"colHeaderData":{"defaultDataNode":{"style":{"themeFont":"Body"}}},"rows":[{"size":50}],"columns":[{"size":160},{"size":60},{"size":100},{"size":100},{"size":270},{"size":60},{"size":100},{"size":100}],"spans":[{"row":0,"rowCount":1,"col":0,"colCount":8}],"selections":{"0":{"row":0,"rowCount":1,"col":0,"colCount":8},"length":1},"index":0}}}'},
            //     complete: framework.unblockUI,
            //     error: crash_manager.rpc_error.bind(crash_manager),
            // });
            var params={jsonstr:json,code:this.code,date:this.date};
            var def1 = this._rpc({route:'/odoo/export_file', params: params}).then(function (result)
            {
                if(result)
                {
                    alert("导出成功。");
                }
            });
            // console.log(json);
            // $.ajax({
            //     url: '/odoo/account_statement',
            //     data: json,
            //     dataType: 'json',
            //     type: "POST",
            //     async: false,
            //     contentType: "application/json",
            //     success: function (data) {
            //         // console.log(data);
            //         alert("保存成功！");
            //         // alert("打印页面的JSON数据:\n" + JSON.stringify(report));
            //     },
            //     error: function (jqXHR, textStatus, errorThrown) {
            //         //alert('保存失败！');
            //         //alert(JSON.stringify(report));
            //     }
            // });
        },
        //转入格式
        import: function(){
            // var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            // var json = JSON.stringify(spreadtemp.toJSON());

            // if (json.length == 0)
            // {
            //     alert("传递的JSON字符串为空，请检查。");
            //     return;
            // }else{
            //     var myForm = document.createElement("form");
            //     myForm.method = "post";
            //     myForm.target="_blank"
            //     // myForm.action = "http://115.28.63.151：8199/SpreadJsExcel.aspx";
            //     // myForm.action = "http://10.24.11.163/SpreadJsExcel.aspx";
            //     myForm.action = "http://10.24.18.60:8069/SpreadJsExcel.aspx";
            //     var myInputcode = document.createElement("input");
            //     myInputcode.setAttribute("type", 'hidden');
            //     myInputcode.setAttribute("name", 'report_code');
            //     myInputcode.setAttribute("value", '0001');
            //     myForm.appendChild(myInputcode);
            //     var myInputname = document.createElement("input");
            //     myInputname.setAttribute("type", 'hidden');
            //     myInputname.setAttribute("name", 'report_name');
            //     myInputname.setAttribute("value", '资产负债表');
            //     myForm.appendChild(myInputname);
            //     var myInputjson = document.createElement("input");
            //     myInputjson.setAttribute("type", 'hidden');
            //     myInputjson.setAttribute("name", 'SpreadjsExcel');
            //     myInputjson.setAttribute("value", json);
            //     myForm.appendChild(myInputjson);
            //     document.body.appendChild(myForm);
            //     myForm.submit();
            //     document.body.removeChild(myForm);
            // }

            // var params={jsonstr:json};
            // var def1 = this._rpc({route:'/odoo/upload_file', params: params}).then(function (result)
            // {
            //     if(result)
            //     {
            //         alert("测试成功。");
            //     }
            // });

            // var self = this;
            // self.do_action({
            //     name: '导入',
            //     type: 'ir.actions.client',
            //     tag: 'statement_import',
            //     params: {
            //         model: 'ps.statement.statements',
            //         context: {},
            //     }
            // });

            var self = this;
            $("#myInputcode").click();
            var file = "";
            var filename = "";
            var imgFile = "";

            $("#myInputcode").change(function () {
                file = $("#upload").find("input")[0].files[0];
                if (file == "" || file == undefined || file == null)
                {
                    alert("未选中文件，请检查");
                    return;
                }
                filename = $("#upload").find("input")[0].files[0].name;

                // 0001_201806_资产负债表.ssjson
                var startindex = filename.lastIndexOf("_");
                var endindex = filename.indexOf(".");
                filename = filename.substring(startindex + 1,endindex);
                //创建读取文件的对象
                var reader = new FileReader();

                //为文件读取成功设置事件
                reader.onload=function(e) {
                    imgFile = e.target.result;

                    var jsonStr = imgFile;
                    var name = filename;
                    var jsonresult = JSON.parse(jsonStr);
                    if(jsonresult["sheets"][name])
                    {
                        var datatable = jsonresult["sheets"][name]["data"]["dataTable"];
                        var rowcount = jsonresult["sheets"][name]["rowCount"];
                        var colcount = jsonresult["sheets"][name]["columnCount"];
                    }
                    else {
                        alert("请检查文件名是否合法，类似于‘0001_201807_资产负债表.ssjson’");
                        return;
                    }

                    var cellinfobak = [];

                    for (var i = 0; i < self.cellinfos.length; i++)
                    {
                        cellinfobak[i] = self.cellinfos[i];
                    }

                    self.cellinfos.splice(0,self.cellinfos.length);

                    for (var i = 0; i < rowcount; i++)
                    {
                        for (var j = 0; j < colcount; j++)
                        {
                            if (!datatable[String(i)])
                            {
                                continue;
                            }

                            if(!datatable[String(i)][String(j)])
                            {
                                continue;
                            }
                            else
                            {
                                var data = datatable[String(i)][String(j)].value;
                                var text = "";
                                if (data == "" || data == undefined || data == null)
                                {
                                    data = 0;
                                }

                                if (isNaN(data))
                                {
                                    text = data;
                                    data = 0;
                                }

                                var formula = "";
                                if (datatable[String(i)][String(j)].formula)
                                {
                                    formula = datatable[String(i)][String(j)].formula;
                                    datatable[String(i)][String(j)].formula = "";
                                }

                                var celldata = {};
                                celldata["row"] = String(i);
                                celldata["col"] = String(j);
                                celldata["rowoffset"] = 0;
                                celldata["coloffset"] = 0;
                                celldata["data"] = data;
                                celldata["text"] = text;
                                celldata["formula"] = formula;                   //四则运算的整体公式
                                celldata["formulaitems"] = [];              //四则运算的分解公式
                                celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                celldata["formulaoperators"] = [];          //四则运算的运算符
                                celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                celldata["newformula"] = "1";               //新增公式
                                self.cellinfos.push(celldata);
                            }
                        }
                    }
                    jsonStr = JSON.stringify(jsonresult);

                    var jsonOptions = {
                        ignoreFormula: false, // indicate to ignore style when convert json to workbook, default value is false
                        ignoreStyle: false, // indicate to ignore the formula when convert json to workbook, default value is false
                        frozenColumnsAsRowHeaders: false, // indicate to treat the frozen columns as row headers when convert json to workbook, default value is false
                        frozenRowsAsColumnHeaders: false, // indicate to treat the frozen rows as column headers when convert json to workbook, default value is false
                        doNotRecalculateAfterLoad: false //  indicate to forbid recalculate after load the json, default value is false
                    };
                    // var spread = new GcSpread.Sheets.Spread(document.getElementById('statements_sheet'), {sheetCount: 1});
                    var spread = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    spread.isPaintSuspended(true);
                    spread.fromJSON(JSON.parse(jsonStr), jsonOptions);
                    spread.isPaintSuspended(false);
                    spread.newTabVisible(false);

                    var activeSheet = spread.getSheet(0);
                     //增加tips
                    var TipCellType = function () {};
                    TipCellType.prototype = new GcSpread.Sheets.TextCellType();
                    TipCellType.prototype.getHitInfo = function (x, y, cellStyle, cellRect, context) {
                        return {
                            x: x,
                            y: y,
                            row: context.row,
                            col: context.col,
                            cellStyle: cellStyle,
                            cellRect: cellRect,
                            sheetArea: context.sheetArea
                        };
                    };
                    TipCellType.prototype.processMouseEnter = function (hitinfo)
                    {
                        if (!this._toolTipElement)
                        {
                            var div = document.createElement("div");
                            $(div).css("position", "absolute")
                            .css("border", "1px #C0C0C0 solid")
                            .css("box-shadow", "1px 2px 5px rgba(0,0,0,0.4)")
                            .css("font", "9pt Arial")
                            .css("background", "white")
                            .css("padding", 5);

                            this._toolTipElement = div;
                        }
                        var formula = "";
                        var row = 0;
                        var col = 0;
                        var rowoffset = 0;
                        var coloffset = 0;
                        var rangerow = 0;
                        var rangecol = 0;
                        if(self.cellinfos == undefined || self.cellinfos == null)
                        {
                            $(this._toolTipElement).text("")
                            .css("top", hitinfo.y + 150)
                            .css("left", hitinfo.x - 20);
                            $(this._toolTipElement).hide();
                            document.body.insertBefore(this._toolTipElement, null);
                            $(this._toolTipElement).show("fast");
                            return;
                        }
                        for (var cellline = 0; cellline < self.cellinfos.length; cellline++)
                        {
                            row = self.cellinfos[cellline]["row"];
                            col = self.cellinfos[cellline]["col"];
                            rowoffset = self.cellinfos[cellline]["rowoffset"];
                            coloffset = self.cellinfos[cellline]["coloffset"];

                            if (rowoffset > 0 || coloffset > 0)
                            {
                                if ((hitinfo.row >= parseInt(row) && hitinfo.row <= parseInt(row) + rowoffset) && (hitinfo.col >= parseInt(col) && hitinfo.col <= parseInt(col) + coloffset))
                                {
                                    formula = self.cellinfos[cellline]["formula"];
                                    if (formula.length > 0)
                                    {
                                        if (formula.indexOf("=") != 0)
                                        {
                                            formula = "=" + formula;
                                        }
                                        rangerow = parseInt(row);
                                        rangecol = parseInt(col);
                                        break;
                                    }
                                }
                            }
                            else
                            {
                                if (hitinfo.row == parseInt(row) && hitinfo.col == parseInt(col) )
                                {
                                    formula = self.cellinfos[cellline]["formula"];
                                    if (formula.length > 0)
                                    {
                                        if (formula.indexOf("=") != 0)
                                        {
                                            formula = "=" + formula;
                                        }
                                        rangerow = parseInt(row);
                                        rangecol = parseInt(col);
                                        break;
                                    }
                                }
                            }
                        }

                        var text = "";
                        if (formula.length > 0)
                        {
                            var startrow = 0;
                            var startcol = 0;
                            var endrow = 0;
                            var endcol = 0;

                            startrow = rangerow + 1;
                            startcol = rangecol;
                            endrow = rangerow + rowoffset + 1;
                            endcol = rangecol + coloffset;

                            var s = "";
                            var e = "";
                            var colcoordinate = activeSheet.getText(0, startcol,GcSpread.Sheets.SheetArea.colHeader);
                            s = colcoordinate+startrow;
                            var colcoordinate = activeSheet.getText(0, endcol,GcSpread.Sheets.SheetArea.colHeader);
                            e = colcoordinate+endrow;

                            if(rowoffset > 0 || coloffset > 0)
                            {
                                text = "作用范围["+s+":"+e+"]\n区域公式["+formula+"]"
                            }
                            else
                            {
                                text = "作用范围["+s+":"+e+"]\n单元公式["+formula+"]"
                            }
                            $(this._toolTipElement).text(text)
                            .css("top", hitinfo.y + 150)
                            .css("left", hitinfo.x - 20);
                            $(this._toolTipElement).hide();
                            document.body.insertBefore(this._toolTipElement, null);
                            $(this._toolTipElement).show("fast");
                        }
                        else {
                            text = activeSheet.getValue(hitinfo.row,hitinfo.col);
                            $(this._toolTipElement).text(text)
                            .css("top", hitinfo.y + 150)
                            .css("left", hitinfo.x - 20);
                            $(this._toolTipElement).hide();
                            document.body.insertBefore(this._toolTipElement, null);
                            if(text)
                            {
                                $(this._toolTipElement).show("fast");
                            }
                        }
                    };
                    TipCellType.prototype.processMouseLeave = function (hitinfo) {
                        if (this._toolTipElement) {
                            document.body.removeChild(this._toolTipElement);
                            this._toolTipElement = null;
                        }
                    };

                    var defaultStyle = activeSheet.getDefaultStyle();
                    defaultStyle.cellType = new TipCellType();
                    activeSheet.setDefaultStyle(defaultStyle);
                    var celldatasets = [];
                    activeSheet.bind(GcSpread.Sheets.Events.CellClick, function (sender, args)
                    {
                        celldatasets = self.cellinfos;
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader) {
                        }
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader) {
                        }
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.corner) {
                        }

                        var rowid = args.row;
                        var colid = args.col;

                        var existformula = false;
                        var row = 0;
                        var col = 0;
                        for (var cellline = 0; cellline < celldatasets.length; cellline++) {
                            var formula = "";
                            row = celldatasets[cellline]["row"];
                            col = celldatasets[cellline]["col"];
                            if (row == String(rowid) && col == String(colid)) {
                                formula = celldatasets[cellline]["formula"];
                                if (formula.length > 0) {
                                    if (formula.indexOf("=") != 0) {
                                        formula = "=" + formula;
                                    }
                                }

                                var formulaBar = document.getElementById('formulaBar');
                                formulaBar.innerHTML = formula;
                                existformula = true;
                                break;
                            }
                        }

                        if (!existformula) {
                            var formulaBar = document.getElementById('formulaBar');
                            if (formulaBar.innerHTML.length > 0) {
                                formulaBar.innerHTML = "";
                            }
                        }
                    });

                    activeSheet.bind(GcSpread.Sheets.Events.CellDoubleClick, function (sender, args) {
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.colHeader) {
                        }
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader) {
                        }
                        if (args.sheetArea === GcSpread.Sheets.SheetArea.corner) {
                        }
                    });
                };
                reader.readAsText(file);
            });
        },
        //导出数据
        output: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var json = JSON.stringify(spreadtemp.toJSON());

            if (json.length == 0)
            {
                alert("传递的JSON字符串为空，请检查。");
                return;
            }else{
                var myForm = document.createElement("form");
                myForm.method = "post";
                myForm.target="_blank";
                myForm.action = "http://115.28.63.151:8199/SpreadJsExcel.aspx";
                // myForm.action = "http://10.24.11.163/SpreadJsExcel.aspx";
                // myForm.action = "http://10.24.18.60:8069/SpreadJsExcel.aspx";
                var myInputcode = document.createElement("input");
                myInputcode.setAttribute("type", 'hidden');
                myInputcode.setAttribute("name", 'report_code');
                myInputcode.setAttribute("value", '0001');
                myForm.appendChild(myInputcode);
                var myInputname = document.createElement("input");
                myInputname.setAttribute("type", 'hidden');
                myInputname.setAttribute("name", 'report_name');
                myInputname.setAttribute("value", '资产负债表');
                myForm.appendChild(myInputname);
                var myInputjson = document.createElement("input");
                myInputjson.setAttribute("type", 'hidden');
                myInputjson.setAttribute("name", 'SpreadjsExcel');
                myInputjson.setAttribute("value", json);
                myForm.appendChild(myInputjson);
                document.body.appendChild(myForm);
                myForm.submit();
                document.body.removeChild(myForm);
            }
        },
        //导入数据
        // input: function(){
        //     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
        //     var json = JSON.stringify(spreadtemp.toJSON());
        //
        //     if (json.length == 0)
        //     {
        //         alert("传递的JSON字符串为空，请检查。");
        //         return;
        //     }else{
        //         var myForm = document.createElement("form");
        //         myForm.method = "post";
        //         myForm.target="_blank"
        //         // myForm.action = "http://115.28.63.151：8199/SpreadJsExcel.aspx";
        //         // myForm.action = "http://10.24.11.163/SpreadJsExcel.aspx";
        //         myForm.action = "http://10.24.18.60:8069/SpreadJsExcel.aspx";
        //         var myInputcode = document.createElement("input");
        //         myInputcode.setAttribute("type", 'hidden');
        //         myInputcode.setAttribute("name", 'report_code');
        //         myInputcode.setAttribute("value", '0001');
        //         myForm.appendChild(myInputcode);
        //         var myInputname = document.createElement("input");
        //         myInputname.setAttribute("type", 'hidden');
        //         myInputname.setAttribute("name", 'report_name');
        //         myInputname.setAttribute("value", '资产负债表');
        //         myForm.appendChild(myInputname);
        //         var myInputjson = document.createElement("input");
        //         myInputjson.setAttribute("type", 'hidden');
        //         myInputjson.setAttribute("name", 'SpreadjsExcel');
        //         myInputjson.setAttribute("value", json);
        //         myForm.appendChild(myInputjson);
        //         document.body.appendChild(myForm);
        //         myForm.submit();
        //         document.body.removeChild(myForm);
        //     }
        // },
        //月末存档
        monthend: function(){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);
            var nextmonth = parseInt(date.substring(5,7)) + 1;
            var nextdate = "";
            if (nextmonth > 12 )
            {
                nextmonth = "01";
                var nextyear = parseInt(date.substring(0,4)) + 1;
                nextdate = nextyear + nextmonth ;
            }
            else
            {
                if (nextmonth >= 1 && nextmonth <= 9)
                {
                    nextmonth = "0" + nextmonth;
                }
                nextdate = date.substring(0,4) + nextmonth ;
            }

            var args = [self.code, currentdate, nextdate]
            var defmonthend = this._rpc({model: 'ps.statement.statements',method: 'monthend',args: args}).then(function (result)
            {
                if (result)
                {
                    alert("月末存档完成。");
                };
            });
        },
        //改变会计区间
        datechange: function (){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);
            var args = [self.code, currentdate]
            var defdatechange = this._rpc({model: 'ps.statement.statements',method: 'datechange',args: args}).then(function (result)
            {
                if (result)
                {
                    var jsonStr = result;

                    var jsonOptions = {
                        ignoreFormula: false, // indicate to ignore style when convert json to workbook, default value is false
                        ignoreStyle: false, // indicate to ignore the formula when convert json to workbook, default value is false
                        frozenColumnsAsRowHeaders: false, // indicate to treat the frozen columns as row headers when convert json to workbook, default value is false
                        frozenRowsAsColumnHeaders: false, // indicate to treat the frozen rows as column headers when convert json to workbook, default value is false
                        doNotRecalculateAfterLoad: false //  indicate to forbid recalculate after load the json, default value is false
                    }

                    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    spreadtemp.fromJSON(JSON.parse(jsonStr), jsonOptions);

                    var celldatasets = [];
                    var row = 0;
                    var col = 0;
                    var activeSheet = spreadtemp.getSheet(0);
                    activeSheet.bind(GcSpread.Sheets.Events.CellClick, function (sender, args)
                    {
                        celldatasets = self.cellinfos;
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.colHeader){
                        }
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader){
                        }
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.corner){
                        }

                        var rowid = args.row;
                        var colid = args.col;

                        var existformula = false;
                        for(var cellline = 0;cellline < celldatasets.length;cellline++)
                        {
                            var formula = "";
                            row = celldatasets[cellline]["row"];
                            col = celldatasets[cellline]["col"];
                            if (row == String(rowid) && col == String(colid))
                            {
                                formula = celldatasets[cellline]["formula"];
                                if (formula.length > 0)
                                {
                                    if (formula.indexOf("=") != 0)
                                    {
                                        formula = "=" + formula;
                                    }
                                }

                                var formulaBar = document.getElementById('formulaBar');
                                formulaBar.innerHTML = formula;
                                existformula = true;
                                break;
                            }
                        }

                        if(!existformula)
                        {
                            var formulaBar = document.getElementById('formulaBar');
                            if(formulaBar.innerHTML.length > 0)
                            {
                                formulaBar.innerHTML = "";
                            }
                        }
                    });

                    activeSheet.bind(GcSpread.Sheets.Events.CellDoubleClick, function (sender, args) {
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.colHeader){
                        }
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.rowHeader){
                        }
                        if(args.sheetArea === GcSpread.Sheets.SheetArea.corner){
                        }
                    });
                }
                else
                {
                    alert("不存在会计区间为["+currentdate+"]的报表，请检查。");
                    var setctionsbak = document.querySelectorAll("section");
                    setctionsbak[0].childNodes[3].value = self.date.substring(0,4) + '-' + self.date.substring(4,6);
                    return;
                }
            });
        },
        //插入行插入列后操作
        formulabyrowcolchange: function(){
            // 插入行：所有去当前报表单元格数据的BB公式和控件自带公式,
            // 如果在插入行上面的单元格定义的公式，取小于插入行上的单元格的值，坐标不变
            // 如果在插入行上面的单元格定义的公式，取大于等于插入行上的单元格的值，那么行坐标需要加1
            // 如果在插入行下面的单元格定义的公式，取小于插入行上的单元格的值，坐标不变
            // 如果在插入行下面的单元格定义的公式，取大于等于插入行上的单元格的值，那么行坐标需要加1
            // 如果在插入行单元格定义的公式，取小于插入行上的单元格的值，坐标不变
            // 如果在插入行单元格定义的公式，取大于等于插入行上的单元格的值，那么行坐标需要加1
            // 总结规律：公式为取小于插入行上的单元格的值，坐标不变；取大于等于插入行上的单元格的值，那么行坐标需要加1；
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var celldatasets = self.cellinfos;
            var formulas = this.defineformulas;
            //计算过程的新新定义公式需要从defineformulas迁移到cellinfos，待处理完保存后再处理，20180718
            var args = [self.code,currentdate,celldatasets,formulas,this.insertrows,this.insertcols,this.deleterows,this.deletecols];
            var defformulachange = this._rpc({model: 'ps.statement.sheet.cells',method: 'formula_by_rowcol_change',args: args}).then(function (result)
            {
                if (result)
                {
                    self.cellinfos = result;
                }
            });
        },
        //剪切
        cut: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            GcSpread.Sheets.SpreadActions.cut.call(sheet);
        },
        //复制
        copy: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            GcSpread.Sheets.SpreadActions.copy.call(sheet);
        },
        //粘贴
        paste: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            GcSpread.Sheets.SpreadActions.paste.call(sheet);
        },
        //合并单元格
        merge: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var sel = sheet.getSelections();
            if (sel.length > 0)
            {
                sel = sel[sel.length - 1];
                sheet.addSpan(sel.row, sel.col, sel.rowCount, sel.colCount, GcSpread.Sheets.SheetArea.viewport);
            }
        },
        //取消合并
        unmerge: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var sels = sheet.getSelections();
            for (var i = 0; i < sels.length; i++)
            {
                var sel = getActualCellRange(sels[i], sheet.getRowCount(), sheet.getColumnCount());
                for (var r = 0; r < sel.rowCount; r++)
                {
                    for (var c = 0; c < sel.colCount; c++)
                    {
                        var span = sheet.getSpan(r + sel.row, c + sel.col, GcSpread.Sheets.SheetArea.viewport);
                        if (span)
                        {
                            sheet.removeSpan(span.row, span.col, GcSpread.Sheets.SheetArea.viewport);
                        }
                    }
                }
            }
        },
        //清除数据
        cleardata: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedcells = sheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            sheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Data);
        },
        //清除公式
        clearformula: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedcells = sheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;

            for(var i = 0;i < this.cellinfos.length;i++)
            {
                var row = parseInt(this.cellinfos[i]["row"]);
                var col = parseInt(this.cellinfos[i]["col"]);

                if (row == rows && col == cols )
                {
                    this.cellinfos[i]["formula"] = "";
                }
            }
        },
        //清除格式
        clearstyle: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedcells = sheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            sheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Style);
        },
        //全部清除
        clearall: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedcells = sheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            sheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Data);
            sheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Style);
        },
        //插入行
        insertrow: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            sheet.addRows(selectedrow, 1);
            var insertrow = {};
            insertrow["row"] = selectedrow;
            insertrow["count"] = 1;
            this.insertrows.push(insertrow);

            if (selectedrow >=0 && selectedrow < self.titlerows)
            {
                self.titlerows = self.titlerows + 1;
            }
            else if (selectedrow >=self.titlerows && selectedrow < self.titlerows + self.headrows)
            {
                self.headrows = self.headrows + 1;
            }
            else if (selectedrow >=self.titlerows + self.headrows && selectedrow < self.titlerows + self.headrows + self.bodyrows)
            {
                self.bodyrows = self.bodyrows + 1;
            }
            else if (selectedrow >=self.titlerows + self.headrows + self.bodyrows && selectedrow < self.titlerows + self.headrows + self.bodyrows + self.tailrows)
            {
                self.tailrows = self.tailrows + 1;
            }

            self.cellinfos = this.formulabyrowcolchange(); //处理公式坐标
            // 新插入行需要设置全边框，单元格属性类似选中行，需要考虑合并单元格的情况
            // sheet.copyTo(selectedrow+1,0,selectedrow,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
            sheet.copyTo(selectedrow+1,0,selectedrow,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
        },
        //插入列
        insertcol: function (){
            var self = this;
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            sheet.addColumns(selectedcol, 1);

            var insertcol = {};
            insertcol["col"] = selectedcol;
            insertcol["count"] = 1;
            this.insertcols.push(insertcol);
            self.bodycols = self.bodycols + 1;
            //报表属性专用
            self.colsproperties.push({"report_code":self.code,
                                        "report_date":self.date,
                                        "col_name":"",
                                        "col_order":self.bodycols,
                                        "col_coordinate":self.bodycols,
                                        "col_isnumber":'0',
                                        "col_isamount":'0',
                                        "col_isadjust":'0',
                                        "col_isitem":'0',
                                        });
            // 新插入行需要设置全边框，单元格属性类似选中行，需要考虑合并单元格的情况
            self.cellinfos = this.formulabyrowcolchange(); //处理公式坐标
            sheet.copyTo(0,selectedcol + 1,0,selectedcol,sheet.getRowCount(),1,GcSpread.Sheets.CopyToOption.Style);
        },
        //删除行
        deleterow: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            sheet.deleteRows(selectedrow, selectedrowcount);
            var deleterow = {};
            deleterow["row"] = selectedrow;
            deleterow["count"] = selectedrowcount;
            this.deleterows.push(deleterow);

            if (selectedrow >=0 && selectedrow < self.titlerows)
            {
                if (selectedrowcount > self.titlerows)
                {
                    self.titlerows = 0
                }
                else{
                    self.titlerows = self.titlerows - selectedrowcount;
                }
            }
            else if (selectedrow >=self.titlerows && selectedrow < self.titlerows + self.headrows)
            {
                if (selectedrowcount > self.headrows)
                {
                    self.headrows = 0
                }
                else{
                    self.headrows = self.headrows - selectedrowcount;
                }
            }
            else if (selectedrow >=self.titlerows + self.headrows && selectedrow < self.titlerows + self.headrows + self.bodyrows)
            {
                if (selectedrowcount > self.bodyrows)
                {
                    self.bodyrows = 0
                }
                else{
                    self.bodyrows = self.bodyrows - selectedrowcount;
                }
            }
            else if (selectedrow >=self.titlerows + self.headrows + self.bodyrows && selectedrow < self.titlerows + self.headrows + self.bodyrows + self.tailrows)
            {
                if (selectedrowcount > self.tailrows)
                {
                    self.tailrows = 0
                }
                else{
                    self.tailrows = self.tailrows  - selectedrowcount;
                }
            }

            self.cellinfos = this.formulabyrowcolchange(); //处理公式坐标
        },
        //删除列
        deletecol: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            sheet.deleteColumns(selectedcol, selectedcolcount);
            var deletecol = {};
            deletecol["col"] = selectedcol;
            deletecol["count"] = selectedcolcount;
            this.deletecols.push(deletecol);

            if (selectedcolcount > self.bodycols)
            {
                self.bodycols = 0
            }
            else{
                self.bodycols = self.bodycols - selectedrowcount;
            }
            self.cellinfos = this.formulabyrowcolchange(); //处理公式坐标
        },
        // 计算选中区域
        calculateselectedrange: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);

            var selectedcells = sheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;

            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);
            var deffiscal = this._rpc({model: 'ps.statement.statements',method: 'get_fiscalperiod'}).then(function (result)
            {
                if (result)
                {
                    currentdate = result;
                }
                else {
                    return;
                }
            });

            // 然后将刚定义未保存的公式信息更新单元格存在信息
            // 区域公式只存放在最左上角的单元格
            // var formulas = this.defineformulas;
            //计算过程的新新定义公式需要从defineformulas迁移到cellinfos，待处理完保存后再处理，20180718
            var dataset = [];
            for(var i=0;i<self.cellinfos.length;i++)
            {
                // rows：控件选中区域开始行
                // cols：控件选中区域开始列
                // rowe：控件选中区域结束行
                // cole：控件选中区域结束列

                var row = parseInt(self.cellinfos[i]["row"]);
                var col = parseInt(self.cellinfos[i]["col"]);

                if (row >= rows && row <= rows + rowCounts - 1 && col >= cols && col <= cols + colCounts - 1)
                {
                    dataset.push(self.cellinfos[i]);
                }
            }

            var args = [self.code,currentdate,dataset,"NOTBB"];
            var defcalculate = this._rpc({model: 'ps.statement.statements',method: 'calculate',args: args}).then(function (result)
            {
                if (result)
                {
                    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    spreadtemp.isPaintSuspended(true);
                    var sheet = spreadtemp.getSheet(0);

                    var row = 0;
                    var col = 0;
                    var data = 0;
                    var formula = "";
                    for(var i=0;i<result.length;i++)
                    {
                        row = result[i].row;
                        col = result[i].col;
                        data = result[i].data;
                        formula = result[i].formula;

                        if(data == undefined || data == null)
                        {
                            data = 0;
                        }

                        if (formula)
                        {
                            if (data == 0)
                            {
                                sheet.setValue(parseInt(row),parseInt(col),"");
                            }
                            else {
                                sheet.setValue(parseInt(row),parseInt(col),data);
                            }
                        }
                    }
                    spreadtemp.isPaintSuspended(false);

                    var celldatasets = [];
                    for(var i = rows;i < rows + rowCounts;i++)
                    {
                        for(var j = cols;j < cols + colCounts;j++)
                        {
                            var data = sheet.getValue(i,j);
                            if(data == "" || data == undefined || data == null)
                            {
                                data = 0;
                            }
                            for(var ii=0;ii<self.cellinfos.length;ii++)
                            {
                                row = self.cellinfos[ii].row;
                                col = self.cellinfos[ii].col;
                                // 已经存在则更新，不存在则插入
                                if (parseInt(row) == i && parseInt(col) == j)
                                {
                                    if (isNaN(data))
                                    {
                                        self.cellinfos[ii]["data"] = 0;
                                        self.cellinfos[ii]["text"] = data;
                                    }
                                    else {
                                        self.cellinfos[ii]["data"] = data;
                                        self.cellinfos[ii]["text"] = "";
                                    }
                                    break;
                                }
                            }
                        }
                    }

                    // self.cellinfos = result;
                    // 将result上的值更新到self.cellinfos上
                    var dataset1 = [];
                    var setctions = document.querySelectorAll("section");
                    var date = setctions[0].childNodes[3].value;
                    var currentdate = date.substring(0,4)+date.substring(5,7);

                    for(var i=0;i<self.cellinfos.length;i++)
                    {
                        // rows：控件选中区域开始行
                        // cols：控件选中区域开始列
                        // rowe：控件选中区域结束行
                        // cole：控件选中区域结束列

                        var row = parseInt(self.cellinfos[i]["row"]);
                        var col = parseInt(self.cellinfos[i]["col"]);

                        if (row >= rows && row <= rows + rowCounts - 1 && col >= cols && col <= cols + colCounts - 1)
                        {
                            dataset1.push(self.cellinfos[i]);
                        }
                    }
                    var args = [self.code,currentdate,dataset1,"BB"];
                    var defcalculate = self._rpc({model: 'ps.statement.statements',method: 'calculate',args: args}).then(function (result1)
                    {
                       if (result1)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            spreadtemp.isPaintSuspended(true);
                            var sheet = spreadtemp.getSheet(0);

                            var row = 0;
                            var col = 0;
                            var data = 0;
                            for(var i=0;i<result1.length;i++)
                            {
                                row = result1[i].row;
                                col = result1[i].col;
                                data = result1[i].data;
                                formula = result1[i].formula;

                                if (data == undefined || data == null)
                                {
                                    data = 0;
                                }

                                if (formula)
                                {
                                    if (data == 0) {
                                        sheet.setValue(parseInt(row), parseInt(col), "");
                                    }
                                    else {
                                        sheet.setValue(parseInt(row), parseInt(col), data);
                                    }
                                }
                                var tmpformula = "";
                                for(var j =0;j <result1[i].formulaitemsbak.length;j++ )
                                {
                                    if(result1[i].formulaitemsbak[j].indexOf("BB") >=0)
                                    {
                                        if (j ==0)
                                        {
                                            tmpformula = result1[i].formulaitems[j];
                                        }
                                        else{
                                             tmpformula = tmpformula + result1[i].formulaoperators[j - 1] + result1[i].formulaitems[j];
                                        }
                                    }
                                }
                                sheet.setFormula(parseInt(row),parseInt(col),tmpformula);
                            }
                            // self.cellinfos = result;

                            for(var i = rows;i < rows + rowCounts - 1;i++)
                            {
                                for(var j = cols;j < cols + colCounts - 1;j++)
                                {
                                    var data = sheet.getValue(i,j);
                                    if(data == "" || data == undefined || data == null)
                                    {
                                        data = 0;
                                    }
                                    for(var ii=0;ii<self.cellinfos.length;ii++)
                                    {
                                        row = self.cellinfos[ii].row;
                                        col = self.cellinfos[ii].col;
                                        // 已经存在则更新，不存在则插入
                                        if (parseInt(row) == i && parseInt(col) == j)
                                        {
                                            if (isNaN(data))
                                            {
                                                self.cellinfos[ii]["data"] = 0;
                                                self.cellinfos[ii]["text"] = data;
                                            }
                                            else {
                                                self.cellinfos[ii]["data"] = data;
                                                self.cellinfos[ii]["text"] = "";
                                            }
                                            break;
                                        }
                                    }
                                }
                            }
                            spreadtemp.isPaintSuspended(false);
                        };
                    });
                };
            });
        },
        //单元格数据构成
        celldatacomposition: function(){
            //先计算选中区域
            this.calculateselectedrange();

            var start = new Date().getTime();

            while(true)
            {
                if(new Date().getTime()-start > 1000) break;
            }

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            var data = sheet.getValue(selectedrow,selectedcol);

            if ((selectedrowcount > 1 ) || (selectedcolcount > 1))
            {
                alert("该功能适用单一单元格，请检查。")
                window.event.returnValue = false;
                return false;
            }

            var selectedrange = "";
            var rangestartrow = "";
            var rangestartcol = "";
            var rangeendrow = "";
            var rangeendcol = "";
            if (selectedrow == -1)
            {
                rangestartrow = 1
            }
            else
            {
                rangestartrow = selectedrow + 1;
            }
            rangeendrow = rangestartrow + selectedrowcount - 1;
            rangestartcol = sheet.getText(0, selectedcol,GcSpread.Sheets.SheetArea.colHeader);
            rangeendcol = sheet.getText(0, selectedcol+selectedcolcount - 1,GcSpread.Sheets.SheetArea.colHeader);
            selectedrange = rangestartcol+rangestartrow+":"+rangeendcol+rangeendrow;

            var $div=$("<div>",{id:"dialog-message",title:"单元格数据构成"});
            var $secformulaarithmetic = $("<section class=\"formulaarithmetic\" id=\"formulaarithmetic\" style=\"height: 100%;width: 100%;margin-top: 20px;\" >");
            var $arithmetictable = $("<table class=\"arithmetictable\" id=\"arithmetictable\" >");
            var $arithmetictablehead = $('<thead class="arithmetictablehead" id="arithmetictablehead"><tr><th>公式</th><th>运算符号</th><th>数值</th></tr></thead>');
            $arithmetictable.append($arithmetictablehead);
            var $arithmetictablebody = $('<tbody class="arithmetictablebody" id="arithmetictablebody"></tbody>');

            var formula = "";
            var self = this;
            var defgetformula = this._rpc({
                model: 'ps.statement.sheet.cells',
                method: 'get_cell_formula',
                args: [this.code,this.date,selectedrow,selectedcol]
            }).then(function (result)
            {
                if (!result || result == "")
                {
                    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    var activeSheet = spreadtemp.getSheet(0);
                    var formula = activeSheet.getFormula(selectedrow,selectedcol);
                    if (formula)
                    {
                        if (formula.indexOf("EVAL") == 0)
                        {
                            formula = formula.substring(6,formula.length);
                            formula = formula.substring(0,formula.length - 2);
                            formula = "=" + formula;
                        }
                    }
                }
                if (result)
                {
                    var temp = "";
                    try {
                        temp = result[0].cell_formula;
                    }
                    catch (err) {
                        temp = "";
                    }
                    if (temp) {
                        formula = temp;
                    }
                }
                if (self.cellinfos.length > 0)
                {
                    var destactionrangesrow = selectedrow;
                    var destactionrangescolnum = selectedcol;
                    var destactionrangeerow = selectedrow + selectedrowcount - 1;
                    var destactionrangeecolnum = selectedcol + selectedcolcount - 1;
                    var formulaitemsvalue = [];
                    for(var i=0;i<self.cellinfos.length;i++)
                    {
                       // rows：控件选中区域开始行
                       // cols：控件选中区域开始列
                       // rowe：控件选中区域结束行
                       // cole：控件选中区域结束列

                        var rows = parseInt(self.cellinfos[i]["row"]);
                        var cols = parseInt(self.cellinfos[i]["col"]);
                        var rowe = rows + self.cellinfos[i]["rowoffset"];
                        var cole = cols + self.cellinfos[i]["coloffset"];

                        if (rows == destactionrangesrow && cols == destactionrangescolnum && rowe == destactionrangeerow && cole == destactionrangeecolnum) {
                            formula = self.cellinfos[i]["formula"];
                            formulaitemsvalue = self.cellinfos[i]["formulaitemsvalue"];
                            data = self.cellinfos[i]["data"];
                        }
                    }
                }

                if (formula)
                {
                    var formulasbyone = {};
                    var formulaunit = [];
                    var operators = [];
                    var resultformulas = false;

                    var defget_formula_from_arithmetic = self._rpc({
                        model: 'ps.statement.sheet.cells',
                        method: 'get_formula_from_arithmetic',
                        args: [formula, formulasbyone, formulaunit, operators]
                    }).then(function (result)
                    {
                        if (result)
                        {
                            formulasbyone = result[0];
                            formulaunit = result[1];
                            operators = result[2];
                            for(var i = 0;i < formulaunit.length;i++ )
                            {
                                var $tr = $("<tr>");
                                var temp = formulaunit[i];
                                if (formulaunit[i].indexOf("=") == 0)
                                {
                                    temp = formulaunit[i].substring(1,formulaunit[i].length);
                                }
                                var $td1=$("<td width='400px'>");
                                // var $input=$("<input>",{"name":"inputaddformula","class":"inputaddformula","id":"inputaddformula","type":"text"});
                                // $input.val(temp);
                                // $td1.append($input);
                                $td1.html(temp);

                                var operator = operators[i];
                                if (!operator)
                                {
                                    operator = "";
                                }

                                var $td2=$("<td width='100px'>");
                                // var $input=$("<input>",{"name":"inputaddoperator","class":"inputaddoperator","id":"inputaddoperator","type":"text"});
                                // $input.val(operator);
                                // $td2.append($input);
                                $td2.html(operator);

                                var $td3 = $("<td id = 'formulavalue'+string(i) width='100px'>");
                                var formulavalue = formulaitemsvalue[i];

                                if (formulavalue == "" || formulavalue == undefined || formulavalue == null)
                                {
                                    $td3.html(0.00);
                                }
                                else{
                                    $td3.html(formulavalue.toFixed(2));
                                }

                                var $td4=$("<td width='100px'>");
                                var $a = $("<a>",{"href":"javascript:;","onclick":'{if(confirm("确定要删除当前选中公式记录吗?")) {deleteCurrentRow(this); }else {}}'});
                                $a.html("删除公式");
                                $td4.append($a);

                                $tr.append($td1);
                                $tr.append($td2);
                                $tr.append($td3);
                                // $tr.append($td4);

                                $arithmetictablebody.append($tr);
                            }
                        }
                    });

                    var $arithmetictablefoot = $('<tfoot class="arithmetictablefoot" id="arithmetictablefoot"></tfoot>');

                    var $td1 = $("<td width='100px'>");
                    $td1.html("<strong>合计</strong>");
                    var $td2 = $("<td width='100px'>");
                    $td2.html("");
                    var $td3 = $("<td width='100px'>");

                    if (data == "" || data == undefined || data == null)
                    {
                        $td3.html(0.00);
                    }
                    else{
                        $td3.html(data.toFixed(2));
                    }
                    // var $td4=$("<td width='100px'>");
                    // $td4.html("");

                    $arithmetictablefoot.append($td1);
                    $arithmetictablefoot.append($td2);
                    $arithmetictablefoot.append($td3);
                    // $arithmetictablefoot.append($td4);

                    $arithmetictable.append($arithmetictablebody);
                    $arithmetictable.append($arithmetictablefoot);
                    $secformulaarithmetic.append($arithmetictable);

                    $div.append($secformulaarithmetic);

                    $div.dialog({
                        modal: true,
                        width:500,
                        buttons: {
                            确定: function()
                            {
                                $div.empty();
                                $( this ).dialog( "close" );
                            },
                        }
                    });
                }
                else{
                    alert("当前选中单元格不存在公式，请检查。");
                    return;
                }
            });
        },
        //公式状态
        formulastate: function (){
            var div = document.getElementById("statement_formula");
            if(div.style.display == "none"){
                div.style.display = "block";
            } else {
                div.style.display = "none";
            }
            var self = this;
            var report_code = self.code;
            var report_date = self.date;

            var args =[report_code,report_date];
            var defdefineformula = this._rpc({model: 'ps.statement.sheet.cells',method: 'get_cells_info',args: args}).then(function (result)
            {
                if (result)
                {
                    // $("#statement_formula").append('<table id = "formula" name = "formula"><thead id="formulahead"><tr><th><input id="allboxs" onclick="allcheck()" type="checkbox"/></th><th>行坐标</th><th>列坐标</th><th>行偏移量</th><th>列偏移量</th><th>公式</th></tr></thead><tbody name="formulabody" id="formulabody"></tbody></table>');
                    var $first=$("#formula").find("tbody");
                    for(var i=0;i<result.length;i++)
                    {
                        var $tr=$("<tr onclick='TrOnClick()'>");
                        for(var j=0;j<6;j++)
                        {
                            if(j==0) {
                                var $td=$("<td width='50px'>");
                                var $inputcheck=$("<input>",{"name":"boxs","id":"rowid"+String(i),"class":"row"+String(i),"type":"checkbox"});
                                // $inputcheck.val(0);
                                $td=$td.append($inputcheck);
                            }
                            else if(j==1)
                            {
                                var $td=$("<td width='100px'>");
                                $td.html(result[i].row_order);
                            }else if(j==2)
                            {
                                var $td=$("<td width='100px'>");
                                $td.html(result[i].col_order);
                            }else if(j==3)
                            {
                                var $td=$("<td width='100px'>");
                                $td.html(result[i].cell_rowoffset);
                            }else if(j==4)
                            {
                                var $td=$("<td width='100px'>");
                                $td.html(result[i].cell_coloffset);
                            }else if(j==5)
                            {
                                var $td=$("<td width='1000px'>");
                                var $input=$("<input>",{"name":"inputformula","class":"inputformula","id":"inputformula","type":"text","oncontextmenu":"rightmenu_formula_guide()"});
                                $input.val(result[i].cell_formula);
                                $td=$td.append($input);
                                // $td.html(result[i].cell_formula).attr("contentEditable","true");

                            }else {
                                var $td=$("<td width='100px'>");
                                $td.html("");
                            }
                            $tr=$tr.append($td);
                        }
                        // $tr.insertBefore($first);
                        $tr.insertAfter($first);
                    }
                }
            });
        },
        //新建公式
        newformula: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            if ((selectedrow <= 0 ) || (selectedrow >= sheet.getRowCount()))
            {
                alert("选中区域的行不在表格范围内，请检查。")
                return;
            }

            if ((selectedcol <= 0 ) || (selectedcol >= sheet.getColumnCount()))
            {
                alert("选中区域的列不在表格范围内，请检查。")
                return;
            }

            var tbl = document.getElementById("formula");
            var trs = tbl.getElementsByTagName("tr");

            var $first=$("#formula").find("tbody");
            var $tr=$("<tr onclick='TrOnClick()'>");

            var $td1=$("<td width='50px'>");
            var $inputcheck=$("<input>",{"name":"boxs","id":"rowid"+String(trs.length+1),"class":"row"+String(trs.length+1),"type":"checkbox"});
            $td1.append($inputcheck);

            // var $td2=$("<td width='100px'>");
            // $td2.html(selectedrow);
            var $td2=$("<td width='100px'>");
            var $input=$("<input>",{"name":"inputaddformularow","class":"inputaddformularow","id":"inputaddformularow","type":"text"});
            $input.val(selectedrow);
            $td2.append($input);

            // var $td3=$("<td width='100px'>");
            // $td3.html(selectedcol);

            var $td3=$("<td width='100px'>");
            var $input=$("<input>",{"name":"inputaddformulacol","class":"inputaddformulacol","id":"inputaddformulacol","type":"text"});
            $input.val(selectedcol);
            $td3.append($input);

            // var $td4=$("<td width='100px'>");
            // $td4.html(selectedrowcount - 1);
            var $td4=$("<td width='100px'>");
            var $input=$("<input>",{"name":"inputaddformularowoffset","class":"inputaddformularowoffset","id":"inputaddformularowoffset","type":"text"});
            $input.val(selectedrowcount - 1);
            $td4.append($input);

            // var $td5=$("<td width='100px'>");
            // $td5.html(selectedcolcount - 1);
            var $td5=$("<td width='100px'>");
            var $input=$("<input>",{"name":"inputaddformulacoloffset","class":"inputaddformulacoloffset","id":"inputaddformulacoloffset","type":"text"});
            $input.val(selectedcolcount - 1);
            $td5.append($input);

            var $td6=$("<td width='1000px'>");
            var $input=$("<input>",{"name":"inputformula","class":"inputformula","id":"inputformula","type":"text","oncontextmenu":"rightmenu_formula_guide()"});
            $input.val("=");
            $td6.append($input);

            $tr.append($td1);
            $tr.append($td2);
            $tr.append($td3);
            $tr.append($td4);
            $tr.append($td5);
            $tr.append($td6);
            $tr.insertBefore($first);
        },
        //公式编辑完成后回车
        inputformulakeydown: function (){
            var self = this;
            if(event.keyCode==13)
            {
                var inputaddformularows = $("input[name='inputaddformularow']");
                var row = inputaddformularows[0].value;
                var inputaddformulacols = $("input[name='inputaddformulacol']");
                var col = inputaddformulacols[0].value;
                var inputaddformularowoffsets = $("input[name='inputaddformularowoffset']");
                var rowoffset = inputaddformularowoffsets[0].value;
                var inputaddformulacoloffsets = $("input[name='inputaddformulacoloffset']");
                var coloffset = inputaddformulacoloffsets[0].value;
                var inputformulas = $("input[name='inputformula']");
                var formula = inputformulas[0].value;

                var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                var sheet = spreadtemp.getSheet(0);

                sheet.setSelection(row,col);
                var selectedrow = row;
                var selectedrowcount = rowoffset + 1;
                var selectedcol = col;
                var selectedcolcount = coloffset + 1;

                if ((selectedrow < 0 ) || (selectedrow > sheet.getRowCount()))
                {
                    alert("选中区域的行不在表格范围内，请检查。")
                    window.event.returnValue = false;
                    return false;
                }

                if ((selectedcol < 0 ) || (selectedcol > sheet.getColumnCount()))
                {
                    alert("选中区域的列不在表格范围内，请检查。")
                    window.event.returnValue = false;
                    return false;
                }

                var data = sheet.getValue(selectedrow,selectedcol);
                var formulaBar = document.getElementById('formulaBar');
                // var formula = formulaBar.innerHTML;
                if(formula == "" || formula == undefined || formula == null)
                {
                    if(confirm("定义的公式为空，将清除当前单元格原有公式，是否确定？"))
                    {
                        var destactionrangesrow = selectedrow;
                        var destactionrangescolnum = selectedcol;
                        var destactionrangeerow = selectedrow + selectedrowcount - 1;
                        var destactionrangeecolnum = selectedcol + selectedcolcount - 1;

                        // 删除定义但是未保存的公式
                        for(var i=0;i<self.cellinfos.length;i++)
                        {
                            var rows = parseInt(self.cellinfos[i]["row"]);
                            var cols = parseInt(self.cellinfos[i]["col"]);

                            if (rows == destactionrangesrow && cols == destactionrangescolnum )
                            {
                                self.cellinfos.splice(i,1); //是删除还是置空值得商榷

                                if(sheet.getComment(selectedrow, selectedcol))
                                {
                                    sheet.setComment(selectedrow, selectedcol, null);
                                    spreadtemp.refresh();
                                }
                            }
                        }
                    }
                    window.event.returnValue = false;
                    return false;
                }
                else {
                    formula = formula.toUpperCase();
                    if(formula.indexOf("=") == 0)
                    {
                        formula = formula.substring(1,formula.length);
                    }

                    var destactionrangesrow = selectedrow;
                    var destactionrangescolnum = selectedcol;
                    var destactionrangeerow = selectedrow + selectedrowcount - 1;
                    var destactionrangeecolnum = selectedcol + selectedcolcount - 1;

                    // 如果是新定义的那么需要更新系统变量self.cellinfos
                    var existrecord = true;
                    if(self.cellinfos.length > 0)
                    {
                        for (var i = 0; i < self.cellinfos.length; i++)
                        {
                            var rows = parseInt(self.cellinfos[i]["row"]);
                            var cols = parseInt(self.cellinfos[i]["col"]);
                            var rowe = rows + self.cellinfos[i]["rowoffset"];
                            var cole = cols + self.cellinfos[i]["coloffset"];

                            // 存在则更新，不存在则插入
                            if (rows == destactionrangesrow && cols == destactionrangescolnum )
                            {
                                self.cellinfos[i]["formula"] = formula;
                                if (isNaN(data))
                                {
                                    self.cellinfos[i]["data"] = 0;
                                    self.cellinfos[i]["text"] = data;
                                }
                                else {
                                    self.cellinfos[i]["data"] = data;
                                    self.cellinfos[i]["text"] = "";
                                }
                                self.cellinfos[i]["rowoffset"] = destactionrangeerow - destactionrangesrow;
                                self.cellinfos[i]["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                                self.cellinfos[i]["formulaitems"] = [];              //四则运算的分解公式
                                self.cellinfos[i]["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                self.cellinfos[i]["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                self.cellinfos[i]["formulaoperators"] = [];          //四则运算的运算符
                                self.cellinfos[i]["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                self.cellinfos[i]["newformula"] = "1";               //新增公式
                            }
                            else {
                                existrecord = false;
                            }
                        }

                        if(!existrecord)
                        {
                            var celldata = {};
                            celldata["row"] = String(destactionrangesrow);
                            celldata["col"] = String(destactionrangescolnum);
                            celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                            celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                            // alert(destactionrangeerow - destactionrangesrow);
                            // alert(destactionrangeecolnum - destactionrangescolnum);
                            if (isNaN(data))
                            {
                                celldata["data"] = 0;
                                celldata["text"] = data;
                            }
                            else {
                                celldata["data"] = data;
                                celldata["text"] = "";
                            }
                            celldata["formula"] = formula;              //四则运算的整体公式
                            celldata["formulaitems"] = [];              //四则运算的分解公式
                            celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                            celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                            celldata["formulaoperators"] = [];          //四则运算的运算符
                            celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                            celldata["newformula"] = "1";               //新增公式
                            self.cellinfos.push(celldata);
                        }
                    }
                    else{
                        var celldata = {};
                        celldata["row"] = String(destactionrangesrow);
                        celldata["col"] = String(destactionrangescolnum);
                        celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                        celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                        if (isNaN(data))
                        {
                            celldata["data"] = 0;
                            celldata["text"] = data;
                        }
                        else {
                            celldata["data"] = data;
                            celldata["text"] = "";
                        }
                        celldata["formula"] = formula;              //四则运算的整体公式
                        celldata["formulaitems"] = [];              //四则运算的分解公式
                        celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                        celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                        celldata["formulaoperators"] = [];          //四则运算的运算符
                        celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                        celldata["newformula"] = "1";               //新增公式
                        self.cellinfos.push(celldata);
                    }
                }
                if(formula.indexOf("=") == 0)
                {
                    formulaBar.innerHTML = formula;
                }
                else
                {
                    formulaBar.innerHTML = "="+formula;
                }

                window.event.returnValue=false;
            }
        },
        //删除公式
        deleteformula: function (){
            var self = this;
            if(confirm("确定要删除当前选中公式记录吗?"))
            {
                var tbl = document.getElementById("formula");
                var trs = tbl.getElementsByTagName("tr");

                var namebox = $("input[name^='boxs']");
                for (var i = 0; i < namebox.length; i++)
                {
                    if (namebox[i].checked)
                    {
                        var tbody = trs[i + 1].parentNode;
                        tbody.removeChild(trs[i + 1]);
                        //只剩行首时删除表格
                        if (tbody.rows.length == 1) {
                            tbody.parentNode.removeChild(tbody);
                        }

                        var rows = document.getElementById('formula').rows[i + 1].cells;
                        var row = rows[1].innerHTML;
                        var col = rows[2].innerHTML;

                        if (self.cellinfos.length > 0)
                        {
                            for (var index = 0; index < self.cellinfos.length; index++)
                            {
                                var rows = parseInt(self.cellinfos[index]["row"]);
                                var cols = parseInt(self.cellinfos[index]["col"]);

                                if (rows == row && cols == col )
                                {
                                    self.cellinfos.splice(index+1,1); //是删除还是置空值得商榷
                                }
                            }
                        }
                    }
                }
            }
        },
        //注销widget
        // destroy: function (){
            //经过验证，返回的页面已经不是当初的页面了，比如，输入的数值已经丢失20180628
            // var url = window.location.href;
            // // alert(url);
            // var temp = "view_type=list&model=ps.statement.statements&action=286&menu_id=195";
            // if (url.indexOf(temp) > 0)
            // {
            //     // alert(temp+";"+url);
            //     this._super.apply(this, arguments);
            //     if(confirm("报表已经修改，关闭前需要点击保存报表按钮完成保存，现在去完成?"))
            //     {
            //         window.history.back();
            //     }else{
            //         // this.save();
            //     }
            // }
        // },
        //公式替换
        replaceformula: function (){
            var self = this;
            var formulaBar = document.getElementById('formulaBar');
            var formula = formulaBar.innerHTML;

            var $div=$("<div>",{id:"dialog-message",title:"公式替换"});
            var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("不支持通过替换公式增加或者减少公式参数。");
            $div=$div.append($paa);
            var $p=$("<p>").html("替换公式");
            $div.append($p);
            var $inputsrc = $("<input>",{"name":"formula_source","class":"formula_source","id":"formula_source","type":"text"});

            $div.append($inputsrc);
            var $p1=$("<p>").html("目标公式");
            $div=$div.append($p1);
            var $inputdesc = $("<input>",{"name":"formula_destination","class":"formula_destination","id":"formula_destination","type":"text"});
            $div.append($inputdesc);

            if(!(formula == "" || formula == undefined || formula == null))
            {
                $inputsrc.val(formula);
                $inputdesc.val(formula);
            }

            $div.dialog({
                modal: true,
                width:500,
                buttons: {
                    确定: function()
                    {
                        var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                        var sheet = spreadtemp.getSheet(0);
                        var selectedRanges = sheet.getSelections();
                        var selectedrow = selectedRanges[0].row;
                        var selectedrowcount = selectedRanges[0].rowCount;
                        var selectedcol = selectedRanges[0].col;
                        var selectedcolcount = selectedRanges[0].colCount;

                        var formulasource = $inputsrc.val();
                        var formuladestination = $inputdesc.val();

                        if(formulasource == "" || formulasource == undefined || formulasource == null)
                        {
                            alert("替换公式为空，请检查。")
                            return false;
                        }

                        if(formuladestination == "" || formuladestination == undefined || formuladestination == null)
                        {
                            alert("目标公式为空，请检查。")
                            return false;
                        }

                        //将选中区域内的所有公式替换，需要遍历选中区域
                        //首先获取控件上公式，然后获取数据库中的公式，最后检查是否有新定义的公式
                        //如果公式存在，并且是新定义的公式，那么需要删除新定义的，然后重新定义一个目标公式的公式

                        var startrow = 0;
                        var endrow = 0;
                        if (selectedrow < 0)
                        {
                            startrow = 0;
                            endrow = selectedrowcount;
                        }
                        else
                        {
                            startrow = selectedrow;
                            endrow = selectedrow + selectedrowcount;
                        }

                        var startcol = 0;
                        var endcol = 0;
                        if (selectedcol < 0)
                        {
                            startcol = 0;
                            endcol = selectedcolcount;
                        }
                        else {
                            startcol = selectedcol;
                            endcol = selectedcol + selectedcolcount;
                        }
                        for (var i = startrow; i < endrow; i++)
                        {
                            for (var j = startcol; j < endcol; j++)
                            {
                                if (self.cellinfos.length > 0)
                                {
                                    for (var index = 0; index < self.cellinfos.length; index++)
                                    {
                                        var rows = parseInt(self.cellinfos[index]["row"]);
                                        var cols = parseInt(self.cellinfos[index]["col"]);

                                        if (rows == i && cols == j )
                                        {
                                            formula = self.cellinfos[index]["formula"];
                                            if (formula)
                                            {
                                                while(formula.indexOf(formulasource) >= 0)
                                                {
                                                    formula = formula.replace(formulasource, formuladestination);
                                                }
                                                self.cellinfos[index]["formula"] = formula;

                                                for(var itemindex = 0;itemindex < self.cellinfos[index]["formulaitems"].minLength;itemindex++)
                                                {
                                                    formula = self.cellinfos[index]["formulaitems"][itemindex].replace(formulasource, formuladestination);
                                                    self.cellinfos[index]["formulaitems"][itemindex] = formula;
                                                    self.cellinfos[index]["formulaitemsbak"][itemindex] = formula;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        $( this ).dialog( "close" );
                    },
                    取消: function()
                    {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                }
            });

        },
        //公式状态公式替换
        replaceformulaatformulastate: function (){
            var self = this;
            var formulaBar = document.getElementById('formulaBar');
            var formula = formulaBar.innerHTML;

            var $div=$("<div>",{id:"dialog-message",title:"公式替换"});
            var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("不支持通过替换公式增加或者减少公式参数。");
            $div=$div.append($paa);
            var $p=$("<p>").html("替换公式");
            $div.append($p);
            var $inputsrc = $("<input>",{"name":"formula_source","class":"formula_source","id":"formula_source","type":"text"});

            $div.append($inputsrc);
            var $p1=$("<p>").html("目标公式");
            $div=$div.append($p1);
            var $inputdesc = $("<input>",{"name":"formula_destination","class":"formula_destination","id":"formula_destination","type":"text"});
            $div.append($inputdesc);

            if(!(formula == "" || formula == undefined || formula == null))
            {
                $inputsrc.val(formula);
                $inputdesc.val(formula);
            }

            $div.dialog({
                modal: true,
                width:500,
                buttons: {
                    确定: function()
                    {
                        var formulasource = $inputsrc.val();
                        var formuladestination = $inputdesc.val();

                        if(formulasource == "" || formulasource == undefined || formulasource == null)
                        {
                            alert("替换公式为空，请检查。")
                            return false;
                        }

                        if(formuladestination == "" || formuladestination == undefined || formuladestination == null)
                        {
                            alert("目标公式为空，请检查。")
                            return false;
                        }

                        var inputformulas = $("input[name='inputformula']");
                        var namebox = $("input[name^='boxs']");
                        for(var i = 0; i < namebox.length; i++)
                        {
                            if (namebox[i].checked)
                            {
                                formula = inputformulas[i].value;
                                if (formula)
                                {
                                    while (formula.indexOf(formulasource) >= 0)
                                    {
                                        formula = formula.replace(formulasource, formuladestination);
                                        inputformulas[i].value = formula;
                                    }
                                }

                                var rows = document.getElementById('formula').rows[i + 1].cells;
                                var row = rows[1].innerHTML;
                                var col = rows[2].innerHTML;

                                if (self.cellinfos.length > 0)
                                {
                                    for (var index = 0; index < self.cellinfos.length; index++)
                                    {
                                        var rows = parseInt(self.cellinfos[index]["row"]);
                                        var cols = parseInt(self.cellinfos[index]["col"]);

                                        if (rows == row && cols == col )
                                        {
                                            self.cellinfos[index]["formula"] = formula;

                                            for(var itemindex = 0;itemindex < self.cellinfos[index]["formulaitems"].minLength;itemindex++)
                                            {
                                                formula = self.cellinfos[index]["formulaitems"][itemindex].replace(formulasource, formuladestination);
                                                self.cellinfos[index]["formulaitems"][itemindex] = formula;
                                                self.cellinfos[index]["formulaitemsbak"][itemindex] = formula;
                                            }
                                        }
                                    }
                                }
                            }
                            namebox[i].checked = false;
                        }
                        // console.log(document.getElementById('formula').rows[1].cells);
                        $( this ).dialog( "close" );
                    },
                    取消: function()
                    {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                }
            });
        },
        //公式栏编辑公式回车
        formulaeditkeydown: function (){
            var self = this;
            if(event.keyCode==13)
            {
                var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                var sheet = spreadtemp.getSheet(0);
                var selectedRanges = sheet.getSelections();
                var selectedrow = selectedRanges[0].row;
                var selectedrowcount = selectedRanges[0].rowCount;
                var selectedcol = selectedRanges[0].col;
                var selectedcolcount = selectedRanges[0].colCount;

                if ((selectedrow < 0 ) || (selectedrow > sheet.getRowCount()))
                {
                    alert("选中区域的行不在表格范围内，请检查。")
                    window.event.returnValue = false;
                    return false;
                }

                if ((selectedcol < 0 ) || (selectedcol > sheet.getColumnCount()))
                {
                    alert("选中区域的列不在表格范围内，请检查。")
                    window.event.returnValue = false;
                    return false;
                }

                var data = sheet.getValue(selectedrow,selectedcol);

                var formulaBar = document.getElementById('formulaBar');
                var formula = formulaBar.innerHTML;
                if(formula == "" || formula == undefined || formula == null)
                {
                    if(confirm("定义的公式为空，将清除当前单元格原有公式，是否确定？"))
                    {
                        var destactionrangesrow = selectedrow;
                        var destactionrangescolnum = selectedcol;
                        var destactionrangeerow = selectedrow + selectedrowcount - 1;
                        var destactionrangeecolnum = selectedcol + selectedcolcount - 1;

                        // 删除定义但是未保存的公式
                        for(var i=0;i<self.cellinfos.length;i++)
                        {
                            // rows：控件选中区域开始行
                            // cols：控件选中区域开始列
                            // rowe：控件选中区域结束行
                            // cole：控件选中区域结束列

                            var rows = parseInt(self.cellinfos[i]["row"]);
                            var cols = parseInt(self.cellinfos[i]["col"]);

                            if (rows == destactionrangesrow && cols == destactionrangescolnum )
                            {
                                // self.cellinfos[i]["formula"] = "";
                                // self.cellinfos[i]["rowoffset"] = 0;
                                // self.cellinfos[i]["coloffset"] = 0;
                                // self.cellinfos[i]["formulaitems"] = [];              //四则运算的分解公式
                                // self.cellinfos[i]["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                // self.cellinfos[i]["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                // self.cellinfos[i]["formulaoperators"] = [];          //四则运算的运算符
                                // self.cellinfos[i]["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                // self.cellinfos[i]["newformula"] = "0";               //新增公式
                                self.cellinfos.splice(i,1); //是删除还是置空值得商榷

                                if(sheet.getComment(selectedrow, selectedcol))
                                {
                                    sheet.setComment(selectedrow, selectedcol, null);
                                    spreadtemp.refresh();
                                }
                            }
                        }
                    }
                    window.event.returnValue = false;
                    return false;
                }
                else {
                    if(formula.indexOf("=") == 0)
                    {
                        formula = formula.substring(1,formula.length);
                    }

                    var destactionrangesrow = selectedrow;
                    var destactionrangescolnum = selectedcol;
                    var destactionrangeerow = selectedrow + selectedrowcount - 1;
                    var destactionrangeecolnum = selectedcol + selectedcolcount - 1;

                    // 如果是新定义的那么需要更新系统变量self.cellinfos
                    if(self.cellinfos.length > 0)
                    {
                        for (var i = 0; i < self.cellinfos.length; i++)
                        {
                            // rows：控件选中区域开始行
                            // cols：控件选中区域开始列
                            // rowe：控件选中区域结束行
                            // cole：控件选中区域结束列

                            var rows = parseInt(self.cellinfos[i]["row"]);
                            var cols = parseInt(self.cellinfos[i]["col"]);
                            var rowe = rows + self.cellinfos[i]["rowoffset"];
                            var cole = cols + self.cellinfos[i]["coloffset"];

                            // if (rows == destactionrangesrow && cols == destactionrangescolnum && rowe == destactionrangeerow && cole == destactionrangeecolnum) {
                            // 存在则更新，不存在则插入
                            if (rows == destactionrangesrow && cols == destactionrangescolnum ) {
                                self.cellinfos[i]["formula"] = formula;
                                if (isNaN(data))
                                {
                                    self.cellinfos[i]["data"] = 0;
                                    self.cellinfos[i]["text"] = data;
                                }
                                else {
                                    self.cellinfos[i]["data"] = data;
                                    self.cellinfos[i]["text"] = "";
                                }
                                self.cellinfos[i]["rowoffset"] = destactionrangeerow - destactionrangesrow;
                                self.cellinfos[i]["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                                self.cellinfos[i]["formulaitems"] = [];              //四则运算的分解公式
                                self.cellinfos[i]["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                self.cellinfos[i]["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                self.cellinfos[i]["formulaoperators"] = [];          //四则运算的运算符
                                self.cellinfos[i]["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                self.cellinfos[i]["newformula"] = "1";               //新增公式
                            }
                            else {
                                var celldata = {};
                                celldata["row"] = String(destactionrangesrow);
                                celldata["col"] = String(destactionrangescolnum);
                                celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                                celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                                if (isNaN(data))
                                {
                                    celldata["data"] = 0;
                                    celldata["text"] = data;
                                }
                                else {
                                    celldata["data"] = data;
                                    celldata["text"] = "";
                                }
                                celldata["formula"] = formula;              //四则运算的整体公式
                                celldata["formulaitems"] = [];              //四则运算的分解公式
                                celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                celldata["formulaoperators"] = [];          //四则运算的运算符
                                celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                celldata["newformula"] = "1";               //新增公式
                                self.cellinfos.push(celldata);
                            }
                        }
                    }
                    else{
                        var celldata = {};
                        celldata["row"] = String(destactionrangesrow);
                        celldata["col"] = String(destactionrangescolnum);
                        celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                        celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                        if (isNaN(data))
                        {
                            celldata["data"] = 0;
                            celldata["text"] = data;
                        }
                        else {
                            celldata["data"] = data;
                            celldata["text"] = "";
                        }
                        celldata["formula"] = formula;              //四则运算的整体公式
                        celldata["formulaitems"] = [];              //四则运算的分解公式
                        celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                        celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                        celldata["formulaoperators"] = [];          //四则运算的运算符
                        celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                        celldata["newformula"] = "1";               //新增公式
                        self.cellinfos.push(celldata);
                    }
                }
                window.event.returnValue=false;
            }
        },
        //公式定义向导
        rightmenu_formula_guide: function (){
            var formulas = [];
            var formulascustom = [];
            var params = [];
            var paramscustom = [];

            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentyear = date.substring(0,4);
            var currentdate = date.substring(5,7);

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var selectedRanges = sheet.getSelections();
            var selectedrow = selectedRanges[0].row;
            var selectedrowcount = selectedRanges[0].rowCount;
            var selectedcol = selectedRanges[0].col;
            var selectedcolcount = selectedRanges[0].colCount;

            var data = sheet.getValue(selectedrow,selectedcol);

            if ((selectedrow < 0 ) || (selectedrow > sheet.getRowCount()))
            {
                alert("选中区域的行不在表格范围内，请检查。")
                window.event.returnValue = false;
                return false;
            }

            if ((selectedcol < 0 ) || (selectedcol > sheet.getColumnCount()))
            {
                alert("选中区域的列不在表格范围内，请检查。")
                window.event.returnValue = false;
                return false;
            }

            var selectedrange = "";
            var rangestartrow = "";
            var rangestartcol = "";
            var rangeendrow = "";
            var rangeendcol = "";
            if (selectedrow == -1)
            {
                rangestartrow = 1
            }
            else
            {
                rangestartrow = selectedrow + 1;
            }
            rangeendrow = rangestartrow + selectedrowcount - 1;
            rangestartcol = sheet.getText(0, selectedcol,GcSpread.Sheets.SheetArea.colHeader);
            rangeendcol = sheet.getText(0, selectedcol+selectedcolcount - 1,GcSpread.Sheets.SheetArea.colHeader);
            selectedrange = rangestartcol+rangestartrow+":"+rangeendcol+rangeendrow;

            var $div=$("<div>",{id:"dialog-message",title:"公式定义向导"});
            var $sectop = $("<section class=\"formulaguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"formulaguidetop\">");

            var $secleft = $("<section class=\"formulalist\" style=\"float:left;height: 100%;width: 35%;\" id=\"formulalist\">");
            // $secleft.append('<select style= "height:21px" name="formulas" id="formulas" onchange="formulas_select_change()"></select>');
            $secleft.append('<select style= "height:21px" name="formulas" id="formulas" ></select>');

            var $secright = $("<section class=\"formulaoperate\" id=\"formulaoperate\" style=\"float:right;height: 100%;width: 60%;overflow: hidden;\" >");
            var $secrightleft = $("<section class=\"formulaoperateselect\" id=\"formulaoperateselect\" style=\"float:left;height: 100%;width: 40%;\" >");
            var $secrightleftleft = $("<section class=\"formulaoperateselectlabel\" id=\"formulaoperateselectlabel\" style=\"float:left;height: 100%;width: 50%;\" >");
            var $secrightleftright = $("<section class=\"formulaoperateselectselect\" id=\"formulaoperateselectselect\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $secrightright = $("<section class=\"formulaoperateaddbutton\" id=\"formulaoperateaddbutton\" style=\"float:right;height: 100%;width: 50%;\" >");

            var $p1=$("<p style='width:70px;height:21px;'>").html("运算符号：");
            $secrightleftleft.append($p1);
            $secrightleftright.append('<select style="height:21px;width:60px;" name="operation" id="operation">\n' +
                        '\t\t\t<option value ="plus" selected = "selected">+</option>\n' +
                        '\t\t\t<option value ="minus">-</option>\n' +
                        '\t\t</select>');
            $secrightright.append('<input type="button" name="addformula" id="addformula" style=\"width:80px;height:21px;\" value=\"添加公式\"/> ');

            $secrightleft.append($secrightleftleft);
            $secrightleft.append($secrightleftright);

            $secright.append($secrightleft);
            $secright.append($secrightright);

            $sectop.append($secleft);
            $sectop.append($secright);

            $div.append($sectop);

            var $secinstruction = $("<section class=\"instruction\" id=\"instruction\" style=\"height: 100%;width: 100%;\">");
            var $instructiontitle = $("<p class=\"instructiontitle\" id=\"instructiontitle\" >").html("<strong>使用说明及示例：</strong>");
            $secinstruction.append($instructiontitle);
            var $instructioncontent = $("<p class=\"instructioncontent\" id=\"instructioncontent\" style=\"border:1px rgb(169,169,169) solid;\">").html("从报表管理系统中取数，示例：=BB(0,0,0001,C6)");
            $secinstruction.append($instructioncontent);

            $div.append($secinstruction);

            var $secfunctionparams = $("<section class=\"functionparams\" id=\"functionparams\" style=\"height: 100%;width: 100%;overflow: hidden;margin-top: 20px;\" >");
            $div.append($secfunctionparams);

            var $secformulaarithmetic = $("<section class=\"formulaarithmetic\" id=\"formulaarithmetic\" style=\"height: 100%;width: 100%;margin-top: 20px;\" >");
            var $arithmetictable = $("<table class=\"arithmetictable\" id=\"arithmetictable\" >");
            // var $arithmetictablehead = $('<thead class="arithmetictablehead" id="arithmetictablehead"><tr><th>公式</th><th>运算符号</th><th>数值</th><th>操作</th></tr></thead>');
            var $arithmetictablehead = $('<thead class="arithmetictablehead" id="arithmetictablehead"><tr><th>公式</th><th>运算符号</th><th>操作</th></tr></thead>');
            $arithmetictable.append($arithmetictablehead);
            var $arithmetictablebody = $('<tbody class="arithmetictablebody" id="arithmetictablebody"></tbody>');

            var formula = "";

            var self = this;
            var defgetformula = this._rpc({
                model: 'ps.statement.sheet.cells',
                method: 'get_cell_formula',
                args: [this.code,this.date,selectedrow,selectedcol]
            }).then(function (result)
            {
                if (!result || result == "")
                {
                    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                    var activeSheet = spreadtemp.getSheet(0);
                    var formula = activeSheet.getFormula(selectedrow,selectedcol);
                    if (formula)
                    {
                        if (formula.indexOf("EVAL") == 0)
                        {
                            formula = formula.substring(6,formula.length);
                            formula = formula.substring(0,formula.length - 2);
                            formula = "=" + formula;
                        }
                    }
                }
                if (result)
                {
                    var temp = "";
                    try {
                        temp = result[0].cell_formula;
                    }
                    catch (err) {
                        temp = "";
                    }
                    if (temp) {
                        formula = temp;
                    }
                }
                var amountvalue = 0;

                if (self.cellinfos.length > 0)
                {
                    var destactionrangesrow = selectedrow;
                    var destactionrangescolnum = selectedcol;
                    var destactionrangeerow = selectedrow + selectedrowcount - 1;
                    var destactionrangeecolnum = selectedcol + selectedcolcount - 1;
                    for(var i=0;i<self.cellinfos.length;i++)
                    {
                       // rows：控件选中区域开始行
                       // cols：控件选中区域开始列
                       // rowe：控件选中区域结束行
                       // cole：控件选中区域结束列

                        var rows = parseInt(self.cellinfos[i]["row"]);
                        var cols = parseInt(self.cellinfos[i]["col"]);
                        var rowe = rows + self.cellinfos[i]["rowoffset"];
                        var cole = cols + self.cellinfos[i]["coloffset"];

                        if (rows == destactionrangesrow && cols == destactionrangescolnum && rowe == destactionrangeerow && cole == destactionrangeecolnum) {
                            formula = self.cellinfos[i]["formula"];
                        }
                    }
                }

                if (formula)
                {
                    var formulasbyone = {};
                    var formulaunit = [];
                    var operators = [];
                    var resultformulas = false;

                    var defget_formula_from_arithmetic = self._rpc({
                        model: 'ps.statement.sheet.cells',
                        method: 'get_formula_from_arithmetic',
                        args: [formula, formulasbyone, formulaunit, operators]
                    }).then(function (result)
                    {
                        if (result)
                        {
                            formulasbyone = result[0];
                            formulaunit = result[1];
                            operators = result[2];
                            for(var i = 0;i < formulaunit.length;i++ )
                            {
                                var $tr = $("<tr>");
                                // var $td1 = $("<td width='100px'>");
                                // var temp = formulaunit[i];
                                // if (formulaunit[i].indexOf("=") == 0)
                                // {
                                //     temp = formulaunit[i].substring(1,formulaunit[i].length);
                                // }
                                // $td1.html(temp);

                                var temp = formulaunit[i];
                                if (formulaunit[i].indexOf("=") == 0)
                                {
                                    temp = formulaunit[i].substring(1,formulaunit[i].length);
                                }
                                var $td1=$("<td width='400px'>");
                                var $input=$("<input>",{"name":"inputaddformula","class":"inputaddformula","id":"inputaddformula","type":"text"});
                                $input.val(temp);
                                $td1.append($input);

                                var operator = operators[i];
                                if (!operator)
                                {
                                    operator = "";
                                }

                                var $td2=$("<td width='100px'>");
                                var $input=$("<input>",{"name":"inputaddoperator","class":"inputaddoperator","id":"inputaddoperator","type":"text"});
                                $input.val(operator);
                                $td2.append($input);

                                // var $td2 = $("<td width='100px'>");
                                // var operator = operators[i];
                                // if (operator)
                                // {
                                //     $td2.html(operator);
                                // }
                                // else
                                // {
                                //     $td2.html("+");
                                // }

                                // var $td3 = $("<td id = 'formulavalue'+string(i) width='100px'>");
                                // var formulavalue = "0";
                                // amountvalue = parseInt(amountvalue)+parseInt(formulavalue);
                                // $td3.html(formulavalue);
                                var $td4=$("<td width='100px'>");
                                var $a = $("<a>",{"href":"javascript:;","onclick":'{if(confirm("确定要删除当前选中公式记录吗?")) {deleteCurrentRow(this); }else {}}'});
                                $a.html("删除公式");
                                $td4.append($a);

                                $tr.append($td1);
                                $tr.append($td2);
                                // $tr.append($td3);
                                $tr.append($td4);

                                $arithmetictablebody.append($tr);
                            }
                        }
                    });
                }

                // var $arithmetictablefoot = $('<tfoot class="arithmetictablefoot" id="arithmetictablefoot"></tfoot>');
                //
                // var $td1 = $("<td width='100px'>");
                // $td1.html("<strong>合计</strong>");
                // var $td2 = $("<td width='100px'>");
                // $td2.html("");
                // var $td3 = $("<td width='100px'>");
                //
                // $td3.html(amountvalue);
                // var $td4=$("<td width='100px'>");
                // $td4.html("");
                //
                // $arithmetictablefoot.append($td1);
                // $arithmetictablefoot.append($td2);
                // $arithmetictablefoot.append($td3);
                // $arithmetictablefoot.append($td4);

                $arithmetictable.append($arithmetictablebody);
                // $arithmetictable.append($arithmetictablefoot);
                $secformulaarithmetic.append($arithmetictable);
            });

            $div.append($secformulaarithmetic);

            var formulaparams = {};
            var defgetformulaparams = this._rpc({
                model: 'ps.statement.sheet.cells',
                method: 'split_formula',
                args: [formula,formulaparams]
            }).then(function (result)
            {
                if (result)
                {
                    formulaparams = result;
                }
            });
            // 系统公式
            var defgetfunctions = this._rpc({
                model: 'ps.statement.functions',
                method: 'get_functions',
            }).then(function (result) {
                if (result)
                {
                    //(完整菜单，后期按需取消注释)
                    // formulas = result;
                    // for(var i=0;i < result.length;i++)
                    // {
                    //     if (result[i].name == "BB")
                    //     {
                    //         $("#formulas").append("<option value='"+result[i].id+"' selected = \"selected\">"+result[i].name +"#"+ result[i].func_summary+"#</option>");
                    //     }
                    //     else
                    //     {
                    //         $("#formulas").append("<option value='"+result[i].id+"'>"+result[i].name +"#"+ result[i].func_summary+"#</option>");
                    //     }
                    // }
                    // 系统公式(暂时版)
                    var option0 = "BB#报表函数#";
                    var option1 = "KMJE#科目金额函数#";
                    $("#formulas").append("<option value='1' selected = \"selected\">"+ option0 +"</option>");
                    $("#formulas").append("<option value='2' >"+ option1 +"</option>");
                }
            });

            //自定义公式
            var defgetfunctions = this._rpc({
                model: 'ps.statement.formulas',
                method: 'get_formulas',
            }).then(function (result) {
                if (result)
                {
                    formulascustom = result;
                    for(var i=0;i < result.length;i++)
                    {
                        $("#formulas").append("<option value='"+result[i].id+"'>"+result[i].name +"#"+ result[i].formula_summary+"#</option>");
                    }
                }
            });

            // 系统公式参数
            var defgetfunctionsparams = this._rpc({
                model: 'ps.statement.function.params',
                method: 'get_function_params',
            }).then(function (result) {
                if (result)
                {
                    params = result;
                    var paramsbyid = [];
                    for(var i=0;i < params.length;i++)
                    {
                        var formulaid = $('#formulas').find('option:selected').attr('value');
                        var funcid = params[i]["func_id"].substring(params[i]["func_id"].indexOf("(")+1,params[i]["func_id"].indexOf(","));
                        if(funcid==formulaid){
                            paramsbyid.push(params[i]);
                        }
                    }
                    for(var i=0;i < paramsbyid.length;i++)
                    {
                        var paramid = paramsbyid[i]["param_id"];
                        var paramdescription = paramsbyid[i]["param_description"];

                        var $secfunctionparamsleft = $("<section class=\"functionparamsdescription\" style=\"display: inline-block;height: 100%;width: 14%;\" id=\"functionparamsdescription\">");
                        var $secfunctionparamsright = $("<section class=\"functionparamsinput\" style=\"display: inline-block;height: 100%;width: 33%;\" id=\"functionparamsinput\">");
                        if(i==1||i==3||i==5){
                            $secfunctionparamsleft.css("margin-left","5%");
                        }
                        var $p=$("<p align=\"right\">").html(paramdescription);
                        $secfunctionparamsleft.append($p);
                        var inputvalue = "";
                        if (paramdescription == "Fiscal year")
                        {
                            inputvalue = currentyear;
                        }
                        if (paramdescription == "Accounting interval")
                        {
                            inputvalue = currentdate;
                        }
                        if (paramdescription == "Report number")
                        {
                            inputvalue = self.code;
                        }
                        var $inputparam = $("<input>",{"name":"param","class":"param","id":"param","type":"text"});
                        $inputparam.val(inputvalue);
                        $secfunctionparamsright.append($inputparam);

                        $secfunctionparams.append($secfunctionparamsleft);
                        $secfunctionparams.append($secfunctionparamsright);
                    }
                }
            });

            //自定义公式参数
            var defgetfunctionsparams = this._rpc({
                model: 'ps.statement.formula.params',
                method: 'get_formula_params',
            }).then(function (result) {
                if (result)
                {
                    paramscustom = result;
                }
            });

            var $secactionrange = $("<section class=\"actionrange\" id=\"actionrange\" style=\"width: 100%;overflow: hidden;margin-top: 20px;\">");
            var $secactionrangeleft = $("<section class=\"actionrangeleft\" id=\"actionrangeleft\" style=\"float:left;width: 49%;overflow: hidden;\" >");
            var $secactionrangeleftleft = $("<section class=\"actionrangeleftleft\" id=\"actionrangeleftleft\" style=\"float:left;width: 35%;\" >");
            var $secactionrangeleftright = $("<section class=\"actionrangeleftright\" id=\"actionrangeleftright\" style=\"float:right;width: 65%;\" >");
            var $secactionrangeright = $("<section class=\"actionrangeright\" id=\"actionrangeright\" style=\"float:right;width: 49%;overflow: hidden;\" >");
            var $secactionrangerightleft = $("<section class=\"actionrangerightleft\" id=\"actionrangerightleft\" style=\"float:left;width: 35%;\" >");
            var $secactionrangerightright = $("<section class=\"actionrangerightright\" id=\"actionrangerightright\" style=\"float:right;width: 65%;\" >");

            var $psrc=$("<p>").html("当前作用范围：");
            $secactionrangeleftleft.append($psrc);
            var $inputactionrangesrc = $("<input>",{"name":"actionrangesrc","class":"actionrangesrc","id":"actionrangesrc","type":"text","readonly":"readonly"});
            $inputactionrangesrc.val(selectedrange);
            $secactionrangeleftright.append($inputactionrangesrc);

            var $pdest=$("<p>").html("目标作用范围：");
            $secactionrangerightleft.append($pdest);
            var $inputactionrangedest = $("<input>",{"name":"actionrangedest","class":"actionrangedest","id":"actionrangedest","type":"text"});
            $inputactionrangedest.val(selectedrange);
            $secactionrangerightright.append($inputactionrangedest);

            $secactionrangeleft.append($secactionrangeleftleft);
            $secactionrangeleft.append($secactionrangeleftright);
            $secactionrangeright.append($secactionrangerightleft);
            $secactionrangeright.append($secactionrangerightright);
            $secactionrange.append($secactionrangeleft);
            $secactionrange.append($secactionrangeright);
            $div.append($secactionrange);

            $div.dialog({
                modal: true,
                width:600,
                buttons: {
                    确定: function()
                    {
                        var formula = "";
                        var tbl = document.getElementById("arithmetictable");
                        var trs = tbl.getElementsByTagName("tr");
                        var inputaddformulas = $("input[name='inputaddformula']");  //获取name值为inputaddformula的所有input
                        var inputaddoperators = $("input[name='inputaddoperator']");  //获取name值为inputaddformula的所有input

                        for(var i = 0; i < inputaddformulas.length; i++)
                        {
                            var temp = inputaddformulas[i].value;
                            var operator = inputaddoperators[i].value;

                            if(temp)
                            {
                                formula = formula + temp;
                            }
                            if (operator)
                            {
                                formula = formula + operator;
                            }
                        }

                        formula = formula.substring(0,formula.length - 1);

                        if (formula.length != 0 )
                        {
                            // if(formula.indexOf("=") == 0)
                            // {
                            //     formula = formula.substring(1,formula.length);
                            // }
                            // // formula = 'EVAL("' + formula+ '")';
                        }
                        else
                        {
                            formula = "";
                        }

                        var destactionrange = "";
                        var actionrangeinputs = document.querySelectorAll("input");
                        for(var i=0;i < actionrangeinputs.length;i++)
                        {
                            if (actionrangeinputs[i] != null && actionrangeinputs[i].name == "actionrangedest")
                            {
                                destactionrange = actionrangeinputs[i].value;
                            }
                        }
                        if (destactionrange) {
                            var destactionrangefront = "";
                            var destactionrangelatter = "";
                            var destactionrangesrow = 0;
                            var destactionrangeerow = 0;
                            var destactionrangescol = "";
                            var destactionrangeecol = "";
                            var destactionrangescolnum = 0;
                            var destactionrangeecolnum = 0;

                            destactionrangefront = destactionrange.substring(0, destactionrange.indexOf(":"));
                            destactionrangelatter = destactionrange.substring(destactionrange.indexOf(":") + 1,destactionrange.length);

                            if(destactionrangefront)
                            {
                                var temp = destactionrangefront.substring(1,2);

                                if(isNaN(temp))
                                {
                                    destactionrangescol = destactionrangefront.substring(0,2);
                                    destactionrangesrow = destactionrangefront.substring(2,destactionrangefront.length) - 1;

                                    var tmp1 = destactionrangescol.substring(0,1);
                                    var temp1 = tmp1.charCodeAt() - 64;

                                    var tmp2 = destactionrangescol.substring(1,2);
                                    var temp2 = tmp2.charCodeAt() - 64;
                                    destactionrangescolnum = temp1*26 + temp2 - 1;

                                }
                                else
                                {
                                    destactionrangescol = destactionrangefront.substring(0,1);
                                    destactionrangesrow = destactionrangefront.substring(1,destactionrangefront.length) - 1;

                                    destactionrangescolnum = destactionrangescol.charCodeAt() - 64 - 1;
                                }
                            }

                            if(destactionrangelatter)
                            {
                                var temp = destactionrangelatter.substring(1,2);

                                if(isNaN(temp))
                                {
                                    destactionrangeecol = destactionrangelatter.substring(0,2);
                                    destactionrangeerow = destactionrangelatter.substring(2,destactionrangelatter.length) - 1;

                                    var tmp1 = destactionrangeecol.substring(0,1);
                                    var temp1 = tmp1.charCodeAt() - 64;

                                    var tmp2 = destactionrangeecol.substring(1,2);
                                    var temp2 = tmp2.charCodeAt() - 64;
                                    destactionrangeecolnum = temp1*26 + temp2 - 1;
                                }
                                else
                                {
                                    destactionrangeecol = destactionrangelatter.substring(0,1);
                                    destactionrangeerow = destactionrangelatter.substring(1,destactionrangelatter.length) - 1;

                                    destactionrangeecolnum = destactionrangeecol.charCodeAt() - 64 - 1;
                                }
                            }
                        }

                        if (self.cellinfos.length > 0)
                        {
                            for (var i = 0; i < self.cellinfos.length; i++)
                            {
                                // rows：控件选中区域开始行
                                // cols：控件选中区域开始列
                                // rowe：控件选中区域结束行
                                // cole：控件选中区域结束列

                                var rows = parseInt(self.cellinfos[i]["row"]);
                                var cols = parseInt(self.cellinfos[i]["col"]);

                                if (rows == destactionrangesrow && cols == destactionrangescolnum)
                                {
                                    if (formula == "")
                                    {
                                        self.cellinfos[i]["formula"] = "";
                                        self.cellinfos[i]["rowoffset"] = 0;
                                        self.cellinfos[i]["coloffset"] = 0;
                                        self.cellinfos[i]["formulaitems"] = [];              //四则运算的分解公式
                                        self.cellinfos[i]["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                        self.cellinfos[i]["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                        self.cellinfos[i]["formulaoperators"] = [];          //四则运算的运算符
                                        self.cellinfos[i]["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                        self.cellinfos[i]["newformula"] = "0";               //新增公式
                                    }
                                    else {
                                        self.cellinfos[i]["formula"] = formula;
                                        self.cellinfos[i]["rowoffset"] = destactionrangeerow - destactionrangesrow;
                                        self.cellinfos[i]["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                                        self.cellinfos[i]["formulaitems"] = [];              //四则运算的分解公式
                                        self.cellinfos[i]["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                        self.cellinfos[i]["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                        self.cellinfos[i]["formulaoperators"] = [];          //四则运算的运算符
                                        self.cellinfos[i]["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                        self.cellinfos[i]["newformula"] = "1";               //新增公式
                                    }
                                }
                                else {
                                    var celldata = {};
                                    celldata["row"] = String(destactionrangesrow);
                                    celldata["col"] = String(destactionrangescolnum);
                                    celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                                    celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                                    if (isNaN(data)) {
                                        celldata["data"] = 0;
                                        celldata["text"] = data;
                                    }
                                    else {
                                        celldata["data"] = data;
                                        celldata["text"] = "";
                                    }
                                    celldata["formula"] = formula;              //四则运算的整体公式
                                    celldata["formulaitems"] = [];              //四则运算的分解公式
                                    celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                                    celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                                    celldata["formulaoperators"] = [];          //四则运算的运算符
                                    celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                                    celldata["newformula"] = "1";               //新增公式
                                    self.cellinfos.push(celldata);
                                }
                            }
                        }
                        else{
                            var celldata = {};
                            celldata["row"] = String(destactionrangesrow);
                            celldata["col"] = String(destactionrangescolnum);
                            celldata["rowoffset"] = destactionrangeerow - destactionrangesrow;
                            celldata["coloffset"] = destactionrangeecolnum - destactionrangescolnum;
                            if (isNaN(data)) {
                                celldata["data"] = 0;
                                celldata["text"] = data;
                            }
                            else {
                                celldata["data"] = data;
                                celldata["text"] = "";
                            }
                            celldata["formula"] = formula;              //四则运算的整体公式
                            celldata["formulaitems"] = [];              //四则运算的分解公式
                            celldata["formulaitemsbak"] = [];           //四则运算的分解公式备份
                            celldata["formulaitemsvalue"] = [];         //四则运算的分解公式的值
                            celldata["formulaoperators"] = [];          //四则运算的运算符
                            celldata["formulaitemscalculated"] = [];    //四则运算的分解公式是否已经计算
                            celldata["newformula"] = "1";               //新增公式
                            self.cellinfos.push(celldata);
                        }

                        var formulaBar = document.getElementById('formulaBar');
                        if(formula.indexOf("=") != 0)
                        {
                            formula = "=" + formula;
                        }
                        formulaBar.innerHTML = formula;

                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                    取消: function()
                    {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                },
                close: function(event, ui)
                {
                    $div.empty();
                }
            });

            $(document).ready(function () {
                //公式选择函数
                $("#formulas").bind("change",function()
                {
                    if($(this).val()==0)
                    {
                        return;
                    }
                    else{
                        var formulaid = $('#formulas').find('option:selected').attr('value');
                        var formulaname = $('#formulas').find('option:selected').text();
                        formulaname = formulaname.substring(0,formulaname.indexOf("#"));
                        var formulainstruction = "从报表管理系统中取数，示例：=BB(0,0,0001,C6)";

                        for (var i=0;i<formulas.length;i++)
                        {
                            if(formulas[i]["id"]==formulaid && formulas[i]["name"] == formulaname){
                                formulainstruction = formulas[i]["func_note"];
                                break;
                            }
                        }

                        for (var i=0;i<formulascustom.length;i++)
                        {
                            if(formulascustom[i]["id"]==formulaid && formulascustom[i]["name"] == formulaname){
                                formulainstruction = formulascustom[i]["formula_note"];
                                break;
                            }
                        }

                        if (!formulainstruction)
                        {
                            formulainstruction = "示例：";
                        }
                        $("#instructioncontent").text(formulainstruction);

                        var paramsbyid = [];
                        for(var i=0;i < params.length;i++)
                        {
                            var formulaid = $('#formulas').find('option:selected').attr('value');
                            var funcid = params[i]["func_id"].substring(params[i]["func_id"].indexOf("(")+1,params[i]["func_id"].indexOf(","));

                            if (funcid == formulaid)
                            {
                                paramsbyid.push(params[i]);
                            }
                        }

                        var paramsbyidcustom = [];
                        for(var i=0;i < paramscustom.length;i++)
                        {
                            var formulaid = $('#formulas').find('option:selected').attr('value');
                            var temp = paramscustom[i]["formula_id"];
                            var funcid = temp.substring(temp.indexOf("(")+1,temp.indexOf(","));

                            if (funcid == formulaid)
                            {
                                paramsbyidcustom.push(paramscustom[i]);
                            }
                        }

                        if(paramsbyid.length > 0 && paramsbyidcustom.length > 0)
                        {
                            paramsbyid = paramsbyidcustom;
                        }

                        $secfunctionparams.empty();
                        for(var i=0;i < paramsbyid.length;i++)
                        {
                            var paramid = paramsbyid[i]["param_id"];
                            var paramdescription = paramsbyid[i]["param_description"];

                            var $secfunctionparamsleft = $("<section class=\"functionparamsdescription\" style=\"display: inline-block;height: 100%;width: 14%;\" id=\"functionparamsdescription\">");
                            var $secfunctionparamsright = $("<section class=\"functionparamsinput\" style=\"display: inline-block;height: 100%;width: 33%;\" id=\"functionparamsinput\">");
                            if(i==1||i==3||i==5){
                                $secfunctionparamsleft.css("margin-left","5%");
                            }
                            var $p=$("<p align=\"right\">").html(paramdescription);
                            $secfunctionparamsleft.append($p);
                            var inputvalue = "";
                            if (paramdescription == "Fiscal year" || paramdescription == "Accounting interval")
                            {
                                inputvalue = "0";
                            }
                            if (paramdescription == "Report number")
                            {
                                inputvalue = self.code;
                            }
                            var $inputparam = $("<input>",{"name":"param","class":"param","id":"param","type":"text"});
                            $inputparam.val(inputvalue);
                            $secfunctionparamsright.append($inputparam);

                            $secfunctionparams.append($secfunctionparamsleft);
                            $secfunctionparams.append($secfunctionparamsright);
                        }
                    }
                });
                //添加公式函数
                $("#addformula").click(function()
                {
                    var formula = "";
                    var formulaname = $('#formulas').find('option:selected').text();
                    formulaname = formulaname.substring(0,formulaname.indexOf("#"));
                    // var tbl = document.getElementById("arithmetictable");
                    // var trs = tbl.getElementsByTagName("tr");
                    formula = formulaname+"(";

                    var paramsbyid = [];
                    for(var i=0;i < params.length;i++)
                    {
                        var formulaid = $('#formulas').find('option:selected').attr('value');
                        var funcid = params[i]["func_id"].substring(params[i]["func_id"].indexOf("(")+1,params[i]["func_id"].indexOf(","));
                        if(funcid==formulaid){
                            paramsbyid.push(params[i]);
                        }
                    }

                    var paraminputs = document.querySelectorAll("input");
                    for(var i=0;i < paraminputs.length;i++)
                    {
                        if(paraminputs[i] != null && paraminputs[i].name == "param")
                        {
                            var temp = paraminputs[i].value;
                            if (temp == "")
                            {
                                formula = formula + "'',";
                            }
                            else
                            {
                                formula = formula + temp+",";
                            }
                        }
                    }
                    formula = formula.substring(0,formula.length - 1);
                    formula = formula + ")";

                    var $tr = $("<tr>");
                    // var $td1 = $("<td width='100px'>");
                    // $td1.html(formula);

                    var $td1=$("<td width='400px'>");
                    var $input=$("<input>",{"name":"inputaddformula","class":"inputaddformula","id":"inputaddformula","type":"text"});
                    $input.val(formula);
                    $td1.append($input);

                    // var $td2 = $("<td width='100px'>");
                    // var operator = $('#operation').find('option:selected').text();
                    // $td2.html(operator);

                    var operator = $('#operation').find('option:selected').text();
                    var $td2=$("<td width='100px'>");
                    var $input=$("<input>",{"name":"inputaddoperator","class":"inputaddoperator","id":"inputaddoperator","type":"text"});
                    $input.val(operator);
                    $td2.append($input);

                    // var $td3 = $("<td id = 'formulavalue'+string(i) width='100px'>");
                    // var formulavalue = "0";
                    // // amountvalue = parseInt(amountvalue)+parseInt(formulavalue);
                    // $td3.html(formulavalue);
                    var $td4=$("<td width='100px'>");
                    var $a = $("<a>",{"href":"javascript:;","onclick":'{if(confirm("确定要删除当前选中公式记录吗?")) {deleteCurrentRow(this); }else {}}'});
                    $a.html("删除公式");
                    $td4.append($a);

                    $tr.append($td1);
                    $tr.append($td2);
                    // $tr.append($td3);
                    $tr.append($td4);

                    $arithmetictablebody.append($tr);
                });
            });
        },
        //金额单位调整
        monetaryunitadjust: function (){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);

            var $div=$("<div>",{id:"dialog-message",title:"选择金额单位"});
            var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("金额单位是必选的。");
            $div.append($paa);
            var $p=$("<p>").html("金额单位");
            $div.append($p);
            var $sec = $('<select style= "height:21px" name="monetaryunit" id="monetaryunit" ></select>');
            $div.append($sec);

            var monetaryunits = {};
            var defmonetaryunit = self._rpc({
                model: 'ps.statement.monetaryunit.define',
                method: 'get_monetaryunit',
            }).then(function (result) {
                if (result)
                {
                    monetaryunits = result;
                    for(var i=0;i < result.length;i++)
                    {
                        if (i == 0)
                        {
                            $("#monetaryunit").append("<option value='"+result[i].id+"' selected = \"selected\">"+result[i].code + "#" + result[i].name + "</option>");
                        }
                        else
                        {
                            $("#monetaryunit").append("<option value='"+result[i].id+"'>" + result[i].code + "#" + result[i].name + "</option>");
                        }
                    }
                }
            });

            $div.dialog({
                modal: true,
                buttons: {
                    确定: function() {
                        var monetaryunitid = $('#monetaryunit').find('option:selected').attr('value');

                        var monetaryunit = {};
                        for(var i=0;i < monetaryunits.length;i++)
                        {
                            if (monetaryunits[i]["id"] == monetaryunitid)
                            {
                                monetaryunit["id"] = monetaryunitid;
                                monetaryunit["code"] = monetaryunits[i].code;
                                monetaryunit["name"] = monetaryunits[i].name;
                                monetaryunit["operator"] = monetaryunits[i].operator;
                                monetaryunit["coefficient"] = monetaryunits[i].coefficient;
                                monetaryunit["precision"] = monetaryunits[i].precision;
                                monetaryunit["monetaryunit"] = monetaryunits[i].monetaryunit;
                                break;
                            }
                        }

                        // 新生成报表，编号是当前报表编号+调整编号，同时调整列的内容全部按照规则处理

                        var args = [self.code,currentdate,monetaryunit];
                        var defmonetaryunitadjust = self._rpc({
                            model: 'ps.statement.statements',
                            method: 'monetaryunitadjust',
                            args: args,
                        }).then(function (result) {
                            if (result)
                            {
                                self.do_action
                                ({
                                    type: 'ir.actions.client',
                                    tag: 'statements',
                                    context : {
                                        'report_code' : self.code + "_" + monetaryunits[i].code,
                                        'report_name' : self.sheetname + "_" + monetaryunit["name"],
                                        'report_date' : currentdate,
                                        'category'  : self.category,
                                        'titlerows' : self.titlerows,
                                        'headrows' : self.headrows,
                                        'bodyrows' : self.bodyrows,
                                        'tailrows' : self.tailrows,
                                        'bodycols' : self.bodycols,
                                    },
                                 },
                                 {   on_reverse_breadcrumb: function ()
                                     {
                                         self.reload();
                                         },
                                     on_close: function ()
                                     {
                                         self.reload();
                                     }
                                 });

                                alert("生成金额单位调整表成功。");
                            }
                        });

                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                    取消: function() {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                }
            });
            $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});
        },
        //数据透视定义
        pivotdefine: function (){
            var self = this;
            self.do_action({
                name: '数据透视',
                type: 'ir.actions.act_window',
                res_model: 'ps.statement.pivot',
                views: [[false, 'list'], [false, 'form']],
                view_type: 'list',
                view_mode: 'form',
                target: 'current',
                context: {report_code: self.code,report_date:self.date,},
                domain: [['report_code', '=', self.code]],
            });
        },
        //数据透视
        pivot: function (){
            var self = this;
            var setctions = document.querySelectorAll("section");
            var date = setctions[0].childNodes[3].value;
            var currentdate = date.substring(0,4)+date.substring(5,7);

            var code = this.code;
            var date = this.date ;

            var $div=$("<div>",{id:"dialog-message",title:"选择数据透视"});
            var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("数据透视是必选的。");
            $div.append($paa);

            var $pinterval=$("<p>").html("区间");
            $div.append($pinterval);

            var $secactioninterval = $("<section class=\"secactioninterval\" id=\"secactioninterval\" style=\"width: 100%;overflow: hidden;\">");
            var $secactionintervalleft = $("<section class=\"secactionintervalleft\" id=\"secactionintervalleft\" style=\"float:left;width: 50%;overflow: hidden;\" >");
            var $secactionintervalleftleft = $("<section class=\"secactionintervalleftleft\" id=\"secactionintervalleftleft\" style=\"float:left;width: 90%;\" >");
            var $secactionintervalleftright = $("<section class=\"secactionintervalleftright\" id=\"secactionintervalleftright\" style=\"float:right;width: 10%;\" >");
            var $secactionintervalright = $("<section class=\"secactionintervalright\" id=\"secactionintervalright\" style=\"float:right;width: 50%;overflow: hidden;\" >");

            var $inputstart=$("<input>",{"name":"inputintervalstart","class":"inputintervalstart","id":"inputintervalstart","type":"month"});
            $inputstart.val(date.substring(0,4)+"-"+date.substring(4,6));
            $secactionintervalleftleft.append($inputstart);
            var $pp=$("<p>").html("至");
            $secactionintervalleftright.append($pp);

            var $inputend=$("<input>",{"name":"inputintervalend","class":"inputintervalend","id":"inputintervalend","type":"month"});
            $inputend.val(date.substring(0,4)+"-"+date.substring(4,6));
            $secactionintervalright.append($inputend);

            $secactionintervalleft.append($secactionintervalleftleft);
            $secactionintervalleft.append($secactionintervalleftright);
            $secactioninterval.append($secactionintervalleft);
            $secactioninterval.append($secactionintervalright);
            $div.append($secactioninterval);

            var $p=$("<p>").html("数据透视");
            $div.append($p);
            var $sec = $('<select style= "height:21px" name="pivottable" id="pivottable" ></select>');
            $div.append($sec);

            var pivottables = {};
            var pivotdetails = {};
            var args = [code,date];
            var defmonetaryunit = self._rpc({
                model: 'ps.statement.pivot',
                method: 'get_pivottable',
                args: args,
            }).then(function (result) {
                if (result)
                {
                    pivottables = result[0];
                    for(var i=0;i < pivottables.length;i++)
                    {
                        if (i == 0)
                        {
                            $("#pivottable").append("<option value='"+pivottables[i].id+"' selected = \"selected\">" + pivottables[i].code + "#" + pivottables[i].name + "</option>");
                        }
                        else
                        {
                            $("#pivottable").append("<option value='"+pivottables[i].id+"'>" + pivottables[i].code + "#" + pivottables[i].name + "</option>");
                        }
                    }
                    pivotdetails = result[1];
                }
            });

            $div.dialog({
                modal: true,
                width:350,
                buttons: {
                    确定: function() {
                        var pivottableid = $('#pivottable').find('option:selected').attr('value');
                        var intervalstart = $('#inputintervalstart').val();
                        var intervalend = $('#inputintervalend').val();

                        // 2018-04
                        var startyear = intervalstart.substring(0,4);
                        var startmonth = intervalstart.substring(5,7);
                        var endyear = intervalend.substring(0,4);
                        var endmonth = intervalend.substring(5,7);

                        if(pivottableid == "" || pivottableid == undefined || pivottableid == null)
                        {
                            alert("未选择数据透视定义，请检查或者首先进行数据透视定义。");
                            return;
                        }

                        if(startyear != endyear)
                        {
                            alert("数据透视只能处理当前会计年度的数据，请检查");
                            return;
                        }

                        var pivottable = {};
                        for(var i=0;i < pivottables.length;i++)
                        {
                            if (pivottables[i].id == pivottableid)
                            {
                                pivottable["id"] = pivottableid;
                                pivottable["report_code"] = pivottables[i].report_code;
                                pivottable["code"] = pivottables[i].code;
                                pivottable["name"] = pivottables[i].name;
                                break;
                            }
                        }

                        //归集固定列，透视列
                        var fixedcolumns = [];
                        var pivotcolumns = [];
                        for(var i=0;i < pivotdetails.length;i++)
                        {
                            if (pivotdetails[i].pivot_id == pivottable["id"] )
                            {
                                if (pivotdetails[i].col_type == "0")
                                {
                                    var fixedcolumn = {};
                                    fixedcolumn["col_order"] = pivotdetails[i].col_order;
                                    fixedcolumn["col_name"] = pivotdetails[i].col_name;
                                    fixedcolumns.push(fixedcolumn);
                                }

                                if (pivotdetails[i].col_type == "1")
                                {
                                    var pivotcolumn = {};
                                    pivotcolumn["col_order"] = pivotdetails[i].col_order;
                                    pivotcolumn["col_name"] = pivotdetails[i].col_name;
                                    pivotcolumns.push(pivotcolumn);
                                }
                            }
                        }
                        //归集数据：固定列
                        var fixcellcontents = [];
                        for(var i = 0;i < fixedcolumns.length;i++)
                        {
                            var fixcol = fixedcolumns[i].col_order - 1;
                            for(var j = self.titlerows+self.headrows - 1; j < self.titlerows+self.headrows+self.bodyrows+self.tailrows;j++)
                            {
                                var cellcontent = {};
                                cellcontent["row"] = j;
                                cellcontent["col"] = fixcol;
                                cellcontent["value"] = "";
                                var row = "";
                                var col = "";
                                for (var k = 0; k < self.cellinfos.length; k++)
                                {
                                    row = self.cellinfos[k]["row"];
                                    col = self.cellinfos[k]["col"];

                                    if (parseInt(row) == j && parseInt(col) == fixcol)
                                    {
                                        cellcontent["value"] = self.cellinfos[k]["data"];
                                        fixcellcontents.push(cellcontent);
                                    }
                                }
                            }
                        }

                        //归集数据：透视区间
                        var months = [];
                        for(var month = parseInt(startmonth);month <= parseInt(endmonth);month++)
                        {
                            if (month != parseInt(currentdate.substring(4,6)))
                            {
                                months.push(month);
                            }
                        }
                        //归集数据：透视列
                        var pivotcellcontents = [];
                        var defmultimonth = self._rpc({model: 'ps.statement.statements',method: 'get_statement_multimonth',args: [self.code,currentdate,months]}).then(function (result)
                        {
                            if (result)
                            {
                                for(var month = parseInt(startmonth);month <= parseInt(endmonth);month++)
                                {
                                    for(var i = 0;i < pivotcolumns.length;i++)
                                    {
                                        var pivotcol = pivotcolumns[i].col_order - 1;
                                        if (month == parseInt(currentdate.substring(4,6)))
                                        {
                                            for(var j = self.titlerows+self.headrows; j < self.titlerows+self.headrows+self.bodyrows;j++)
                                            {
                                                var cellcontent = {};
                                                cellcontent["month"] = month;
                                                cellcontent["row"] = j;
                                                cellcontent["col"] = pivotcol;
                                                cellcontent["value"] = "";
                                                var row = "";
                                                var col = "";

                                                for (var k = 0; k < self.cellinfos.length; k++)
                                                {
                                                    row = self.cellinfos[k]["row"];
                                                    col = self.cellinfos[k]["col"];

                                                    if (parseInt(row) == j && parseInt(col) == pivotcol)
                                                    {
                                                        cellcontent["value"] = self.cellinfos[k]["data"];
                                                        pivotcellcontents.push(cellcontent);
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        else {
                                            for(var iindex = 0;iindex < result.length;iindex++)
                                            {
                                                var monthjson = result[iindex];
                                                var monthresult = monthjson["month"];
                                                var jsonresult = JSON.parse(monthjson["json"]);
                                                var datatable = jsonresult["sheets"][self.sheetname]["data"]["dataTable"];

                                                if (month == monthresult)
                                                {
                                                    for(var j = self.titlerows+self.headrows; j < self.titlerows+self.headrows+self.bodyrows+self.tailrows;j++)
                                                    {
                                                        var cellcontent = {};
                                                        cellcontent["month"] = month;
                                                        cellcontent["row"] = j;
                                                        cellcontent["col"] = pivotcol;
                                                        if (!datatable[String(j)])
                                                        {
                                                            continue;
                                                        }

                                                        if(!datatable[String(j)][String(pivotcol)])
                                                        {
                                                            continue;
                                                        }

                                                        if (!datatable[String(j)][String(pivotcol)].value)
                                                        {
                                                            cellcontent["value"] = 0;
                                                        }
                                                        else
                                                        {
                                                            cellcontent["value"] = datatable[String(j)][String(pivotcol)].value;
                                                        }
                                                        pivotcellcontents.push(cellcontent);
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        });

                        self.do_action
                        ({
                            type: 'ir.actions.client',
                            tag: 'statements_pivot',
                            target: 'new',
                            context : {
                                'report_code' : self.code + "_" + pivottable["code"],
                                'report_name' : pivottable["name"],
                                'report_date' : currentdate,
                                'category'  : self.category,
                                'titlerows' : self.titlerows,
                                'headrows' : self.headrows,
                                'bodyrows' : self.bodyrows,
                                'tailrows' : self.tailrows,
                                'bodycols' : self.bodycols,
                                'intervalstart' : startmonth,
                                'intervalend' : endmonth,
                                'startyear' : startyear,
                                'fixedcolumns' : fixedcolumns,
                                'pivotcolumns' : pivotcolumns,
                                'fixcellcontents' : fixcellcontents,
                                'pivotcellcontents' : pivotcellcontents,
                            },
                        });

                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                    取消: function() {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                }
            });
            $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});
        },
        //合并居中
        mergecell: function (){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedRanges = activeSheet.getSelections();//get selected ranges and store to a variable;
            var rows = selectedRanges[0].row;	//the start row of selected ranges;
            var rowCounts = selectedRanges[0].rowCount;	//the number of selected rows;
            var cols = selectedRanges[0].col;	//the start column of selected ranges;
            var colCounts = selectedRanges[0].colCount;	//the number of selected column;
            // Merge rowCounts rows x colCounts columns with origin at cell(rows, cols).
            activeSheet.addSpan(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            // Merge three columns with origin at cell(row,col).
            //activeSheet.addSpan(3, 3, 2, 2, GcSpread.Sheets.SheetArea.viewport);
            // Set on every anchor cell
            var cell = activeSheet.getCell(rows, cols, GcSpread.Sheets.SheetArea.viewport);
            cell.hAlign(GcSpread.Sheets.HorizontalAlign.center);
            cell.vAlign(GcSpread.Sheets.VerticalAlign.center);
        },
        //取消合并
        deletespan: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedSpan = activeSheet.getSelections();
            var rows = selectedSpan[0].row;
            var cols = selectedSpan[0].col;
            //Gets the spans in the specified range in the specified sheet area.
            activeSheet.removeSpan(rows, cols, GcSpread.Sheets.SheetArea.viewport);
        },
        //全边框
        borderline: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            var linetype1 = GcSpread.Sheets.LineStyle.thin;
            // var linetype2 = GcSpread.Sheets.LineStyle.thick;
            // var linetype3 = GcSpread.Sheets.LineStyle.none;
            // var linetype = [linetype1,linetype2,linetype3];
            // // alert(linetype);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",linetype1), { all:true }, 3);
        },
        //左边框
        borderleft: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { left:true }, 3);
        },
        //右边框
        borderright: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { right:true }, 3);
        },
        //上边框
        bordertop: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { top:true }, 3);
        },
        //下边框
        borderbottom: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { bottom:true }, 3);
        },
        //外边框
        borderoutline: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { outline:true }, 3);
        },
        //内边框
        borderinside: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
            activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.thin), { inside:true }, 3);
        },

        textdecorationunderline: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var row2 = rows + selectedcells[0].rowCount - 1;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var col2 = cols + selectedcells[0].colCount - 1;
            // var underline = GcSpread.Sheets.TextDecorationType.Underline; // cssStyle.textDecoration=1
            // var overline = GcSpread.Sheets.TextDecorationType.Overline;   // cssStyle.textDecoration=4
            // var linethrough = GcSpread.Sheets.TextDecorationType.LineThrough; // cssStyle.textDecoration=2
            // var nonedecoration = GcSpread.Sheets.TextDecorationType.None; // cssStyle.textDecoration=0
            // GcSpread.Sheets.TextDecorationType.Overline|GcSpread.Sheets.TextDecorationType.LineThrough : cssStyle.textDecoration=2+4=6
            // activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.None);
            var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
            var num = cssStyle.textDecoration;
            //use this variable to justify what the text decoration condition of the selected cell is
            if(!num || num == 0){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.Underline);
            }else if(num == 1){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.None);
            }else if(num == 2){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.Underline|GcSpread.Sheets.TextDecorationType.LineThrough);
            }else if(num ==3){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.LineThrough);
            }
        },

        textdecorationlinethrough: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var row2 = rows + selectedcells[0].rowCount - 1;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var col2 = cols + selectedcells[0].colCount - 1;
            // underline: cssStyle.textDecoration=1
            // linethrough(删除线): cssStyle.textDecoration=2
            // overline: cssStyle.textDecoration=4
            // none: cssStyle.textDecoration=0
            // Overline&LineThrough : cssStyle.textDecoration=2+4=6
            var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
            var num = cssStyle.textDecoration;
            //use this variable to justify what the text decoration condition of the selected cell is
            if(!num || num == 0){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.LineThrough);
            }else if(num == 1){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.Underline|GcSpread.Sheets.TextDecorationType.LineThrough);
            }else if(num == 2){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.None);
            }else if(num == 3){
                activeSheet.getCells(rows,cols,row2,col2).textDecoration(GcSpread.Sheets.TextDecorationType.Underline);
            }
        },
        //水平左对齐
        leftalign: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.left);
                }
            }
        },
        //水平居中对齐
        centeralign: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                }
            }
        },
        //水平右对齐
        rightalign: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.right);
                }
            }
        },
        //垂直左对齐
        vleft: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.top);
                }
            }
        },
        //垂直居中对齐
        vcenter: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.center);
                }
            }
        },
        //垂直右对齐
        vright: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            for (var k = cols; k < cols + colCounts; k++) {
                for (var i = rows, j = k; i < rows + rowCounts; i++) {
                    activeSheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.bottom);
                }
            }
        },
        //粗体
        fontbold: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var rows2 = rows + rowCounts - 1;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var cols2 = cols + colCounts - 1;
            var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
            var fontElement = $("<span></span>");
            var fontweight = 'bold';
            var fontactualstyle = cssStyle.font;
            // var fontstyle = 'italic';
            fontElement.css("font", cssStyle.font); // 字体概括
            // fontElement.css("font-size", "36px"); // 字体大小
            // fontElement.css("font-weight", fontweight); // 字体粗细
            // fontElement.css("font-style", fontstyle); // 字体倾斜
            // fontElement.css("font-family",'Arial'); // 字体类型
            cssStyle.font = fontElement.css("font");
            // activeSheet.getCell(rows,cols).font(cssStyle.font);
            if(fontactualstyle.match(fontweight)){
                fontElement.css("font-weight", "normal");
                cssStyle.font = fontElement.css("font");
                activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
            }else{
                fontElement.css("font-weight", "bold"); // 字体粗细
                cssStyle.font = fontElement.css("font");
                activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
            }
        },
        //斜体
        fontitalic: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            var rows2 = rows + rowCounts - 1;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            var cols2 = cols + colCounts - 1;
            var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
            var fontElement = $("<span></span>");
            // var fontweight = 'bold';
            var fontstyle = 'italic';
            var fontactualstyle = cssStyle.font;
            fontElement.css("font", cssStyle.font); // 字体概括
            if(fontactualstyle.match(fontstyle)){//判断字体内是否包含字符串"italic"
                fontElement.css("font-style", "normal");
                cssStyle.font = fontElement.css("font");
                activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
            }else{
                fontElement.css("font-style", "italic"); // 字体倾斜
                cssStyle.font = fontElement.css("font");
                activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
            }
        },

        // bolditalic: function() {
        //     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
        //     var activeSheet = spreadtemp.getActiveSheet();
        //     var selectedcells = activeSheet.getSelections();
        //     var rows = selectedcells[0].row;	//the start row of selected ranges;
        //     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
        //     var cols = selectedcells[0].col;	//the start column of selected ranges;
        //     var colCounts = selectedcells[0].colCount;	//the number of selected column;
        //     var cstyle = activeSheet.getActualStyle(rows,cols,GcSpread.Sheets.SheetArea.viewport, false);
        //     var fontsize0 = new Array();
        //     fontsize0[0]="bold italic";
        //     var fontsize1 = fontsize0[0] + " " + cstyle.font;//Set the argument for font method
        //     var fontsize2 = "normal normal " + cstyle.font;
        //     if(numita_bold){
        //         for (var k = cols; k < cols + colCounts; k++) {
        //             for (var i = rows, j = k; i < rows + rowCounts; i++) {
        //                 activeSheet.getCell(i, j).font(fontsize1);
        //                 //activeSheet.getCell(i, j).font("bold italic 14.6667px Calibri");
        //             }
        //         }
        //     }else{
        //         for (var k = cols; k < cols + colCounts; k++) {
        //             for (var i = rows, j = k; i < rows + rowCounts; i++) {
        //                 activeSheet.getCell(i, j).font(fontsize2);
        //             }
        //         }
        //     }
        //     numita_bold = !numita_bold;
        // },
        //撤销
        undo: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            GcSpread.Sheets.SpreadActions.undo.apply(activeSheet);

        },
        //恢复
        redo: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            GcSpread.Sheets.SpreadActions.redo.apply(activeSheet);
        },
        //复制
        copyt: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            spreadtemp.cutCopyIndicatorVisible(true);
            spreadtemp.cutCopyIndicatorBorderColor("green");//设置复制标识颜色
            activeSheet.clipBoardOptions(GcSpread.Sheets.ClipboardPasteOptions.All);
            GcSpread.Sheets.SpreadActions.copy.call(activeSheet);
        },
        //剪切
        cutt: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            spreadtemp.cutCopyIndicatorVisible(true);
            spreadtemp.cutCopyIndicatorBorderColor("red");//设置复制标识颜色
            activeSheet.clipBoardOptions(GcSpread.Sheets.ClipboardPasteOptions.All);
            GcSpread.Sheets.SpreadActions.cut.call(activeSheet);
        },
        //粘贴
        pastet: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            activeSheet.clipBoardOptions(GcSpread.Sheets.ClipboardPasteOptions.All);
            GcSpread.Sheets.SpreadActions.paste.call(activeSheet);
        },

        // addrow: function() {
        //     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
        //     var activeSheet = spreadtemp.getActiveSheet();
        //     var selectedcells = activeSheet.getSelections();
        //     var rows = selectedcells[0].row;	//the start row of selected ranges;
        //     activeSheet.addRows(rows, 1);
        // },
        //
        // delrow: function() {
        //     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
        //     var activeSheet = spreadtemp.getActiveSheet();
        //     var selectedcells = activeSheet.getSelections();
        //     var rows = selectedcells[0].row;	//the start row of selected ranges;
        //     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
        //     activeSheet.deleteRows(rows, rowCounts);
        // },
        //显示行
        showrow: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            for (var i = rows-1 ; i < rows + rowCounts; i++) {
                activeSheet.setRowVisible(i,true,GcSpread.Sheets.SheetArea.viewport);
            }
        },
        //隐藏行
        hiderow: function() {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            for (var i = rows; i < rows + rowCounts; i++) {
                activeSheet.setRowVisible(i,false,GcSpread.Sheets.SheetArea.viewport);
            }
        },
        //字体
        fontset: function (){
            var $div=$("<div>",{id:"dialog-message",title:"字体设置"});
            var $sectop = $("<section class=\"fontguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"fontguidetop\">");
            var $secleft = $("<section class=\"fontlist\" style=\"float:left;height: 100%;width: 50%;\" id=\"fontlist\">");
            var $secleftleft = $("<section class=\"fontoperateselect\" id=\"fontoperateselect\" style=\"height: 100%;width: 50%;margin: 0 auto;\" >");
            var $secleftleftleft = $("<section class=\"fontoperateselectlabel0\" id=\"fontoperateselectlabel0\" style=\"display: inline-block;height: 100%;width: 30%;margin: 0 auto;\" >");
            var $secleftleftright = $("<section class=\"fontoperateselectselect0\" id=\"fontoperateselectselect0\" style=\"height: 100%;width: 70%;display: inline-block;\" >");
            var $p0=$("<p style='height:21px;'>").html("字体：");
            $secleftleftleft.append($p0);
            var $selectfont=$("<select>",{id:"setfont"});
            $selectfont.css("height","21px");
            $secleftleftright.append($selectfont);
            var fontselectlist = ["Arial","Arial Black","Calibri","Cambria","Candara","Century","Courier New","Comic Sans MS",
            "Garamond","Georgia","Malgun Gothic","Mangal","Meiryo","MS Gothic","MS Mincho","MS PGothic","MS PMincho","Tahoma",
            "Times","Times New Roman","Trebuchet MS","SimSun","NSimSun","SimHei","Microsoft YaHei","LiSu","YouYuan","KaiTi",
            "STXihei","MingLiU","PMingLiU","STCAIYUN"];
            for(var i=0;i < fontselectlist.length;i++)
            {
                $selectfont.append("<option value='"+fontselectlist[i]+"'>"+fontselectlist[i]+"</option>");
            }
            // $secleftleft.append('<select style= "width:70%;height:21px;display: inline-block;" name="font" id="font" ></select>');
            $secleftleft.append($secleftleftleft);
            $secleftleft.append($secleftleftright);
            $secleft.append($secleftleft);

            var $secright = $("<section class=\"fontoperate\" id=\"fontoperate\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $secrightleft = $("<section class=\"fontoperateselect\" id=\"fontoperateselect\" style=\"height: 100%;width: 50%;margin: 0 auto;\" >");
            var $secrightleftleft = $("<section class=\"fontoperateselectlabel\" id=\"fontoperateselectlabel\" style=\"display: inline-block;height: 100%;width: 30%;\" >");
            var $secrightleftright = $("<section class=\"fontoperateselectselect\" id=\"fontoperateselectselect\" style=\"height: 100%;width: 70%;display: inline-block;\" >");
            // var $secrightright = $("<section class=\"fontoperateaddbutton\" id=\"fontoperateaddbutton\" style=\"float:right;height: 100%;width: 50%;\" >");

            //弹出框“运算符号”（下拉菜单），“添加公式”（按钮）的设置
            var $p1=$("<p style='height:21px;'>").html("字号：");
            $secrightleftleft.append($p1);
            //设置下拉菜单以及菜单内的选项，默认选项为当前字体的大小
            var $selectsize=$("<select>",{id:"setsize"});
            $selectsize.css("height","21px");
            $secrightleftright.append($selectsize);
            //定义字体字号的数组
            var fontsizelist = [8,9,10,11,12,14,16,18,20,24,26,28,36,48,72];
            // alert(fontsizelist); //显示包含字号的数组
            for(var i=0;i < fontsizelist.length;i++)
            {
                $selectsize.append("<option value='"+fontsizelist[i]+"'>"+fontsizelist[i]+"</option>");
            }

            $secrightleft.append($secrightleftleft);
            $secrightleft.append($secrightleftright);

            $secright.append($secrightleft);

            $sectop.append($secleft);
            $sectop.append($secright);

            $div.append($sectop);

            $div.dialog({
                modal: true,
                width:600,
                buttons: {
                    确定: function()
                    {
                        var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                        var activeSheet = spreadtemp.getActiveSheet();
                        var selectedcells = activeSheet.getSelections();
                        var rows = selectedcells[0].row;	//the start row of selected ranges;
                        var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
                        var rows2 = rows + rowCounts - 1;
                        var cols = selectedcells[0].col;	//the start column of selected ranges;
                        var colCounts = selectedcells[0].colCount;	//the number of selected column;
                        var cols2 = cols + colCounts - 1;
                        var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
                        var fontElement = $("<span></span>");
                        var optionfont = $('#setfont').find('option:selected').text();
                        // alert(optionfont);//显示字体
                        var optionfontsize = $('#setsize').find('option:selected').text()+"px";
                        // alert(optionfontsize);//显示字号
                        fontElement.css("font", cssStyle.font);
                        fontElement.css("font-family",optionfont);
                        fontElement.css("font-size", optionfontsize);
                        cssStyle.font = fontElement.css("font");
                        // alert(cssStyle.font);//显示字体概括信息
                        activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
                        for (var i = rows; i < rows2+1; i++) {
                            activeSheet.autoFitRow(i);
                        }
                        for (var j = cols; j < cols2+1; j++) {
                            activeSheet.autoFitColumn(j);
                        }

                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                    取消: function()
                    {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                },
                close: function(event, ui)
                {
                    $div.empty();
                }
            });
        },
        //报表属性
        reportproperties: function(){
            var properties = [];
            var self = this;

            //设置报表属性对话框
            var $div=$("<div>",{id:"dialog-message",title:"报表属性"});
            //设置对话框第一层
            //对话框第一层左半部分
            var $sectop = $("<section class=\"reportpropertyguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"reportpropertyguidetop\">");//对话框第一行sectop
            var $secleft = $("<section class=\"reportproperty\" style=\"float:left;height: 100%;width: 50%;\" id=\"reporcodeproperty\">");//对话框第一行左半部分，占sectop的50%
            var $secleftleft = $("<section class=\"reportinput\" id=\"reporcodeinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");//对话框第一行左半部分详细设置，占secleft的80%
            var $secleftleftleft = $("<section class=\"reportinputlabel\" id=\"reportcodelabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");//对话框第一行左半部分的左半部分，占secleftleft的36%
            var $secleftleftright = $("<section class=\"reportinputinput\" id=\"reportcodeinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");//对话框第一行左半部分的右半部分，占secleftleft的60%
            var $p0=$("<p style='height:21px;'>").html("报表编号：");
            $secleftleftleft.append($p0);
            var $inputreportcode=$("<input id=\'reportcode\' type='text' readonly='readonly' >");
            $inputreportcode.css("height","21px");
            $inputreportcode.css("background-color","#D9D9D9");//为readonly的input框设置灰色背景色
            $secleftleftright.append($inputreportcode);
            $secleftleft.append($secleftleftleft);
            $secleftleft.append($secleftleftright);
            $secleft.append($secleftleft);
            //对话框第一层右半部分
            var $secright = $("<section class=\"reportproperty\" id=\"reporttimeproperty\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $secrightleft = $("<section class=\"reporttimeselect\" id=\"reporttimeselect\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $secrightleftleft = $("<section class=\"reportpropertyselectlabel\" id=\"reporttimeselectlabel\" style=\"display: inline-block;height: 100%;width: 36%;\" >");
            var $secrightleftright = $("<section class=\"reportpropertyselectselect\" id=\"reportpropertytimeselectselect\" style=\"height: 100%;width: 60%;display: inline-block;\" >");

            var $p1=$("<p style='height:21px;'>").html("编报时间：");
            $secrightleftleft.append($p1);
            //设置下拉菜单以及菜单内的选项
            var $selectreporttime=$("<select>",{id:"setreporttime"});
            $selectreporttime.css("height","21px");
            $secrightleftright.append($selectreporttime);
            var reporttimelist = ["月报表", "全部"];
            for(var i=0;i < reporttimelist.length;i++)
            {
                $selectreporttime.append("<option value='"+reporttimelist[i]+"'>"+reporttimelist[i]+"</option>");
            }
            $secrightleft.append($secrightleftleft);
            $secrightleft.append($secrightleftright);
            $secright.append($secrightleft);
            $sectop.append($secleft);
            $sectop.append($secright);
            $div.append($sectop);
            //对话框第二层 & 2nd left part
            var $sec2nd = $("<section class=\"reportpropertyguide2nd\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"reportpropertyguide2nd\">");
            var $sec2ndleft = $("<section class=\"reportproperty\" style=\"float:left;height: 100%;width: 50%;\" id=\"repornameproperty\">");
            var $sec2ndleftleft = $("<section class=\"reportinput\" id=\"repornameinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec2ndleftleftleft = $("<section class=\"reportinputlabel\" id=\"reportnamelabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
            var $sec2ndleftleftright = $("<section class=\"reportinputinput\" id=\"reportnameinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p3=$("<p style='height:21px;'>").html("报表名称：");
            $sec2ndleftleftleft.append($p3);
            var $inputreportname=$("<input id=\'reportname\' type='text' >");
            $inputreportname.css("height","21px");
            $sec2ndleftleftright.append($inputreportname);
            $sec2ndleftleft.append($sec2ndleftleftleft);
            $sec2ndleftleft.append($sec2ndleftleftright);
            $sec2ndleft.append($sec2ndleftleft);
            //2nd right part
            var $sec2ndright = $("<section class=\"reportproperty\" id=\"reportingcodeproperty\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $sec2ndrightleft = $("<section class=\"reportingcodeinput\" id=\"reportingcodeinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec2ndrightleftleft = $("<section class=\"reportpropertyinputlabel\" id=\"reportingcodeinputlabel\" style=\"display: inline-block;height: 100%;width: 36%;\" >");
            var $sec2ndrightleftright = $("<section class=\"reportpropertyinputinput\" id=\"reportingcodeinputinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            //设置输入框标签
            var $p4=$("<p style='height:21px;'>").html("上报编号：");
            $sec2ndrightleftleft.append($p4);
            var $inputreportingcode=$("<input id=\'reportingcode\' type='text'>");
            $inputreportingcode.css("height","21px");
            //将各个部分进行拼接，构成对话框第二层
            $sec2ndrightleftright.append($inputreportingcode);
            $sec2ndrightleft.append($sec2ndrightleftleft);
            $sec2ndrightleft.append($sec2ndrightleftright);
            $sec2ndright.append($sec2ndrightleft);
            $sec2nd.append($sec2ndleft);
            $sec2nd.append($sec2ndright);
            $div.append($sec2nd);
            //dialog 3rd $ 3rd left part
            var $sec3rd = $("<section class=\"reportpropertyguide3rd\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"reportpropertyguide3rd\">");
            var $sec3rdleft = $("<section class=\"reportproperty\" style=\"float:left;height: 100%;width: 50%;\" id=\"titlerowsproperty\">");
            var $sec3rdleftleft = $("<section class=\"reportinput\" id=\"titlerowsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec3rdleftleftleft = $("<section class=\"reportinputlabel\" id=\"titlerowslabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
            var $sec3rdleftleftright = $("<section class=\"reportinputinput\" id=\"titlerowsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p5=$("<p style='height:21px;'>").html("标题行数：");
            $sec3rdleftleftleft.append($p5);
            var $inputtitlerows=$("<input id=\'titlerows\' type='number'>");
            $inputtitlerows.css("height","21px");
            $sec3rdleftleftright.append($inputtitlerows);
            $sec3rdleftleft.append($sec3rdleftleftleft);
            $sec3rdleftleft.append($sec3rdleftleftright);
            $sec3rdleft.append($sec3rdleftleft);
            // 3rd right part
            var $sec3rdright = $("<section class=\"reportproperty\" id=\"headrowsproperty\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $sec3rdrightleft = $("<section class=\"reportinput\" id=\"headrowsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec3rdrightleftleft = $("<section class=\"reportinputlabel\" id=\"headrowslabel\" style=\"display: inline-block;height: 100%;width: 36%;\" >");
            var $sec3rdrightleftright = $("<section class=\"reportinputinput\" id=\"headrowsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p6=$("<p style='height:21px;'>").html("表头行数：");
            $sec3rdrightleftleft.append($p6);
            var $inputheadrows=$("<input id=\'headrows\' type='number'>");
            $inputheadrows.css("height","21px");
            $sec3rdrightleftright.append($inputheadrows);
            $sec3rdrightleft.append($sec3rdrightleftleft);
            $sec3rdrightleft.append($sec3rdrightleftright);
            $sec3rdright.append($sec3rdrightleft);
            $sec3rd.append($sec3rdleft);
            $sec3rd.append($sec3rdright);
            $div.append($sec3rd);
            //dialog 4th & 4th left part
            var $sec4th = $("<section class=\"reportpropertyguide4th\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"reportpropertyguide4th\">");
            var $sec4thleft = $("<section class=\"reportproperty\" style=\"float:left;height: 100%;width: 50%;\" id=\"bodyrowsproperty\">");
            var $sec4thleftleft = $("<section class=\"reportinput\" id=\"bodyrowsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec4thleftleftleft = $("<section class=\"reportinputlabel\" id=\"bodyrowslabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
            var $sec4thleftleftright = $("<section class=\"reportinputinput\" id=\"bodyrowsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p7=$("<p style='height:21px;'>").html("表体行数：");
            $sec4thleftleftleft.append($p7);
            var $inputbodyrows=$("<input id=\'bodyrows\' type='number'>");
            $inputbodyrows.css("height","21px");
            $sec4thleftleftright.append($inputbodyrows);
            $sec4thleftleft.append($sec4thleftleftleft);
            $sec4thleftleft.append($sec4thleftleftright);
            $sec4thleft.append($sec4thleftleft);
            //4th left part
            var $sec4thright = $("<section class=\"reportproperty\" id=\"tailrowsproperty\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $sec4thrightleft = $("<section class=\"reportinput\" id=\"tailrowsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec4thrightleftleft = $("<section class=\"reportinputlabel\" id=\"tailrowslabel\" style=\"display: inline-block;height: 100%;width: 36%;\" >");
            var $sec4thrightleftright = $("<section class=\"reportinputinput\" id=\"tailrowsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p8=$("<p style='height:21px;'>").html("表尾行数：");
            $sec4thrightleftleft.append($p8);
            var $inputtailrows=$("<input id=\'headrows\' type='number'>");
            $inputtailrows.css("height","21px");
            $sec4thrightleftright.append($inputtailrows);
            $sec4thrightleft.append($sec4thrightleftleft);
            $sec4thrightleft.append($sec4thrightleftright);
            $sec4thright.append($sec4thrightleft);
            $sec4th.append($sec4thleft);
            $sec4th.append($sec4thright);
            $div.append($sec4th);
            //dialog 5th & 5th left part
            var $sec5th = $("<section class=\"reportpropertyguide5th\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"reportpropertyguide5th\">");
            var $sec5thleft = $("<section class=\"reportproperty\" style=\"float:left;height: 100%;width: 50%;\" id=\"totalrowsproperty\">");
            var $sec5thleftleft = $("<section class=\"reportinput\" id=\"totalrowsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec5thleftleftleft = $("<section class=\"reportinputlabel\" id=\"totalrowslabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
            var $sec5thleftleftright = $("<section class=\"reportinputinput\" id=\"totalrowsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p9=$("<p style='height:21px;'>").html("总行数：");
            $sec5thleftleftleft.append($p9);
            var $inputtotalrows=$("<input id=\'totalrows\' type='number' readonly='readonly'>");
            $inputtotalrows.css("height","21px");
            $inputtotalrows.css("background-color","#D9D9D9");
            $sec5thleftleftright.append($inputtotalrows);
            $sec5thleftleft.append($sec5thleftleftleft);
            $sec5thleftleft.append($sec5thleftleftright);
            $sec5thleft.append($sec5thleftleft);
            //5th right part
            var $sec5thright = $("<section class=\"reportproperty\" id=\"totalcolsproperty\" style=\"float:right;height: 100%;width: 50%;\" >");
            var $sec5thrightleft = $("<section class=\"reportinput\" id=\"totalcolsinput\" style=\"height: 100%;width: 80%;margin: 0 auto;\" >");
            var $sec5thrightleftleft = $("<section class=\"reportinputlabel\" id=\"totalcolslabel\" style=\"display: inline-block;height: 100%;width: 36%;\" >");
            var $sec5thrightleftright = $("<section class=\"reportinputinput\" id=\"totalcolsinput\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
            var $p10=$("<p style='height:21px;'>").html("总列数：");
            $sec5thrightleftleft.append($p10);
            var $inputtotalcols=$("<input id=\'totalcols\' type='number'>");
            $inputtotalcols.css("height","21px");
            $sec5thrightleftright.append($inputtotalcols);
            $sec5thrightleft.append($sec5thrightleftleft);
            $sec5thrightleft.append($sec5thrightleftright);
            $sec5thright.append($sec5thrightleft);
            $sec5th.append($sec5thleft);
            $sec5th.append($sec5thright);
            $div.append($sec5th);
            //dialog 6th for table
            var $sec6thtable = $("<section class=\"sectioncolumnstable\" id=\"columnspropertiestable\" style=\"height: 100%;width: 100%;margin-top: 20px;overflow: hidden;\" >");
            var $columnstable = $("<table class=\"columnstable\" id=\"columnstable\" style=\"height: 100%;width: 90%;margin-left: auto;margin-right: auto\" border=\"1\">");
            var $columnstablehead = $('<thead class="colstablehead" id="colstablehead"><tr>' +
                '<th style="text-align:center;">列名称</th>' +
                '<th style="text-align:center;">列坐标</th>' +
                '<th style="text-align:center;">数值列</th>' +
                '<th style="text-align:center;">汇总列</th>' +
                '<th style="text-align:center;">调整列</th>' +
                '<th style="text-align:center;">项目列</th></tr></thead>');
            // $("th").css("text-align","center");
            //这种方法之所以不能修改th标签的属性，是因为获取不到th 这些th是通过js dom进去的 页面没渲染出来 所以抓取不到
            //用这种方法dom,只能是在上面的th里面一个个的加style,或者通过css给它设样式,不要在js里写（by福元）
            var $columnstablebody = $('<tbody class="colstablebody" id="colstablebody"></tbody>');

            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
            var activeSheet = spreadtemp.getActiveSheet();
            var selectedcells = activeSheet.getSelections();
            var rows = selectedcells[0].row;	//the start row of selected ranges;
            var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
            // var rows2 = rows + rowCounts - 1;
            var cols = selectedcells[0].col;	//the start column of selected ranges;
            var colCounts = selectedcells[0].colCount;	//the number of selected column;
            // var cols2 = cols + colCounts - 1;
            var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);

            //获取所有列坐标，并将列坐标(字母)存到列表(colcoordinates)中
            var colcoordinates = []; //列坐标字母
            var colorders = []; //列坐标数字
            var colnames = [];  //列名称
            var sheetcolscounts = activeSheet.getColumnCount(GcSpread.Sheets.SheetArea.viewport);
            for(var k=0;k<sheetcolscounts;k++)
            {
                //从前台获取所有字母型的列坐标，A,B,C等
                var colcoordinate = activeSheet.getText(0, k,GcSpread.Sheets.SheetArea.colHeader);
                colcoordinates.push(colcoordinate);
                colorders.push(String(k+1));
                //不支持多行表头，没有意义
                var colname = activeSheet.getValue(self.titlerows + self.headrows - 1,k);
                if (colname == null || colname == undefined)
                {
                    colname = "";
                }
                colnames.push(colname);
            }

            var reportcode = "";
            var reportname = "";
            var titlerows = "";
            var headrows = "";
            var bodyrows = "";
            var tailrows = "";
            var totalrows = "";
            var totalcols = "";

            if (self.isnew == "1")
            {
                alert("新建报表需要先保存后设置报表属性。");
                return;
            }
            else {
                //报表属性获取并显示
                var args = [self.code,self.date];
                var defgetpropertiesparams = this._rpc({
                    model: 'ps.statement.statements',
                    method: 'get_reportproperties_params',
                    args:args,
                }).then(function (result) {
                    properties = result;
                    reportcode = properties[0]['report_code'];
                    reportname = properties[0]['report_name'];
                    titlerows = properties[0]['title_rows'];
                    headrows = properties[0]['head_rows'];
                    bodyrows = properties[0]['body_rows'];
                    tailrows = properties[0]['tail_rows'];
                    totalrows = properties[0]['total_rows'];
                    totalcols = properties[0]['total_cols'];

                    //多次定义报表属性情况处理
                    var h2s = document.querySelectorAll("h2");
                    var reportnamebak = h2s[0].innerText;
                    var titlerowsbak = self.titlerows;
                    var headrowsbak = self.headrows;
                    var bodyrowsbak = self.bodyrows;
                    var tailrowsbak = self.tailrows;
                    var totalrowsbak = self.titlerows+self.headrows+self.bodyrows+self.tailrows;
                    var totalcolsbak = self.bodycols;

                    if(reportname != reportnamebak)
                    {
                        reportname = reportnamebak;
                    }

                    if(titlerows != titlerowsbak)
                    {
                        titlerows = titlerowsbak;
                    }
                    if(headrows != headrowsbak)
                    {
                        headrows = headrowsbak;
                    }
                    if(bodyrows != bodyrowsbak)
                    {
                        bodyrows = bodyrowsbak;
                    }
                    if(tailrows != tailrowsbak)
                    {
                        tailrows = tailrowsbak;
                    }
                    if(totalrows != totalrowsbak)
                    {
                        totalrows = totalrowsbak;
                    }
                    if(totalcols != totalcolsbak)
                    {
                        totalcols = totalcolsbak;
                    }

                    $inputreportcode.val(reportcode);
                    $inputreportname.val(reportname);
                    $inputreportingcode.val(reportcode);
                    $inputtitlerows.val(titlerows);
                    $inputtitlerows.attr("min", titlerows);//set the attribute "min" for this input tag
                    $inputheadrows.val(headrows);
                    $inputheadrows.attr("min", headrows);
                    $inputbodyrows.val(bodyrows);
                    $inputbodyrows.attr("min", bodyrows);
                    $inputtailrows.val(tailrows);
                    $inputtailrows.attr("min", tailrows);
                    $inputtotalrows.val(totalrows);
                    $inputtotalcols.val(totalcols);
                    $inputtotalcols.attr("min", totalcols);

                    $inputtitlerows.change(function ()
                    {
                        if ($inputtitlerows.val() < titlerows)
                        {
                            alert("新的表头行数不能低于原始的表头行数");
                            $inputtitlerows.val(titlerows);
                        }
                        var instotalrows = Number($inputtitlerows.val()) + Number($inputheadrows.val())
                            + Number($inputbodyrows.val()) + Number($inputtailrows.val());
                        $inputtotalrows.val(instotalrows);
                    });
                    $inputheadrows.change(function ()
                    {
                        if ($inputheadrows.val() < headrows)
                        {
                            alert("新的表头行数不能低于原始的表头行数");
                            $inputheadrows.val(headrows);
                        }
                        var instotalrows = Number($inputtitlerows.val()) + Number($inputheadrows.val())
                            + Number($inputbodyrows.val()) + Number($inputtailrows.val());
                        $inputtotalrows.val(instotalrows);
                    });
                    $inputbodyrows.change(function ()
                    {
                        if ($inputbodyrows.val() < bodyrows)
                        {
                            alert("新的表体行数不能低于原始的表体行数");
                            $inputbodyrows.val(bodyrows);
                        }
                        var instotalrows = Number($inputtitlerows.val()) + Number($inputheadrows.val())
                            + Number($inputbodyrows.val()) + Number($inputtailrows.val());
                        $inputtotalrows.val(instotalrows);
                    });
                    $inputtailrows.change(function ()
                    {
                        if ($inputtailrows.val() < tailrows)
                        {
                            alert("新的表尾行数不能低于原始的表尾行数");
                            $inputtailrows.val(tailrows);
                        }
                        var instotalrows = Number($inputtitlerows.val()) + Number($inputheadrows.val())
                            + Number($inputbodyrows.val()) + Number($inputtailrows.val());
                        $inputtotalrows.val(instotalrows);
                    });

                    $inputtotalcols.change(function ()
                    {
                        if ($inputtotalcols.val() < totalcols)
                        {
                            alert("新的表列数不能低于原始的表列数");
                            $inputtotalcols.val(totalcols);
                        }
                    });
                });

                //列属性获取并显示
                var args = [self.code,self.date];
                var defgetcolsproperties = self._rpc({
                    model: 'ps.statement.sheet.columns',
                    method: 'get_columns_info',
                    args:args,
                }).then(function (result)
                {
                    var colsproperties = result;
                    var colname = "";
                    var colnamesdb = [];
                    var colorder = "";
                    var colordersdb = [];//局部变量，仅能在此function内使用

                    for (var i = 0; i < colsproperties.length; i++)
                    {
                        colname = colsproperties[i]['col_name'];
                        colorder = colsproperties[i]['col_order'];
                        colnamesdb.push(colname);
                        colordersdb.push(colorder);
                    }

                    //多次定义报表属性情况处理：以当前报表上显示的为准
                    //行列增加或行列删除:插入/删除行列或者通过报表属性增加行数或者列数
                    if(colorders.length != colordersdb.length)
                    {

                    }

                    //插入列无法识别是插入到哪里了，跟列属性无法对应呢
                    //插入列有self.colsproperties记录里

                    for (var l = 0; l < colorders.length; l++)
                    {
                        var $tr = $("<tr id='row_" + colorders[l] + "' align=\"center\">");//set the row(lth)
                        var $td1 = $("<td  class='colname' id='colid_" + colorders[l] + "'>");//set the 1st cell in the row
                        $td1.append("<input id='colname_" + colorders[l] + "' style=\"border: 0px;text-align: center;width:100%;\" value=" + colnames[l] + ">");//set the context for this cell
                        var $td2 = $("<td class='colcoordinate' id='colcoordinate_" + colcoordinates[l] + "'>");
                        $td2.html(colcoordinates[l]);
                        var $td3 = $("<td class='colproperties' id='isnumber_" + colcoordinates[l] + "'>");
                        if (self.colsproperties[l]["col_isnumber"] == "1")
                        {
                            $td3.append($("<input type='checkbox' checked='checked' value='1' id='inputisnumber_" + colcoordinates[l] + "'>"));
                        }
                        else {
                            $td3.append($("<input type='checkbox' value='1' id='inputisnumber_" + colcoordinates[l] + "'>"));
                        }

                        var $td4 = $("<td class='colproperties' id='isamount_" + colcoordinates[l] + "'>");
                        if (self.colsproperties[l]["col_isamount"] == "1") {
                            $td4.append($("<input type='checkbox' checked='checked' value='1' id='inputisamount_" + colcoordinates[l] + "'>"));
                        }
                        else {
                            $td4.append($("<input type='checkbox' value='1' id='inputisamount_" + colcoordinates[l] + "'>"));
                        }
                        var $td5 = $("<td class='colproperties' id='isadjust_" + colcoordinates[l] + "'>");
                        if (self.colsproperties[l]["col_isadjust"] == "1") {
                            $td5.append($("<input type='checkbox' checked='checked' value='1' id='inputisadjust_" + colcoordinates[l] + "'>"));
                        }
                        else {
                            $td5.append($("<input type='checkbox' value='1' id='inputisadjust_" + colcoordinates[l] + "'>"));
                        }
                        var $td6 = $("<td class='colproperties' id='isitem_" + colcoordinates[l] + "'>");
                        if (self.colsproperties[l]["col_isitem"] == "1") {
                            $td6.append($("<input type='checkbox' checked='checked' value='1' id='inputisitem_" + colcoordinates[l] + "'>"));
                        }
                        else {
                            $td6.append($("<input type='checkbox' value='1' id='inputisitem_" + colcoordinates[l] + "'>"));
                        }
                        $tr.append($td1);
                        $tr.append($td2);
                        $tr.append($td3);
                        $tr.append($td4);
                        $tr.append($td5);
                        $tr.append($td6);

                        $columnstablebody.append($tr);
                        $columnstable.append($columnstablehead);
                        $columnstable.append($columnstablebody);
                        $sec6thtable.append($columnstable);
                        $div.append($sec6thtable);
                    }
                });
            }

            $div.dialog({
                modal: true,
                width: 630,
                buttons: {
                    确定: function()
                    {
                        //设置变量获取新的报表属性
                        var bereportcode = localStorage.getItem('code');
                        var bereportdate = localStorage.getItem('date');
                        var bereportname = $inputreportname.val();
                        var betitlerows = $inputtitlerows.val();
                        var beheadrows = $inputheadrows.val();
                        var bebobyrows = $inputbodyrows.val();
                        var betailrows = $inputtailrows.val();
                        var betotalrows = $inputtotalrows.val();
                        var betotalcols = $inputtotalcols.val();

                        if(bereportname != reportname)
                        {
                            var h2s = document.querySelectorAll("h2");
                            h2s[0].innerText = bereportname;
                        }

                        if(betitlerows > titlerows)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            var sheet = spreadtemp.getSheet(0);
                            for(var i = 0;i < betitlerows - titlerows;i++)
                            {
                                sheet.addRows(titlerows - 1, 1);
                                var insertrow = {};
                                insertrow["row"] = titlerows - 1;
                                insertrow["count"] = 1;
                                self.insertrows.push(insertrow);
                                self.cellinfos = self.formulabyrowcolchange(); //处理公式坐标
                                sheet.copyTo(titlerows,0,titlerows - 1,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
                            }
                        }
                        if(beheadrows > headrows)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            var sheet = spreadtemp.getSheet(0);
                            for(var i = 0;i < beheadrows - headrows;i++)
                            {
                                sheet.addRows(headrows - 1, 1);
                                var insertrow = {};
                                insertrow["row"] = headrows - 1;
                                insertrow["count"] = 1;
                                self.insertrows.push(insertrow);
                                self.cellinfos = self.formulabyrowcolchange(); //处理公式坐标
                                sheet.copyTo(headrows,0,headrows - 1,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
                            }
                        }

                        if(bebobyrows > bodyrows)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            var sheet = spreadtemp.getSheet(0);
                            for(var i = 0;i < bebobyrows - bodyrows;i++)
                            {
                                sheet.addRows(bodyrows - 1, 1);
                                var insertrow = {};
                                insertrow["row"] = bodyrows - 1;
                                insertrow["count"] = 1;
                                self.insertrows.push(insertrow);
                                self.cellinfos = self.formulabyrowcolchange(); //处理公式坐标
                                sheet.copyTo(bodyrows,0,bodyrows - 1,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
                            }
                        }

                        if(betailrows > tailrows)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            var sheet = spreadtemp.getSheet(0);
                            for(var i = 0;i < betailrows - tailrows;i++)
                            {
                                sheet.addRows(tailrows - 1, 1);
                                var insertrow = {};
                                insertrow["row"] = tailrows - 1;
                                insertrow["count"] = 1;
                                self.insertrows.push(insertrow);
                                self.cellinfos = self.formulabyrowcolchange(); //处理公式坐标
                                sheet.copyTo(tailrows,0,tailrows - 1,0,1,sheet.getColumnCount(),GcSpread.Sheets.CopyToOption.Style);
                            }
                        }

                        if(betotalcols > totalcols)
                        {
                            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                            var sheet = spreadtemp.getSheet(0);
                            for(var i = 0;i < betotalcols - totalcols;i++)
                            {
                                sheet.addColumns(totalcols + i, 1);

                                var insertcol = {};
                                insertcol["col"] = totalcols + i;
                                insertcol["count"] = 1;
                                self.insertcols.push(insertcol);
                                self.cellinfos = self.formulabyrowcolchange(); //处理公式坐标
                                sheet.copyTo(0, totalcols + i - 1, 0, totalcols + i, sheet.getRowCount(), 1, GcSpread.Sheets.CopyToOption.Style);
                            }
                        }

                        // 复选框信息前端传后台
                        var becolpropertis = [];
                        for(var n=0;n<colcoordinates.length;n++)
                        {
                            var cpname = "#colname_" + colorders[n]; //shorts for col property name, for exemple:资产
                            var cpid1 = "#isnumber_" + colcoordinates[n]; //cpid shorts for columns properties isnumber, for example: isnumber_A
                            var cpid2 = "#isamount_" + colcoordinates[n]; //columns properties isamount
                            var cpid3 = "#isadjust_" + colcoordinates[n]; //columns properties isadjust
                            var cpid4 = "#isitem_" + colcoordinates[n]; //columns properties isitem
                            var checkcell1 = $(cpid1).find("input:checked").val(); //设置变量用于判断'数值列'复选框是否被选中
                            var checkcell2 = $(cpid2).find("input:checked").val(); //设置变量用于判断'汇总列'复选框是否被选中
                            var checkcell3 = $(cpid3).find("input:checked").val(); //设置变量用于判断'调整列'复选框是否被选中
                            var checkcell4 = $(cpid4).find("input:checked").val(); //设置变量用于判断'项目列'复选框是否被选中
                            if(!checkcell1){
                                var checkcell1 = "0";
                            }
                            if(!checkcell2){
                                var checkcell2 = "0";
                            }
                            if(!checkcell3){
                                var checkcell3 = "0";
                            }
                            if(!checkcell4){
                                var checkcell4 = "0";
                            }
                            becolpropertis.push({"report_code":bereportcode,
                                                "report_date":bereportdate,
                                                "col_name":$(cpname).val(),
                                                "col_order":colorders[n],
                                                "col_coordinate":colorders[n],
                                                "col_isnumber":checkcell1,
                                                "col_isamount":checkcell2,
                                                "col_isadjust":checkcell3,
                                                "col_isitem":checkcell4,
                                                });
                        }

                        self.colsproperties = becolpropertis;

                        //更新控件列名称
                        var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
                        var sheet = spreadtemp.getSheet(0);
                        for(var i = 0;i < becolpropertis.length;i++)
                        {
                            sheet.setValue(parseInt(betitlerows) + parseInt(beheadrows) - 1,i,becolpropertis[i]["col_name"]) ;
                            sheet.getRow(parseInt(betitlerows) + parseInt(beheadrows) - 1).font("bold 10pt Arial");
                            sheet.getCell(parseInt(betitlerows) + parseInt(beheadrows) - 1,i).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                        }

                        // var args = [bereportcode, bereportdate, bereportname, betitlerows, beheadrows, bebobyrows, betailrows, betotalrows, betotalcols];
                        // // alert(args);
                        // //用下面的方法将变量传回后台，then(function)内的功能是否有必要？
                        // var deftransforpropertiesparams = self._rpc({
                        //     model: 'ps.statement.statements',
                        //     method: 'get_reportproperties_from_frontend',
                        //     args: args
                        // }).then(function (result) {
                        //     if (!result) {
                        //         // alert(args);
                        //     } else {
                        //         alert("no result");
                        //     }
                        // });
                        // var args_cols = [bereportcode, bereportdate, becolpropertis];
                        // var deftransforcolpropertiesparams = self._rpc({
                        //     model: 'ps.statement.sheet.columns',
                        //     method: 'get_columnsproperties_from_frontend',
                        //     args: args_cols
                        // }).then(function (result) {
                        //     if (!result) {
                        //         // alert(args);
                        //     } else {
                        //         alert("no result");
                        //     }
                        // });

                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                    取消: function()
                    {
                        $div.empty();
                        $( this ).dialog( "close" );
                    },
                },
                close: function(event, ui)
                {
                    $div.empty();
                }
            });
        },
    });
    core.action_registry.add('statements', HomePage);

});
