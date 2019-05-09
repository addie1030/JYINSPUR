odoo.define('statements_pivot_sheet',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var HomePage=AbstractAction.extend({
        template: 'statements_pivot_template',
        init: function(parent,context){
            this._super(parent,context);
            this.name="statements_pivot";
            this.code = context.context.report_code;
            this.sheetname = context.context.report_name;
            this.date = context.context.report_date;
            this.category = context.context.category;
            this.titlerows = context.context.titlerows;
            this.headrows = context.context.headrows;
            this.bodyrows = context.context.bodyrows;
            this.tailrows = context.context.tailrows;
            this.bodycols = context.context.bodycols;
            this.intervalstart = context.context.intervalstart;
            this.intervalend = context.context.intervalend;
            this.startyear = context.context.startyear;
            this.fixedcolumns = context.context.fixedcolumns;
            this.pivotcolumns = context.context.pivotcolumns;
            this.fixcellcontents = context.context.fixcellcontents;
            this.pivotcellcontents = context.context.pivotcellcontents;

            this.cellinfos = [];   //单元格信息
            this.defineformulas = [];
            this.insertrows = [];
            this.insertcols = [];
            this.deleterows = [];
            this.deletecols = [];
        },
        events:{
            'click button#btnPrint': 'print',
            'click button#btnExport': 'export',
        },
        start: function()
        {
            var fiscaldate = this.date;
            var self = this;
            var company = "my company";
            var defcompany = this._rpc({model: 'ps.statement.statements',method: 'get_statement_company',args: []}).then(function (result)
            {
                if (result)
                {
                    company = result;
                    var columns = self.fixedcolumns.length + (parseInt(self.intervalend) - parseInt(self.intervalstart) + 1) * self.pivotcolumns.length;
                    var spread = new GcSpread.Sheets.Spread(document.getElementById('statements_pivot_sheet'), {sheetCount: 1});
                    spread.isPaintSuspended(true);
                    var sheet = spread.getActiveSheet();
                    sheet.setRowCount(parseInt(self.titlerows)+parseInt(self.headrows)+parseInt(self.bodyrows)+parseInt(self.tailrows));
                    sheet.setColumnCount(columns);
                    sheet.setName(self.sheetname+"("+self.intervalstart+"-"+self.intervalend+"月)");
                    sheet.addSpan(0, 0, 1, columns);
                    sheet.setRowHeight(0, 50);
                    sheet.getCells(0, 0, 0, columns).text(self.sheetname+"("+self.intervalstart+"-"+self.intervalend+"月)").font("20pt Calibri").textIndent(4);
                    sheet.getCells(0, 0, 0, columns).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                    sheet.getCells(0, 0, 0, columns).vAlign(GcSpread.Sheets.VerticalAlign.center);
                    sheet.setColumnWidth(0, 160);
                    sheet.setColumnWidth(columns/2, 100);
                    sheet.setColumnWidth(columns-1, 160);
                    sheet.getCell(1, columns-1).text("会小企01表");
                    sheet.getCell(1, columns-1).hAlign(GcSpread.Sheets.HorizontalAlign.right);
                    sheet.getCell(2, 0).text("单位名称："+company);

                    sheet.getCell(2, columns/2).text(fiscaldate.substring(0,4)+"年"+fiscaldate.substring(4,6)+"月");
                    sheet.getCell(2, columns-1).text("金额单位：元");
                    sheet.getCell(2, columns-1).hAlign(GcSpread.Sheets.HorizontalAlign.right);

                    var range = new GcSpread.Sheets.Range(parseInt(self.titlerows)+parseInt(self.headrows) - 1, 0, 1, parseInt(self.titlerows)+parseInt(self.headrows)+parseInt(self.bodyrows)+parseInt(self.tailrows));
                    sheet.setBorder(range,new GcSpread.Sheets.LineBorder("Black", GcSpread.Sheets.LineStyle.medium), {
                        all: true
                    });
                    var range1 = new GcSpread.Sheets.Range(parseInt(self.titlerows)+parseInt(self.headrows), 0, parseInt(self.bodyrows), columns);
                    sheet.setBorder(range1,new GcSpread.Sheets.LineBorder("Black", GcSpread.Sheets.LineStyle.thin), {
                        all: true
                    });

                    //固定列内容填充
                    if (self.fixcellcontents)
                    {
                        var colid = -1;
                        var srccol = 9999;
                        for(var i = 0;i < self.fixcellcontents.length;i++)
                        {
                            var row = self.fixcellcontents[i]["row"];
                            var col = self.fixcellcontents[i]["col"];
                            if (srccol != col)
                            {
                                srccol = col;
                                colid = colid + 1;
                            }
                            var value = self.fixcellcontents[i]["value"];
                            if (value == 0)
                            {
                                value = "";
                            }
                            if (!isNaN(value))
                            {
                                value = String(value);
                            }
                            sheet.setValue(row,colid,value);
                            sheet.autoFitColumn(colid);
                        }
                    }

                    // 表头行处理
                    sheet.setSelection(parseInt(self.titlerows)+parseInt(self.headrows) - 1,0,1,1);
                    var selectedRanges = sheet.getSelections();
                    var selectedrow = selectedRanges[0].row;
                    var selectedrowcount = selectedRanges[0].rowCount;
                    var selectedcol = selectedRanges[0].col;
                    var selectedcolcount = selectedRanges[0].colCount;
                    sheet.addRows(selectedrow, 1);
                    sheet.copyTo(selectedrow+1,0,selectedrow,selectedcol,1,columns,GcSpread.Sheets.CopyToOption.Style);
                    // 表头行固定列处理
                    for(var i = 0;i < self.fixedcolumns.length;i++)
                    {
                        sheet.addSpan(parseInt(self.titlerows) + parseInt(self.headrows) - 1, i, 2, 1);
                        sheet.setValue(parseInt(self.titlerows) + parseInt(self.headrows) - 1,i,self.fixedcolumns[i].col_name);

                        sheet.getCell(parseInt(self.titlerows)+parseInt(self.headrows) - 1, i).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                        sheet.getCell(parseInt(self.titlerows)+parseInt(self.headrows) - 1, i).vAlign(GcSpread.Sheets.VerticalAlign.center);
                    }

                    // 表头行透视列处理
                    for(var i = 0;i <= parseInt(self.intervalend) - parseInt(self.intervalstart);i++)
                    {
                        var colid = self.fixedcolumns.length + i * self.pivotcolumns.length;
                        sheet.addSpan(parseInt(self.titlerows) + parseInt(self.headrows) - 1, colid, 1, self.pivotcolumns.length);
                        if (parseInt(self.intervalend) > 8) {
                            var value = String(parseInt(self.intervalstart) + i) + "月";
                        }
                        else {
                            var value = "0" + String(parseInt(self.intervalstart) + i) + "月";
                        }

                        sheet.setValue(parseInt(self.titlerows) + parseInt(self.headrows) - 1, colid, value);
                        sheet.getCell(parseInt(self.titlerows) + parseInt(self.headrows) - 1, colid).hAlign(GcSpread.Sheets.HorizontalAlign.center);
                        sheet.getCell(parseInt(self.titlerows) + parseInt(self.headrows) - 1, colid).vAlign(GcSpread.Sheets.VerticalAlign.center);

                        for (var j = 0; j < self.pivotcolumns.length; j++)
                        {
                            sheet.setValue(parseInt(self.titlerows) + parseInt(self.headrows), self.fixedcolumns.length + i * self.pivotcolumns.length + j, self.pivotcolumns[j].col_name);
                        }
                    }
                    //透视列内容填充
                    if (self.pivotcellcontents)
                    {
                        var colid = self.fixedcolumns.length - 1;
                        var srccol = 9999;
                        for (var k = 0; k < self.pivotcellcontents.length; k++)
                        {
                            var row = self.pivotcellcontents[k]["row"];
                            var col = self.pivotcellcontents[k]["col"];
                            if (srccol != col) {
                                srccol = col;
                                colid = colid + 1;
                            }

                            sheet.autoFitColumn(colid);
                            sheet.getCell(row + 1, colid).formatter("#,##0.00;[Red]#,##0.00");
                            var month = self.pivotcellcontents[k]["month"];
                            var value = self.pivotcellcontents[k]["value"];

                            if (value == 0) {
                                value = "";
                            }
                            sheet.setValue(row + 1, colid, value);
                        }
                    }

                    spread.isPaintSuspended(false);
                    spread.newTabVisible(false);

                    var setctions = document.querySelectorAll("section");
                    setctions[8].childNodes[3].value = self.startyear + '-' + self.intervalstart;
                    $("#user_date_end").val(self.startyear + '-' + self.intervalend);
                    $("#report_title").html(self.sheetname);
                }
            });
        },
        render: function ()
        {},
        export: function(){
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_pivot_sheet"));
            var json = JSON.stringify(spreadtemp.toJSON());

            if (json.length == 0)
            {
                alert("传递的JSON字符串为空，请检查。");
                return;
            }else{
                var myForm = document.createElement("form");
                myForm.method = "post";
                myForm.target="_blank"
                myForm.action = "http://115.28.63.151：8199/SpreadJsExcel.aspx";
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

        print: function ()
        {
            var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_pivot_sheet"));
            var sheet = spreadtemp.getSheet(0);
            var printInfo = sheet.printInfo();
            printInfo.orientation(GcSpread.Sheets.PrintPageOrientation.portrait);
            printInfo.margin({top:0, bottom:0, left:0, right:0, header:0, footer:0});
            spreadtemp.print(0);
        },

    });
    core.action_registry.add('statements_pivot', HomePage);

});
