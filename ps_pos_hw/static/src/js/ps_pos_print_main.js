odoo.define('ps_pos_hw.devices', function (require) {
    "use strict";
    var devices = require('point_of_sale.devices');
    var screens = require('point_of_sale.screens');
    var electron = nodeRequire('electron');
    var remote = electron.remote;
    var printer_model = remote.require('printer');
    var iconv = remote.require('iconv-lite');
    var escpos = remote.require('node-escpos');
    var cmds = escpos.cmds;
    var PosPaymentScreenWidget = screens.PaymentScreenWidget;

    PosPaymentScreenWidget.include({
        validate_order: function(force_validation) {
        if (this.order_is_valid(force_validation)) {
            this.finalize_validation();
            var order = this.pos.get_order();
            var receipt = {
                widget: this,
                pos: this.pos,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            };
            this.pos.proxy.print_receipt(receipt);
        }
    },

    });

    devices.ProxyDevice  = devices.ProxyDevice.extend({
        print_receipt: function(receipt) {
            var data = [];
            data.push(new Buffer([0x1b, 0x40]));
            data.push(iconv.encode('公司：           ' + receipt.order.pos.company.name + '\r\n', 'cp936'));
            data.push(iconv.encode('电话：           ' + receipt.order.pos.company.phone + '\r\n', 'cp936'));
            data.push(iconv.encode('客户：           ' + receipt.order.attributes.client.name + '\r\n', 'cp936'));
            data.push(iconv.encode('用户：           ' + receipt.order.pos.proxy.pos.user.name + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            var min = receipt.orderlines[0].product.display_name;
            for (var orderline in receipt.orderlines){
                var order = receipt.orderlines[orderline];
                if (order.product.display_name.length < min.length){
                    min = order.product.display_name;
                };
            };
            for (var orderline in receipt.orderlines){
                var order = receipt.orderlines[orderline];
                var space = ' ';
                var len = 14 - order.product.display_name.length;
                len -= order.product.display_name.length - min.length;
                for (var i=1; i<=len; i++){
                    space += ' ';
                };
                data.push(iconv.encode(order.product.display_name + space + order.quantityStr, 'cp936'));
                data.push(iconv.encode('\r\n', 'cp936'));
                data.push(iconv.encode(order.price.toFixed(2), 'cp936'));
                if (order.price.toFixed(2) != order.product.list_price.toFixed(2)){
                    data.push(iconv.encode("    " + "优惠:" + "       " + (order.product.list_price - order.price).toFixed(2) + '\r\n', 'cp936'));
                }else {
                    data.push(iconv.encode('\r\n', 'cp936'));
                };

            };
            data.push(new Buffer([0x0a]));
            data.push(iconv.encode('小计：                ' + receipt.receipt.should_pay.toFixed(2) + '\r\n', 'cp936'));
            data.push(iconv.encode('优惠总计：             ' + receipt.receipt.total_offer.toFixed(2) + '\r\n', 'cp936'));
            for (var tax_index in receipt.receipt.tax_details){
                var tax = receipt.receipt.tax_details[tax_index];
                data.push(iconv.encode(tax.name + '：     ' + tax.amount.toFixed(2) + '\r\n', 'cp936'));
            };
            data.push(iconv.encode('总计：                ' + receipt.receipt.total_with_tax.toFixed(2) + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            data.push(iconv.encode('现金：                ' + receipt.paymentlines[0].amount.toFixed(2)  + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            data.push(iconv.encode('找零：                ' + receipt.receipt.change.toFixed(2) + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            data.push(iconv.encode('订单号：      ' + receipt.order.name + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            data.push(iconv.encode('时间：' + receipt.order.formatted_validation_date + '\r\n', 'cp936'));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x0a]));
            data.push(new Buffer([0x1d, 0x56, 0x00]));
            data.push(new Buffer([0x10, 0x14, 0x01, 0x00, 0x05]));
            printer_model.printDirect({
                data: Buffer.concat(data),
                type: 'RAW',
                success: function (jobID) {
                },
                error: function (err) {
                }
            });

        },
        print_sale_details: function() {
        },
    });

    screens.ReceiptScreenWidget  = screens.ReceiptScreenWidget.include({
        print: function() {
            var self = this;
            var receipt =  self.get_receipt_render_env();
            self.pos.proxy.print_receipt(receipt);
        },
    });
});

