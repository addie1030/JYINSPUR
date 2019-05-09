// $("#btnVCenter").click(function() {
//     alert("222")
// });
//Description: Alignment for text in selected cells: vertical center.
$("#btnVCenter").click(function() {
    // get spread object
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
});
//Description:Automatically fits the viewport row.
$("#btnAutoFitR").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    for (var i = rows; i < rows + rowCounts; i++) {
        activeSheet.autoFitRow(i);
    }
});

//Operation on the columns
//Description: add a column.
// $("#btnAddCol").click(function() {
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var activeSheet = spreadtemp.getActiveSheet();
//     var selectedcells = activeSheet.getSelections();
//     var cols = selectedcells[0].col;	//the start column of selected ranges;
//     activeSheet.addColumns(cols, 1);
// });
//
// //Description: delete the hidden columns.
// $("#btnDelCol").click(function() {
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var activeSheet = spreadtemp.getActiveSheet();
//     var selectedcells = activeSheet.getSelections();
//     var cols = selectedcells[0].col;	//the start column of selected ranges;
//     var colCounts = selectedcells[0].colCount;	//the number of selected cols;
//     activeSheet.deleteColumns(cols, colCounts);
// });

//Description: show the hidden columns.
$("#btnShowC").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected columns;
    for (var i = cols-1 ; i < cols + colCounts; i++) {
        activeSheet.setColumnVisible(i,true,GcSpread.Sheets.SheetArea.viewport);
    }
});

//Description: hide the selected columns.
$("#btnHideC").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected columns;
    for (var i = cols; i < cols + colCounts; i++) {
        activeSheet.setColumnVisible(i,false,GcSpread.Sheets.SheetArea.viewport);
    }
});

//Description: automatically fits the viewport columns.
$("#btnAutoFitC").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    for (var i = cols; i < cols + colCounts; i++) {
        activeSheet.autoFitColumn(i);
    }
});

//Description: make an attempt.
$("#btnClearBorder").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var selectedranges = new GcSpread.Sheets.Range(rows, cols, rowCounts, colCounts, GcSpread.Sheets.SheetArea.viewport);
    activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.none), { all:true }, 3);
});

//Description: transfer numbers to Chinese characters
var numt = true;
$("#btnToggleCase").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    if(numt){
        for (var k = cols; k < cols + colCounts; k++) {
            for (var i = rows, j = k; i < rows + rowCounts; i++) {
                activeSheet.setFormatter(i,j,"[DBNum2][$-804]General");
            }
        }
    }else{
        for (var k = cols; k < cols + colCounts; k++) {
            for (var i = rows, j = k; i < rows + rowCounts; i++) {
                activeSheet.setFormatter(i,j,"[DBNum3][$-804]General");
            }
        }
    }
    numt = !numt
});

