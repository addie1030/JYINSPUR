//右键点击触发
function processSpreadContextMenu(e)
{
    // move the context menu to the position of the mouse point
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var target = getHitTest(e.pageX, e.pageY, activeSheet),
        hitTestType = target.hitTestType,
        row = target.row,
        col = target.col,
        selections = activeSheet.getSelections();

    var isHideContextMenu = false;

    // if (hitTestType === GcSpread.Sheets.SheetArea.colHeader)
    // {
    //     if (getCellInSelections(selections, row, col) === null)
    //     {
    //         activeSheet.setSelection(-1, col, activeSheet.getRowCount(), 1);
    //     }
    //     if (row !== undefined && col !== undefined)
    //     {
    //         $(".context-header").show();
    //         $(".context-cell").hide();
    //     }
    // } else if (hitTestType === GcSpread.Sheets.SheetArea.rowHeader)
    // {
    //     if (getCellInSelections(selections, row, col) === null)
    //     {
    //         activeSheet.setSelection(row, -1, 1, activeSheet.getColumnCount());
    //     }
    //     if (row !== undefined && col !== undefined)
    //     {
    //         $(".context-header").show();
    //         $(".context-cell").hide();
    //     }
    // } else if (hitTestType === GcSpread.Sheets.SheetArea.viewport)
    // {
    //     if (getCellInSelections(selections, row, col) === null)
    //     {
    //         activeSheet.clearSelection();
    //         activeSheet.endEdit();
    //         activeSheet.setActiveCell(row, col);
    //         updateMergeButtonsState();
    //     }
    //     if (row !== undefined && col !== undefined)
    //     {
    //         $(".context-header").hide();
    //         $(".context-cell").hide();
    //         showMergeContextMenu();
    //     } else
    //     {
    //         isHideContextMenu = true;
    //     }
    // } else if (hitTestType === GcSpread.Sheets.SheetArea.corner)
    // {
    //     activeSheet.setSelection(-1, -1, activeSheet.getRowCount(), activeSheet.getColumnCount());
    //     if (row !== undefined && col !== undefined)
    //     {
    //         $(".context-header").hide();
    //         $(".context-cell").show();
    //     }
    // }

    var $contextMenu = $("#spreadContextMenu");
    $contextMenu.data("sheetArea", hitTestType);
    if (isHideContextMenu)
    {
        hideSpreadContextMenu();
    } else
    {
        $contextMenu.css({ left: e.pageX, top: e.pageY });
        $contextMenu.show();

        $(document).on("click.contextmenu", function ()
        {
            if ($(event.target).parents("#spreadContextMenu").length === 0)
            {
                hideSpreadContextMenu();
            }
        });
    }
}
//右键菜单点击触发
function processContextMenuClicked()
{
    var action = $(this).data("action");
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var sheetArea = $("#spreadContextMenu").data("sheetArea");

    hideSpreadContextMenu();

    switch (action)
    {
        // case "cut":
        //     GcSpread.Sheets.SpreadActions.cut.call(activeSheet);
        //     break;
        // case "copy":
        //     GcSpread.Sheets.SpreadActions.copy.call(activeSheet);
        //     break;
        // case "paste":
        //     GcSpread.Sheets.SpreadActions.paste.call(activeSheet);
        //     break;
        // case "cleardata":
        //     var selectedcells = activeSheet.getSelections();
        //     var rows = selectedcells[0].row;	//the start row of selected ranges;
        //     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
        //     // var rows2 = rows + rowCounts - 1;
        //     var cols = selectedcells[0].col;	//the start column of selected ranges;
        //     var colCounts = selectedcells[0].colCount;	//the number of selected column;
        //     // var cols2 = cols + colCounts - 1;
        //     activeSheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Data);
        //     break;
        // case "clearstyle":
        //     var selectedcells = activeSheet.getSelections();
        //     var rows = selectedcells[0].row;	//the start row of selected ranges;
        //     var rowCounts = selectedcells[0].rowCount;	//the number of selected rows;
        //     var cols = selectedcells[0].col;	//the start column of selected ranges;
        //     var colCounts = selectedcells[0].colCount;	//the number of selected column;
        //     activeSheet.clear(rows,cols,rowCounts,colCounts,GcSpread.Sheets.SheetArea.viewport,GcSpread.Sheets.StorageType.Style);
        //     break;
        // case "insertrow":
        //     activeSheet.addRows(activeSheet.getActiveRowIndex(), 1);
        //     break;
        // case "insertcol":
        //     // activeSheet.addColumns(activeSheet.getActiveColumnIndex(), 1);
        //     // insertcol()
        //     break;
        // case "deleterow":
        //     activeSheet.deleteRows(activeSheet.getActiveRowIndex(), 1);
        //     break;
        // case "deletecol":
        //     activeSheet.deleteColumns(activeSheet.getActiveColumnIndex(), 1);
        //     break;
        // case "delete":
        //     if (sheetArea === GcSpread.Sheets.SheetArea.colHeader)
        //     {
        //         activeSheet.deleteColumns(activeSheet.getActiveColumnIndex(), 1);
        //     } else if (sheetArea === GcSpread.Sheets.SheetArea.rowHeader)
        //     {
        //         activeSheet.deleteRows(activeSheet.getActiveRowIndex(), 1);
        //     }
        //     break;
        // case "merge":
        //     var sel = activeSheet.getSelections();
        //     if (sel.length > 0)
        //     {
        //         sel = sel[sel.length - 1];
        //         activeSheet.addSpan(sel.row, sel.col, sel.rowCount, sel.colCount, GcSpread.Sheets.SheetArea.viewport);
        //     }
        //     updateMergeButtonsState();
        //     break;
        // case "unmerge":
        //     var sels = activeSheet.getSelections();
        //     for (var i = 0; i < sels.length; i++)
        //     {
        //         var sel = getActualCellRange(sels[i], activeSheet.getRowCount(), activeSheet.getColumnCount());
        //         for (var r = 0; r < sel.rowCount; r++)
        //         {
        //             for (var c = 0; c < sel.colCount; c++)
        //             {
        //                 var span = activeSheet.getSpan(r + sel.row, c + sel.col, GcSpread.Sheets.SheetArea.viewport);
        //                 if (span)
        //                 {
        //                     activeSheet.removeSpan(span.row, span.col, GcSpread.Sheets.SheetArea.viewport);
        //                 }
        //             }
        //         }
        //     }
        //     updateMergeButtonsState();
        //     break;
        // default:
        //     break;
    }
}

