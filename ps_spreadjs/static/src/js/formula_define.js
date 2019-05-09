$("#btnFormula").click(function(){
    //迁移到statement.js的defineformula方法中20180622
    // var div = document.getElementById("statement_formula");
    // if(div.style.display == "none"){
    //     div.style.display = "block";
    // } else {
    //     div.style.display = "none";
    // }
});

function TrOnClick() {
    var tbl = document.getElementById("formula");
    var trs = tbl.getElementsByTagName("tr");
    var namebox = $("input[name^='boxs']");
    for(var i = 0; i < namebox.length; i++) {
         if (namebox[i].checked)
         {
             trs[i+1].style.background = "#E0E0E0";
         }
         else {
            trs[i+1].style.background = "white";
         }
    }
};

function allcheck() {
    var nn = $("#allboxs").is(":checked"); //判断th中的checkbox是否被选中，如果被选中则nn为true，反之为false
    var tbl = document.getElementById("formula");
    var trs = tbl.getElementsByTagName("tr");
    var namebox = $("input[name='boxs']");  //获取name值为boxs的所有input

    for(var i = 0; i < namebox.length; i++) {
        if(nn == true) {
            namebox[i].checked = true;    //js操作选中checkbox
            trs[i + 1].style.background = "#E0E0E0";
        }
        else{
            namebox[i].checked=false;
            trs[i+1].style.background = "white";
        }
    }
};

//迁移到statement.js的deleteformula方法中20180625
// function deleteCurrentRow(obj){
//     var tbl = document.getElementById("formula");
//     var trs = tbl.getElementsByTagName("tr");
//     alert(trs.length);
//     var tr=obj.parentNode.parentNode;
//     var tbody=tr.parentNode;
//     tbody.removeChild(tr);
//     //只剩行首时删除表格
//     if(tbody.rows.length==1) {
//         tbody.parentNode.removeChild(tbody);
//     }
//     var tbl = document.getElementById("formula");
//     var trs = tbl.getElementsByTagName("tr");
//     alert(trs.length);
// };

function deleteCurrentRow(obj){
    var tbl = document.getElementById("arithmetictable");
    var trs = tbl.getElementsByTagName("tr");
    var tr=obj.parentNode.parentNode;
    var tbody=tr.parentNode;
    tbody.removeChild(tr);
    //只剩行首时删除表格，删除表格后，没法添加公式了，20180710已验证
    // if(tbody.rows.length==0)
    // {
    //     tbody.parentNode.removeChild(tbody);
    // }
};

//迁移到statement.js的rightmenu_formula_guide方法中，使用按钮事件替换右键20180627
//原因是没法使用公用变量
// function rightmenu_formula_guide() {
//
//     var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//     var sheet = spreadtemp.getSheet(0);
//     var selectedRanges = sheet.getSelections();
//     var selectedrow = selectedRanges[0].row;
//     var selectedrowcount = selectedRanges[0].rowCount;
//     var selectedcol = selectedRanges[0].col;
//     var selectedcolcount = selectedRanges[0].colCount;
//
//     if ((selectedrow <= 0 ) || (selectedrow >= sheet.getRowCount()))
//     {
//         alert("选中区域的行不在表格范围内，请检查。")
//         window.event.returnValue = false;
//         return false;
//     }
//
//     if ((selectedcol <= 0 ) || (selectedcol >= sheet.getColumnCount()))
//     {
//         alert("选中区域的列不在表格范围内，请检查。")
//         window.event.returnValue = false;
//         return false;
//     }
//     // console.log(self);
//     // console.log(event);
//
//     var $div=$("<div>",{id:"dialog-message",title:"公式定义向导"});
//     var $sec = $("<section class=\"formulalist\" style=\"float:left;height: 100%;\" id=\"formulalist\">");
//     $sec=$sec.append('<select style= "height:21px" name="formulas" id="formulas"></select>');
//
//     var defgetformula = this._rpc({
//         model: 'ps.statement.formulas',
//         method: 'get_formulas',
//     }).then(function (result) {
//         if (result)
//         {
//             for(var i=0;i < result.length;i++)
//             {
//                 $("#formulas").append("<option value='"+result[i].name+"'>"+result[i].formula_summary+"</option>");
//             }
//         }
//     });
//
//     $div=$div.append($sec);
//     var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("所有的表单字段都是必填的。");
//     $div=$div.append($paa);
//     var $p=$("<p>").html("报表编号");
//     $div=$div.append($p);
//     $div=$div.append('<input type=\"text\" name=\"report_code\" id="report_code" /> ');
//     var $p1=$("<p>").html("报表名称");
//     $div=$div.append($p1);
//     $div=$div.append('<input type=\"text\" name=\"report_name\" id="report_name"/> ');
//     var $p2=$("<p>").html("编报时间");
//     $div=$div.append($p2);
//     $div=$div.append('<select style= "height:21px" name="category" id="category">\n' +
//         '\t\t\t<option value ="month" selected = "selected">月报表</option>\n' +
//         '\t\t</select>');
//
//     $div.dialog({
//         modal: true,
//         buttons: {
//             确定: function()
//             {
//
//                 $( this ).dialog( "close" );
//             }
//         }
//     });
//
//     window.event.returnValue = false;
//     return false;
// // }

//迁移到statement.js的formulaeditkeydown方法中，使用按钮事件替换右键20180709
//原因是没法使用公用变量self.defineformulas
// function formulaedit(){
//     if(event.keyCode==13)
//     {
//         var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
//         var sheet = spreadtemp.getSheet(0);
//         var selectedRanges = sheet.getSelections();
//         var selectedrow = selectedRanges[0].row;
//         var selectedrowcount = selectedRanges[0].rowCount;
//         var selectedcol = selectedRanges[0].col;
//         var selectedcolcount = selectedRanges[0].colCount;
//
//         if ((selectedrow < 0 ) || (selectedrow > sheet.getRowCount()))
//         {
//             alert("选中区域的行不在表格范围内，请检查。")
//             window.event.returnValue = false;
//             return false;
//         }
//
//         if ((selectedcol < 0 ) || (selectedcol > sheet.getColumnCount()))
//         {
//             alert("选中区域的列不在表格范围内，请检查。")
//             window.event.returnValue = false;
//             return false;
//         }
//
//         var formulaBar = document.getElementById('formulaBar');
//         var formula = formulaBar.innerHTML;
//         if(formula == "" || formula == undefined || formula == null)
//         {
//             sheet.getCells(selectedrow,selectedcol,selectedrow + selectedrowcount - 1,selectedcol + selectedcolcount - 1).formula(formula);
//             // // destactionrangesrow：控件选中区域开始行
//             // // destactionrangescolnum：控件选中区域开始列
//             // // destactionrangeerow：控件选中区域结束行
//             // // destactionrangeecolnum：控件选中区域结束列
//             // var defineformula = {};
//             // defineformula["rows"] = destactionrangesrow;
//             // defineformula["cols"] = destactionrangescolnum;
//             // defineformula["rowe"] = destactionrangeerow;
//             // defineformula["cole"] = destactionrangeecolnum;
//             // defineformula["formula"] = formula;
//             // self.defineformulas.push(defineformula);
//         }
//         event.returnValue=false;
//     }
// }

function rightmenu_formula_guide() {
    alert("请点击按钮fx进行公式定义，不支持右键帮助。");
    event.returnValue=false;
}