//Description: Set font color.
$("#btnForeColor").click(function() {
    var $div=$("<div>",{id:"dialog-message",title:"字体颜色"});
    var $sectop = $("<section class=\"forecolorguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"forecolorguidetop\">");
    var $secleft = $("<section class=\"colorlist\" style=\"float:left;height: 100%;width: 100%;\" id=\"colorlist\">");
    var $secleftleft = $("<section class=\"forecoloroperateselect\" id=\"forecoloroperateselect\" style=\"height: 100%;width: 100%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"forecolorselectlabel0\" id=\"forecolorselectlabel0\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"forecolorselectselect0\" id=\"forecolorselectselect0\" style=\"height: 100%;width: 50%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("颜色：");
    $secleftleftleft.append($p0);
    var $selectforecolor=$("<select>",{id:"setforecolor"});
    $selectforecolor.css("height","21px");
    $secleftleftright.append($selectforecolor);
    var forecolorcode = ["#000000","#434343","#666666","#cccccc","#d9d9d9","#ffffff","#980000","#ff0000","#ff9900","#ffff00",
    "#00ff00","#00ffff","#4a86e8","#0000ff","#9900ff","#ff00ff","#e6b8af","#f4cccc","#fce5cd","#fff2cc","#d9ead3","#d0e0e3",
    "#c9daf8","#cfe2f3","#d9d2e9","#ead1dc","#dd7e6b","#ea9999","#f9cb9c","#ffe599","#b6d7a8","#a2c4c9","#a4c2f4","#9fc5e8",
    "#b4a7d6","#d5a6bd","#cc4125","#e06666","#f6b26b","#ffd966","#93c47d","#76a5af","#6d9eeb","#6fa8dc","#8e7cc3","#c27ba0",
    "#a61c00","#cc0000","#e69138","#f1c232","#6aa84f","#45818e","#3c78d8","#3d85c6","#674ea7","#a64d79","#5b0f00","#660000",
    "#783f04","#7f6000","#274e13","#0c343d","#1c4587","#073763","#20124d","#4c1130"];
    // alert(forecolorcode.length);//显示包含颜色的数组
    for(var i=0;i < forecolorcode.length;i++)
    {
        $selectforecolor.append("<option style=\'background-color:"+forecolorcode[i]+"\' value='"+forecolorcode[i]+"'></option>");
    }
    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    $sectop.append($secleft);
    // $sectop.append($secright);
    $div.append($sectop);

    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var rows2 = rows + rowCounts - 1;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var cols2 = cols + colCounts - 1;
    //change事件的用法
    $selectforecolor.change(function(optionforecolor){
        var optionforecolor=$selectforecolor.find('option:selected').val();
        $selectforecolor.css("background-color",optionforecolor);
    });
    $div.dialog({
        modal: true,
        width: 260,
        buttons: {
            确定: function()
            {
                // alert(optionforecolor);//显示颜色
                var optionforecolor=$selectforecolor.find('option:selected').val();
                activeSheet.getCells(rows,cols,rows2,cols2).foreColor(optionforecolor);

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
});
//设置单元格背景色
$("#btnBackColor").click(function() {
    var $div=$("<div>",{id:"dialog-message",title:"背景颜色"});
    var $sectop = $("<section class=\"backcolorguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"backcolorguidetop\">");
    var $secleft = $("<section class=\"backcolorlist\" style=\"float:left;height: 100%;width: 100%;\" id=\"backcolorlist\">");
    var $secleftleft = $("<section class=\"backcoloroperateselect\" id=\"backcoloroperateselect\" style=\"height: 100%;width: 100%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"backcolorselectlabel0\" id=\"backcolorselectlabel0\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"backcolorselectselect0\" id=\"backcolorselectselect0\" style=\"height: 100%;width: 50%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("颜色：");
    $secleftleftleft.append($p0);
    var $selectbackcolor=$("<select>",{id:"setbackcolor"});
    $selectbackcolor.css("height","21px");
    $secleftleftright.append($selectbackcolor);
    var backcolorcode = ["#000000","#434343","#666666","#cccccc","#d9d9d9","#ffffff","#980000","#ff0000","#ff9900","#ffff00",
    "#00ff00","#00ffff","#4a86e8","#0000ff","#9900ff","#ff00ff","#e6b8af","#f4cccc","#fce5cd","#fff2cc","#d9ead3","#d0e0e3",
    "#c9daf8","#cfe2f3","#d9d2e9","#ead1dc","#dd7e6b","#ea9999","#f9cb9c","#ffe599","#b6d7a8","#a2c4c9","#a4c2f4","#9fc5e8",
    "#b4a7d6","#d5a6bd","#cc4125","#e06666","#f6b26b","#ffd966","#93c47d","#76a5af","#6d9eeb","#6fa8dc","#8e7cc3","#c27ba0",
    "#a61c00","#cc0000","#e69138","#f1c232","#6aa84f","#45818e","#3c78d8","#3d85c6","#674ea7","#a64d79","#5b0f00","#660000",
    "#783f04","#7f6000","#274e13","#0c343d","#1c4587","#073763","#20124d","#4c1130"];
    // alert(backcolorcode.length);//显示包含颜色的数组
    for(var i=0;i < backcolorcode.length;i++)
    {
        $selectbackcolor.append("<option style=\'background-color:"+backcolorcode[i]+"\' value='"+backcolorcode[i]+"'></option>");
    }
    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    $sectop.append($secleft);
    // $sectop.append($secright);
    $div.append($sectop);

    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var rows2 = rows + rowCounts - 1;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var cols2 = cols + colCounts - 1;
    $selectbackcolor.change(function(optionbackcolor){
        var optionbackcolor=$selectbackcolor.find('option:selected').val();
        $selectbackcolor.css("background-color",optionbackcolor);
    });
    $div.dialog({
        modal: true,
        width: 260,
        buttons: {
            确定: function()
            {
                // alert(optionbackcolor);//显示颜色
                var optionbackcolor=$selectbackcolor.find('option:selected').val();
                activeSheet.getCells(rows,cols,rows2,cols2).backColor(optionbackcolor);

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

});

//Description: Set the Height for the Rows
$("#btnSetRowHeight").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var rows2 = rows + rowCounts - 1;
    var rowheight = activeSheet.getRowHeight(rows,GcSpread.Sheets.SheetArea.viewport);

    var $div=$("<div>",{id:"dialog-message",title:"设置行高"});
    var $sectop = $("<section class=\"rowheightguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"rowheightguidetop\">");
    var $secleft = $("<section class=\"rowheightset\" style=\"float:left;height: 100%;width: 100%;\" id=\"rowheightset\">");
    var $secleftleft = $("<section class=\"rowheightoperateset\" id=\"rowheightoperateset\" style=\"height: 100%;width: 100%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"rowheightesetlabel\" id=\"rowheightesetlabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"rowheightesetinput\" id=\"rowheightesetinput\" style=\"height: 100%;width: 50%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("行高：");
    $secleftleftleft.append($p0);
    var $setrowheight=$("<input>",{id:"setrowheights"});
    $setrowheight.css("height","21px");
    $setrowheight.css("width","50%");
    $setrowheight.css("text-align","center");
    $setrowheight.val(rowheight);
    $secleftleftright.append($setrowheight);

    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    $sectop.append($secleft);
    // $sectop.append($secright);
    $div.append($sectop);

    $div.dialog({
        modal: true,
        width: 260,
        buttons: {
            确定: function()
            {
                var rowheight1 = $setrowheight.val();
                // alert(rowheight1);//显示输入行高
                for(var i = rows; i < rows2 + 1; i++){
                    activeSheet.setRowHeight(i, rowheight1,GcSpread.Sheets.SheetArea.viewport);
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


});
//设置列宽
$("#btnSetColWidth").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var cols2 = cols + colCounts - 1;
    var colwidth = activeSheet.getColumnWidth(cols, GcSpread.Sheets.SheetArea.viewport);


    var $div=$("<div>",{id:"dialog-message",title:"设置列宽"});
    var $sectop = $("<section class=\"colwidthguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"colwidthguidetop\">");
    var $secleft = $("<section class=\"colwidthset\" style=\"float:left;height: 100%;width: 100%;\" id=\"colwidthset\">");
    var $secleftleft = $("<section class=\"colwidthoperateset\" id=\"colwidthoperateset\" style=\"height: 100%;width: 100%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"colwidthesetlabel\" id=\"colwidthesetlabel\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"colwidthesetinput\" id=\"colwidthesetinput\" style=\"height: 100%;width: 50%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("列宽：");
    $secleftleftleft.append($p0);
    var $setcolumnwidth=$("<input>",{id:"setcolumnwidths"});
    $setcolumnwidth.css("height","21px");
    $setcolumnwidth.css("width","50%");
    $setcolumnwidth.css("text-align","center");
    $setcolumnwidth.val(colwidth);
    $secleftleftright.append($setcolumnwidth);

    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    $sectop.append($secleft);
    // $sectop.append($secright);
    $div.append($sectop);

    $div.dialog({
        modal: true,
        width: 260,
        buttons: {
            确定: function()
            {
                var columnwidth1 = $setcolumnwidth.val();
                for(var i = cols; i < cols2 + 1; i++){
                    activeSheet.setColumnWidth(i, columnwidth1,GcSpread.Sheets.SheetArea.viewport);
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


});
//设置单元格格式
$("#btnSetFormat").click(function() {
    // companydes = self.env.user.company_id.name
    var $div=$("<div>",{id:"dialog-message",title:"单元格格式"});
    var $sectop = $("<section class=\"cellformatguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"cellformatguidetop\">");
    var $secleft = $("<section class=\"cellformatlist\" style=\"float:left;height: 100%;width: 100%;\" id=\"cellformatlist\">");
    var $secleftleft = $("<section class=\"cellformatoperateselect\" id=\"cellformatoperateselect\" style=\"height: 100%;width: 100%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"cellformatselectlabel0\" id=\"cellformatselectlabel0\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"cellformatselectselect0\" id=\"cellformatselectselect0\" style=\"height: 100%;width: 50%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("格式：");
    $secleftleftleft.append($p0);
    var $selectcellformat=$("<select>",{id:"setcellformat"});
    $selectcellformat.css("height","21px");
    $secleftleftright.append($selectcellformat);
    var cellformatlist = ["General","#,##0.00;[Red]#,##0.00","0.00%;[red]0.00%","# ??/??;[Red]# ??/??","0.00E+00;[Red]0.00E+00","@"];
    var cellformatname = ["常规","数值","百分比","分数","科学计数","文本"];
    // alert(cellformatlist.length);//显示包含单元格格式的数组
    // alert(cellformatname.length);//显示包含单元格格式名称的数组
    for(var i=0;i < cellformatlist.length;i++)
    {
        $selectcellformat.append("<option value='"+cellformatlist[i]+"'>"+cellformatname[i]+"</option>");
    }
    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    $sectop.append($secleft);
    // $sectop.append($secright);
    $div.append($sectop);

    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var rows2 = rows + rowCounts - 1;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var cols2 = cols + colCounts - 1;

    $div.dialog({
        modal: true,
        width: 260,
        buttons: {
            确定: function()
            {
                // alert(optioncellformat);//显示颜色
                var optioncellformat=$selectcellformat.find('option:selected').val();
                activeSheet.getCells(rows,cols,rows2,cols2).formatter(optioncellformat);

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
});
//自动换行
var numWW = true;
$("#btnWordWrap").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var selectedcells = activeSheet.getSelections();
    var rows = selectedcells[0].row;	//the start row of selected ranges;
    var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
    var rows2 = rows + rowCounts - 1;
    var cols = selectedcells[0].col;	//the start column of selected ranges;
    var colCounts = selectedcells[0].colCount;	//the number of selected column;
    var cols2 = cols + colCounts - 1;
    if(numWW){
        activeSheet.getCells(rows,cols,rows2,cols2).wordWrap(true);
        for (var i = rows; i < rows + rowCounts; i++) {
            activeSheet.autoFitRow(i);
        }
    }else{
        activeSheet.getCells(rows,cols,rows2,cols2).wordWrap(false);
        for (var i = rows; i < rows + rowCounts; i++) {
            activeSheet.autoFitRow(i);
         }
    }
    return numWW = !numWW;
});

//设置框线种类
$("#btnSetLineStyle").click(function() {
    // companydes = self.env.user.company_id.name
    var $div=$("<div>",{id:"dialog-message",title:"边框设置"});
    var $sectop = $("<section class=\"linetypeguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"linetypeguidetop\">");
    var $secleft = $("<section class=\"linetypelist\" style=\"float:left;height: 100%;width: 50%;\" id=\"linetypelist\">");
    var $secleftleft = $("<section class=\"linetypeoperateselect\" id=\"linetypeoperateselect\" style=\"height: 100%;width: 50%;margin: 0 auto;\" >");
    var $secleftleftleft = $("<section class=\"linetypeselectlabel0\" id=\"linetypeselectlabel0\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $secleftleftright = $("<section class=\"linetypeselectselect0\" id=\"linetypeselectselect0\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
    var $p0=$("<p style='height:21px;'>").html("线条：");
    $secleftleftleft.append($p0);
    var $selectlinetype=$("<select>",{id:"setlinetype"});
    $selectlinetype.css("height","21px");
    $secleftleftright.append($selectlinetype);
    var thinL = GcSpread.Sheets.LineStyle.thin;
    var mediumL = GcSpread.Sheets.LineStyle.medium;
    var thickL = GcSpread.Sheets.LineStyle.thick;
    var dottedL = GcSpread.Sheets.LineStyle.dotted;
    var dashedL = GcSpread.Sheets.LineStyle.dashed;
    var doubleL = GcSpread.Sheets.LineStyle.double;
    var dashdotL = GcSpread.Sheets.LineStyle.dashDot;
    var linetypelist = [0,1,2,3,4,5,6];
    var linetypelist2 = [thinL,mediumL,thickL,dottedL,dashedL,doubleL,dashdotL];
    // alert(linetypelist);
    var linetypename = ["细线","中线","粗线","点线","虚线","双线","点虚线"];
    // alert(linetypelist.length);//显示包含单元格格式的数组
    // alert(linetypename.length);//显示包含单元格格式名称的数组
    for(var i=0;i < linetypelist.length;i++)
    {
        $selectlinetype.append("<option value='"+linetypelist[i]+"'>"+linetypename[i]+"</option>");
    }
    $secleftleft.append($secleftleftleft);
    $secleftleft.append($secleftleftright);
    $secleft.append($secleftleft);

    var $secright = $("<section class=\"linestyleoperate\" id=\"linestyleoperate\" style=\"float:right;height: 100%;width: 50%;\" >");
    var $secrightleft = $("<section class=\"linestyleoperateselect\" id=\"linestyleoperateselect\" style=\"height: 100%;width: 50%;margin: 0 auto;\" >");
    var $secrightleftleft = $("<section class=\"linestyleoperateselectlabel\" id=\"linestyleoperateselectlabel\" style=\"display: inline-block;height: 100%;width: 30%;\" >");
    var $secrightleftright = $("<section class=\"linestyleoperateselectselect\" id=\"linestyleoperateselectselect\" style=\"height: 100%;width: 60%;display: inline-block;\" >");

    var $p1=$("<p style='height:21px;'>").html("边框：");
    $secrightleftleft.append($p1);
    //设置下拉菜单以及菜单内的选项
    var $selectlinestyle=$("<select>",{id:"setlinestyle"});
    $selectlinestyle.css("height","21px");
    $secrightleftright.append($selectlinestyle);
    var linestylelist = [0,1,2,3,4,5,6];
    var linestylelist2 = [{all:true},{left:true},{right:true},{top:true},
        {bottom:true},{inside:true},{outline:true}];
    // alert(linestylelist);
    var linestylename = ["全边框","左边框","右边框","上边框","下边框","内边框","外边框"];
    // alert(linestylename);
    for(var i=0;i < linestylename.length;i++)
    {
        $selectlinestyle.append("<option value='"+linestylelist[i]+"'>"+linestylename[i]+"</option>");
    }

    $secrightleft.append($secrightleftleft);
    $secrightleft.append($secrightleftright);

    $secright.append($secrightleft);

    $sectop.append($secleft);
    $sectop.append($secright);
    $div.append($sectop);

    var $sec2nd = $("<section class=\"linecolorguidetop\" style=\"height: 100%;width: 100%;overflow: hidden;\" id=\"linecolorguidetop\">");
    var $sec2ndleft = $("<section class=\"linecolorlist\" style=\"float:left;height: 100%;width: 50%;\" id=\"linecolorlist\">");
    var $sec2ndleftleft = $("<section class=\"linecoloroperateselect\" id=\"linecoloroperateselect\" style=\"height: 100%;width: 50%;margin: 0 auto;\" >");
    var $sec2ndleftleftleft = $("<section class=\"linecolorselectlabel0\" id=\"linecolorselectlabel0\" style=\"display: inline-block;height: 100%;width: 36%;margin: 0 auto;\" >");
    var $sec2ndleftleftright = $("<section class=\"linecolorselectselect0\" id=\"linecolorselectselect0\" style=\"height: 100%;width: 60%;display: inline-block;\" >");
    var $p3=$("<p style='height:21px;'>").html("颜色：");
    $sec2ndleftleftleft.append($p3);
    var $selectlinecolor=$("<select>",{id:"setlinecolor"});
    $selectlinecolor.css("height","21px");
    $sec2ndleftleftright.append($selectlinecolor);
    var linecolorcode = ["#000000","#434343","#666666","#cccccc","#d9d9d9","#ffffff","#980000","#ff0000","#ff9900","#ffff00",
    "#00ff00","#00ffff","#4a86e8","#0000ff","#9900ff","#ff00ff","#e6b8af","#f4cccc","#fce5cd","#fff2cc","#d9ead3","#d0e0e3",
    "#c9daf8","#cfe2f3","#d9d2e9","#ead1dc","#dd7e6b","#ea9999","#f9cb9c","#ffe599","#b6d7a8","#a2c4c9","#a4c2f4","#9fc5e8",
    "#b4a7d6","#d5a6bd","#cc4125","#e06666","#f6b26b","#ffd966","#93c47d","#76a5af","#6d9eeb","#6fa8dc","#8e7cc3","#c27ba0",
    "#a61c00","#cc0000","#e69138","#f1c232","#6aa84f","#45818e","#3c78d8","#3d85c6","#674ea7","#a64d79","#5b0f00","#660000",
    "#783f04","#7f6000","#274e13","#0c343d","#1c4587","#073763","#20124d","#4c1130"];
    // alert(linecolorcode.length);//显示包含颜色的数组
    for(var i=0;i < linecolorcode.length;i++)
    {
        $selectlinecolor.append("<option style=\'background-color:"+linecolorcode[i]+"\' value='"+linecolorcode[i]+"'></option>");
    }
    $sec2ndleftleft.append($sec2ndleftleftleft);
    $sec2ndleftleft.append($sec2ndleftleftright);
    $sec2ndleft.append($sec2ndleftleft);

    $sec2nd.append($sec2ndleft);
    $div.append($sec2nd);

    $selectlinecolor.change(function(optionlinecolor){
    var optionlinecolor=$selectlinecolor.find('option:selected').val();
    $selectlinecolor.css("background-color",optionlinecolor);
    });

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

    $div.dialog({
        modal: true,
        width: 600,
        buttons: {
            确定: function()
            {
                // alert(optionlinetype);//显示颜色
                var optionlinetype=$selectlinetype.find('option:selected').val();
                var optionlinestyle=$selectlinestyle.find('option:selected').val();
                var optionlinecolor=$selectlinecolor.find('option:selected').val();
                // alert(optionlinestyle);
                activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder(optionlinecolor,linetypelist2[optionlinetype]),
                    linestylelist2[optionlinestyle], 3);
                // alert(optionlinetype);
                // activeSheet.setBorder(selectedranges, new GcSpread.Sheets.LineBorder("black",optionlinetype), { all:true }, 3);
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
});

//Description: Make an attempt;
$("#btnTry").click(function() {
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var sheet = spreadtemp.getActiveSheet();
    // sheet.setValue(1,0, 50,3);
    // sheet.setValue(2,0, 100,3);
    // sheet.setValue(3,0, 2,3);
    // sheet.setValue(4,0, 60,3);
    // sheet.setValue(5,0, 90,3);
    // sheet.setValue(6,0, 3,3);
    // sheet.setValue(7,0, 40,3);
    // sheet.setValue(8,0, 70,3);
    // sheet.setValue(9,0, 5,3);
    // sheet.setValue(10,0, 35,3);
    // sheet.setSelection(1,1,11,1);
    sheet.getCell(1, 1).borderTop(new GcSpread.Sheets.LineBorder("black",GcSpread.Sheets.LineStyle.double));
    sheet.copyTo(1,1,2,2,2,2,GcSpread.Sheets.CopyToOption.Style);
});

//add shortcut for the spread sheet
// function addkeymap()
// {
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var activeSheet = spreadtemp.getActiveSheet();
//     //Map the created action to the "Ctrl+B" key.
//     activeSheet.addKeyMap(GcSpread.Sheets.Key.b, true, false, false, false, fontboldjs);
//     //Map the created action to the "Ctrl+I" key
//     activeSheet.addKeyMap(GcSpread.Sheets.Key.i, true, false, false, false, fontitalicjs);
// }
//
// function fontboldjs(){
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var activeSheet = spreadtemp.getActiveSheet();
//     var selectedcells = activeSheet.getSelections();
//     var rows = selectedcells[0].row;	//the start row of selected ranges;
//     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
//     var rows2 = rows + rowCounts - 1;
//     var cols = selectedcells[0].col;	//the start column of selected ranges;
//     var colCounts = selectedcells[0].colCount;	//the number of selected column;
//     var cols2 = cols + colCounts - 1;
//     var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
//     var fontElement = $("<span></span>");
//     var fontweight = 'bold';
//     var fontactualstyle = cssStyle.font;
//     fontElement.css("font", cssStyle.font); // 字体概括
//     cssStyle.font = fontElement.css("font");
//     if(fontactualstyle.match(fontweight)){
//         fontElement.css("font-weight", "normal");
//         cssStyle.font = fontElement.css("font");
//         activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
//     }else{
//         fontElement.css("font-weight", "bold"); // 字体粗细
//         cssStyle.font = fontElement.css("font");
//         activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
//     }
// }
//
// function fontitalicjs() {
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var activeSheet = spreadtemp.getActiveSheet();
//     var selectedcells = activeSheet.getSelections();
//     var rows = selectedcells[0].row;	//the start row of selected ranges;
//     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
//     var rows2 = rows + rowCounts - 1;
//     var cols = selectedcells[0].col;	//the start column of selected ranges;
//     var colCounts = selectedcells[0].colCount;	//the number of selected column;
//     var cols2 = cols + colCounts - 1;
//     var cssStyle = activeSheet.getActualStyle(rows,cols) || new GcSpread.Sheets.Style();
//     var fontElement = $("<span></span>");
//     // var fontweight = 'bold';
//     var fontstyle = 'italic';
//     var fontactualstyle = cssStyle.font;
//     fontElement.css("font", cssStyle.font); // 字体概括
//     if(fontactualstyle.match(fontstyle)){//判断字体内是否包含字符串"italic"
//         fontElement.css("font-style", "normal");
//         cssStyle.font = fontElement.css("font");
//         activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
//     }else{
//         fontElement.css("font-style", "italic"); // 字体倾斜
//         cssStyle.font = fontElement.css("font");
//         activeSheet.getCells(rows,cols,rows2,cols2).font(cssStyle.font);
//     }
// }
//
//
// // $(document).ready(function () {
// //      addkeymap();
// // })
// window.onload = function () {
//     alert("111");
//     addkeymap();
// }