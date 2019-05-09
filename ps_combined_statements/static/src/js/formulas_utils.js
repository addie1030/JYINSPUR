odoo.define('combined_statements.utils', function(require) {
"use strict";

	/**
	 * 获取单元格值
	 * @param sheet Spread工作簿
	 * @param coordinate 单元格坐标
	 * @returns {value}
	 */
	function getCellValueWithSheet(sheet, coordinate) {
		let column_index = stringTonum(coordinate.match(/^[a-z|A-Z]+/gi)[0]);
		let row_index = parseInt(coordinate.match(/\d+$/gi)[0]);
		return sheet.getValue(row_index - 1, column_index - 1);
	}

	/**
	 * 获取单元格值
	 * @param spread
	 * @param sheetName 工作簿名称
	 * @param coordinate 单元格坐标
	 * @returns {*}
	 */
	function getCellValueWithSpread(spread, sheetName, coordinate) {
		let sheet = spread.getSheetFromName(sheetName);
		return getCellValueWithSheet(sheet, coordinate);
	}

	/**
	 * 转换数字为Excel列代号
	 * @param number 数字
	 * @returns {string}
	 */
	function numToString(number) {
		let stringArray = [];
		let numToStringAction = function(nnum) {
			let num = nnum - 1;
			let a = parseInt(num/26);
			let b = num%26;
			stringArray.push(String.fromCharCode(64 + parseInt(b + 1)));
			if (a > 0) {
				numToStringAction(a);
			}
		};
		numToStringAction(number);
		return stringArray.reverse().join("");
	}

	/**
	 * 将字母转换为Excel列对应数字
	 * @param column
	 * @returns {number}
	 */
	function stringTonum(column) {
		let str = column.toLowerCase().split("");
		let al = str.length;
		let getCharNumber = function(charx) {
			return charx.charCodeAt() - 96;
		};
		let numout = 0;
		let charnum = 0;
		for (let i = 0; i < al; i++) {
			charnum = getCharNumber(str[i]);
			numout += charnum*Math.pow(26, al - i - 1);
		}
		return numout;
	}

	/**
	 * 校验是否是数字（包含正负整数，0以及正负浮点数
	 * @param val
	 * @returns {boolean}
	 */
	function isNumber(val) {
		let regPos = /^\d+(\.\d+)?$/; //非负浮点数
		let regNeg = /^(-(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*)))$/; //负浮点数
		return !!(regPos.test(val) || regNeg.test(val));
	}

	return {
		getCellValueWithSheet: getCellValueWithSheet,
		getCellValueWithSpread: getCellValueWithSpread,
		stringTonum: stringTonum,
		numToString: numToString,
		isNumber: isNumber
	};

});