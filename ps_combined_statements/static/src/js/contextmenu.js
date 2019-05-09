/**
 * 右键点击触发
 * @param e
 */
function processSpreadContextMenu(e) {
	let spreadtemp = GcSpread.Sheets.findControl(document.getElementById("ss"));
	let activeSheet = spreadtemp.getActiveSheet();

	let target = getHitTest(e.pageX, e.pageY, activeSheet),
		hitTestType = target.hitTestType,
		row = target.row,
		col = target.col,
		selections = activeSheet.getSelections();

	let isHideContextMenu = false;

	let $contextMenu = $("#spreadContextMenu");
	$contextMenu.data("sheetArea", hitTestType);
	if (isHideContextMenu) {
		hideSpreadContextMenu();
	} else {
		$contextMenu.css({left: e.pageX, top: e.pageY - 53});
		$contextMenu.show();

		$(document).on("click.contextmenu", function() {
			if ($(event.target).parents("#spreadContextMenu").length === 0) {
				hideSpreadContextMenu();
			}
		});
	}
}

/**
 * 右键菜单点击触发
 */
function processContextMenuClicked() {
	let action = $(this).attr('id');
	let spread = GcSpread.Sheets.findControl(document.getElementById("ss"));
	let spreadNS = GcSpread.Sheets,
		sheet = spread.getActiveSheet(),
		viewport = spreadNS.SheetArea.viewport,
		actions = spreadNS.SpreadActions,
		style = spreadNS.StorageType.style,
		data = spreadNS.StorageType.Data,
		sels = sheet.getSelections();

//	let selectedRanges = sheet.getSelections();
//	let Style = GcSpread.Sheets.CopyToOption.Style;
//	var sheetArea = $("#spreadContextMenu").data("sheetArea");

	hideSpreadContextMenu();

	switch(action) {
		case "common_format":
		case "text_format":
			setFormatter(sheet, sels, "@");
			break;
		case "numerical_format":
		case "account_format":
			setFormatter(sheet, sels, "#,##0.00");
			break;
		case "currency_format":
			setFormatter(sheet, sels, "¥#,##0.00");
			break;
		case "date_format":
			setFormatter(sheet, sels, "yyyy-MM-dd");
			break;
		case "alignleft":
			alignleft(sheet, sels);
			break;
		case "aligncenter":
			aligncenter(sheet, sels);
			break;
		case "alignright":
			alignright(sheet, sels);
			break;
		case "aligntop":
			aligntop(sheet, sels);
			break;
		case "alignvetically":
			alignvetically(sheet, sels);
			break;
		case "alignbottom":
			alignbottom(sheet, sels);
			break;
		case "wordwrap":
			wordwrap(sheet, sels);
			break;
		case "noborder":
			noborder(sheet);
			break;
		case "bold":
			bold(sheet, sels);
			break;
		case "italic":
			italic(sheet, sels);
			break;
		case "cut":
			cut(actions, sheet);
			break;
		case "copy":
			copy(actions, sheet);
			break;
		case "paste":
			paste(actions, sheet);
			break;
		case "cleardata":
			cleardata(viewport, sheet, sels, data);
			break;
		case "clearformula":
			clearformula(sheet, sels);
			break;
		case "clearstyle":
			clearstyle(sheet, sels, viewport, style);
			break;
		case "clearall":
			clearall(sheet, sels, viewport, data, style);
			break;
		case "insertrow":
			insertrow(sheet);
			break;
		case "insertcol":
			insertcol(sheet);
			break;
		case "deleterow":
			deleterow(sheet, sels);
			break;
		case "deletecol":
			deletecol(sheet, sheet.getActiveColumnIndex());
			break;
		case "merge":
			merge(sheet, sels);
			break;
		case "unmerge":
			unmerge(sheet, sels);
			break;
		default:
			break;
	}
}

/**
 * 隐藏右键菜单
 */
function hideSpreadContextMenu() {
	$("#spreadContextMenu").hide();
	$(document).off("click.contextmenu");
}

/**
 * 处理页面坐标
 * @param pageX
 * @param pageY
 * @param sheet
 * @returns {*}
 */
function getHitTest(pageX, pageY, sheet) {
	let offset = $("#ss").offset(),
		x = pageX - offset.left,
		y = pageY - offset.top;
	return sheet.hitTest(x, y);
}

/**
 * 页面加载完成绑定事件
 */
$(document).ready(function() {
	$(document).on("contextmenu", function() {
		event.preventDefault();
		return false;
	});
});

/**
 * 设置单元格格式
 * @param sheet
 * @param sels
 * @param farmatterStr
 */
function setFormatter(sheet, sels, farmatterStr) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).formatter(farmatterStr);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 左对齐
 * @param sheet
 * @param sels
 */
function alignleft(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.left);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 右对齐
 * @param sheet
 * @param sels
 */
function alignright(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.right);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 居中对齐
 * @param sheet
 * @param sels
 */
function aligncenter(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).hAlign(GcSpread.Sheets.HorizontalAlign.center);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 顶端对齐
 * @param sheet
 * @param sels
 */
function aligntop(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.Top);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 垂直居中
 * @param sheet
 * @param sels
 */
function alignvetically(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.center).hAlign(GcSpread.Sheets.HorizontalAlign.center);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 底端对齐
 * @param sheet
 * @param sels
 */
function alignbottom(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).vAlign(GcSpread.Sheets.VerticalAlign.bottom);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 无边框
 * @param sheet
 */