function hideSpreadContextMenu()
{
    $("#spreadContextMenu").hide();
    $(document).off("click.contextmenu");
}

function updateMergeButtonsState()
{
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    var sels = activeSheet.getSelections(),
        mergable = false,
        unmergable = false;

    sels.forEach(function (range)
    {
        var ranges = activeSheet.getSpans(range),
            spanCount = ranges.length;

        if (!mergable)
        {
            if (spanCount > 1 || (spanCount === 0 && (range.rowCount > 1 || range.colCount > 1)))
            {
                mergable = true;
            } else if (spanCount === 1)
            {
                var range2 = ranges[0];
                if (range2.row !== range.row || range2.col !== range.col ||
                    range2.rowCount !== range2.rowCount || range2.colCount !== range.colCount)
                {
                    mergable = true;
                }
            }
        }
        if (!unmergable)
        {
            unmergable = spanCount > 0;
        }
    });

    $("#mergeCells").attr("disabled", mergable ? null : "disabled");
    $("#unmergeCells").attr("disabled", unmergable ? null : "disabled");
}

function getHitTest(pageX, pageY, sheet)
{
    var offset = $("#statements_sheet").offset(),
            x = pageX - offset.left,
            y = pageY - offset.top;
    var spreadtemp = GcSpread.Sheets.findControl(document.getElementById("statements_sheet"));
    var activeSheet = spreadtemp.getActiveSheet();
    return activeSheet.hitTest(x, y);
}

function getCellInSelections(selections, row, col)
{
    var count = selections.length, range;
    for (var i = 0; i < count; i++)
    {
        range = selections[i];
        if (range.contains(row, col))
        {
            return range;
        }
    }
    return null;
}

function getActualCellRange(cellRange, rowCount, columnCount)
{
    if (cellRange.row === -1 && cellRange.col === -1)
    {
        return new spreadNS.Range(0, 0, rowCount, columnCount);
    }
    else if (cellRange.row === -1)
    {
        return new spreadNS.Range(0, cellRange.col, rowCount, cellRange.colCount);
    }
    else if (cellRange.col === -1)
    {
        return new spreadNS.Range(cellRange.row, 0, cellRange.rowCount, columnCount);
    }

    return cellRange;
}

function showMergeContextMenu()
{
    // use the result of updateMergeButtonsState
    if ($("#mergeCells").attr("disabled"))
    {
        $(".context-merge").hide();
    } else
    {
        $(".context-cell.divider").show();
        $(".context-merge").show();
    }

    if ($("#unmergeCells").attr("disabled"))
    {
        $(".context-unmerge").hide();
    } else
    {
        $(".context-cell.divider").show();
        $(".context-unmerge").show();
    }
}

$(document).ready(function ()
{
    $("#statements_sheet").bind("contextmenu", processSpreadContextMenu);

    $("#spreadContextMenu a").click(processContextMenuClicked);// a 对应 a标签

    $(document).on("contextmenu", function ()
    {
        // event.stopPropagation();
        event.preventDefault();
        // window.event.returnValue = false;
        return false;
    });
});


//firefox----这段js重新封装了event对象，经验证可以在火狐下支持
function __firefox(){
    HTMLElement.prototype.__defineGetter__("runtimeStyle", __element_style);
    window.constructor.prototype.__defineGetter__("event", __window_event);
    Event.prototype.__defineGetter__("srcElement", __event_srcElement);
}

function __element_style(){
    return this.style;
}

function __window_event(){
    return __window_event_constructor();
}

function __event_srcElement(){
    return this.target;
}

function __window_event_constructor(){
    if(document.all){
    return window.event;
}

var _caller = __window_event_constructor.caller;
    while(_caller!=null){
        var _argument = _caller.arguments[0];
        if(_argument){
            var _temp = _argument.constructor;
            if(_temp.toString().indexOf("Event")!=-1){
                return _argument;
            }
        }
    _caller = _caller.caller;
    }
    return null;
}

if(window.addEventListener){
    __firefox();
}