function noborder(sheet) {
	// sheet.getActiveRange()
}

/**
 * 粗体
 * @param sheet
 * @param sels
 */
function bold(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).font('bold normal 15px normal');
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 斜体
 * @param sheet
 * @param sels
 */
function italic(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).font('italic normal 15px normal');
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 自动换行
 * @param sheet
 * @param sels
 */
function wordwrap(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let i = sel.row; i < sel.row + sel.rowCount; i++) {
		for (let j = sel.col; j < sel.col + sel.colCount; j++) {
			sheet.getCell(i, j).wordWrap(true);
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 剪切
 * @param SpreadActions
 * @param sheet
 */
function cut(SpreadActions, sheet) {
	SpreadActions.cut.call(sheet);
}

/**
 * 复制
 * @param SpreadActions
 * @param sheet
 */
function copy(SpreadActions, sheet) {
	SpreadActions.copy.call(sheet);
}

/**
 * 粘贴
 * @param SpreadActions
 * @param sheet
 */
function paste(SpreadActions, sheet) {
	SpreadActions.paste.call(sheet);
}

/**
 * 合并单元格
 * @param sheet
 * @param sel
 */
function merge(sheet, sel) {
	if (sel.length > 0) {
		sel = getActualCellRange(sel[sel.length - 1], sheet.getRowCount(), sheet.getColumnCount());
		sheet.addSpan(sel.row, sel.col, sel.rowCount, sel.colCount);
	}
}

/**
 * 取消单元格合并
 * @param sheet
 * @param sel
 */
function unmerge(sheet, sel) {
	if (sel.length > 0) {
		sel = getActualCellRange(sel[sel.length - 1], sheet.getRowCount(), sheet.getColumnCount());
		sheet.isPaintSuspended(true);
		for (let i = 0; i < sel.rowCount; i++) {
			for (let j = 0; j < sel.colCount; j++) {
				sheet.removeSpan(i + sel.row, j + sel.col);
			}
		}
		sheet.isPaintSuspended(false);
	}
}

/**
 * 清除数据
 * @param viewport
 * @param sheet
 * @param sels
 * @param Data
 */
function cleardata(viewport, sheet, sels, Data) {
	let rows = sels[0].row;	//the start row of selected ranges;
	let rowCounts = sels[0].rowCount;	//the number of selected rows;
	let cols = sels[0].col;	//the start column of selected ranges;
	let colCounts = sels[0].colCount;	//the number of selected column;
	sheet.clear(rows, cols, rowCounts, colCounts, viewport, Data);
}

/**
 * 清除公式
 * @param sheet
 * @param sels
 */
function clearformula(sheet, sels) {
	let sel = sels[0];
	sheet.isPaintSuspended(true);
	for (let r = sel.row; r < sel.row + sel.rowCount; r++) {
		for (let c = sel.col; c < sel.col + sel.colCount; c++) {
			sheet.getCell(r, c).formula("");
		}
	}
	sheet.isPaintSuspended(false);
}

/**
 * 清除样式
 * @param sheet
 * @param sels
 * @param viewport
 * @param Style
 */
function clearstyle(sheet, sels, viewport, Style) {
	let rows = sels[0].row;	//the start row of selected ranges;
	let rowCounts = sels[0].rowCount;	//the number of selected rows;
	let cols = sels[0].col;	//the start column of selected ranges;
	let colCounts = sels[0].colCount;	//the number of selected column;
	sheet.clear(rows, cols, rowCounts, colCounts, viewport, Style);
}

/**
 * 清除所有
 * @param sheet
 * @param sels
 * @param viewport
 * @param Data
 * @param Style
 */
function clearall(sheet, sels, viewport, Data, Style) {
	let rows = sels[0].row;	//the start row of selected ranges;
	let rowCounts = sels[0].rowCount;	//the number of selected rows;
	let cols = sels[0].col;	//the start column of selected ranges;
	let colCounts = sels[0].colCount;	//the number of selected column;
	sheet.clear(rows, cols, rowCounts, colCounts, viewport, Data);
	sheet.clear(rows, cols, rowCounts, colCounts, viewport, Style);
}

/**
 * 插入行
 * @param sheet
 */
function insertrow(sheet) {
	sheet.addRows(sheet.getActiveRowIndex(), 1);
}

/**
 * 插入列
 * @param sheet
 */
function insertcol(sheet) {
	sheet.addColumns(sheet.getActiveColumnIndex(), 1);
}

/**
 * 删除行
 * @param sheet
 * @param sels
 */
function deleterow(sheet, sels) {
	if (sels.length > 0) {
		let s = sels[0];
		sheet.deleteRows(s.row, s.rowCount);
	}
}

/**
 * 删除列
 * @param sheet
 * @param colIndex
 */
function deletecol(sheet, colIndex) {
	sheet.deleteColumns(colIndex, 1);
}

function getActualCellRange(cellRange, rowCount, columnCount) {
	if (cellRange.row === -1 && cellRange.col === -1) {
		return new spreadNS.Range(0, 0, rowCount, columnCount);
	}
	else if (cellRange.row === -1) {
		return new spreadNS.Range(0, cellRange.col, rowCount, cellRange.colCount);
	}
	else if (cellRange.col === -1) {
		return new spreadNS.Range(cellRange.row, 0, cellRange.rowCount, columnCount);
	}
	return cellRange;
}