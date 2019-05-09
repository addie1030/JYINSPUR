odoo.define('ps_point_of_sale.screens', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var screens = require('point_of_sale.screens');
    var PosPaymentScreenWidget = screens.PaymentScreenWidget;
    var rpc = require('web.rpc');
    var PosActionpadWidget = screens.ActionpadWidget;
    var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;


    PosPaymentScreenWidget.include({

        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.keyboard_handler = function(event){
                // On mobile Chrome BarcodeEvents relies on an invisible
                // input being filled by a barcode device. Let events go
                // through when this input is focused.
                if (self.gui.current_popup){
                    return;
                }
                if (BarcodeEvents.$barcodeInput && BarcodeEvents.$barcodeInput.is(":focus")) {
                    return;
                }

                var key = '';

                if (event.type === "keypress") {
                    if (event.keyCode === 13) { // Enter
                        self.validate_order();
                    } else if ( event.keyCode === 190 || // Dot
                                event.keyCode === 110 ||  // Decimal point (numpad)
                                event.keyCode === 188 ||  // Comma
                                event.keyCode === 46 ) {  // Numpad dot
                        key = self.decimal_point;
                    } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                        key = '' + (event.keyCode - 48);
                    } else if (event.keyCode === 45) { // Minus
                        key = '-';
                    } else if (event.keyCode === 43) { // Plus
                        key = '+';
                    }
                } else { // keyup/keydown
                    if (event.keyCode === 46) { // Delete
                        key = 'CLEAR';
                    } else if (event.keyCode === 8) { // Backspace
                        key = 'BACKSPACE';
                    }
                }

                self.payment_input(key);
                event.preventDefault();
            };

        },

        verify_pass_callback: function (force_validation) {
            if (this.order_is_valid(force_validation)) {
                    this.finalize_validation();
             }
        },
        order_is_valid: function(force_validation) {
            var self = this;
            var order = this.pos.get_order();

            // FIXME: this check is there because the backend is unable to
            // process empty orders. This is not the right place to fix it.
            if (order.get_orderlines().length === 0) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Order'),
                    'body':  _t('There must be at least one product in your order before it can be validated'),
                });
                return false;
            }
            // pos订单付款验证时校验是否选择客户
            var customer = order.attributes.client;
            if (customer){
                var ps_member_no = customer['ps_member_no'];
            }
            var require_set_customer = order.pos.config.require_set_customer;
            if (require_set_customer && !customer) {
                this.gui.show_popup('error',{
                    'title': _t('Empty Customer'),
                    'body':  _t('You need to select the customer.'),
                });
                return false;
            }

            //判断是否选择了付款方式
            var aj_id = order.selected_paymentline.cashregister.journal.id;
            if (!aj_id){
                this.gui.show_popup('error',{
                    'title': _t('Empty Journal'),
                    'body':  _t('You need to select the Journal.'),
                });
                return false;
            }

            //判断会员是否有密码
            var passbool = false;
            if (!force_validation) {
                if (ps_member_no) {
                    passbool = rpc.query({
                        args: [ps_member_no],
                        model: 'res.partner',
                        method: 'get_member_pass_boolean',
                    })
                        .then(function (result) {
                            if (result) {
                                return true;
                            }else{
                                self.verify_pass_callback('pass');
                            }
                        });
                }
            }

            if (!force_validation) {
                if (passbool) {
                    if (customer) {
                        if (!force_validation && ps_member_no) {
                            this.gui.show_popup('ps_password', {
                                'title': _t('Password ?'),
                                confirm: function (pw) {
                                    if (pw) {
                                        var res = this._rpc({
                                            model: 'res.partner',
                                            method: 'verify_member_password',
                                            args: [ps_member_no, pw]
                                        }).then(function (result) {
                                            if (result) {
                                                self.verify_pass_callback('pass');
                                            } else {
                                                self.gui.show_popup('error', _t('Incorrect Password'));
                                                return false;
                                            }
                                        });
                                    } else {
                                        self.gui.show_popup('error', _t('Please input a password.'));
                                        return false;
                                    }
                                },
                            });
                            return false;
                        }
                    }
                }
            }

            if (!order.is_paid() || this.invoicing) {
                return false;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(order.get_total_with_tax() - order.get_total_paid()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.gui.show_popup('error',{
                        title: _t('Cannot return change without a cash payment method'),
                        body:  _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return false;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (!force_validation && order.get_total_with_tax() > 0 && (order.get_total_with_tax() * 1000 < order.get_total_paid())) {
                this.gui.show_popup('confirm',{
                    title: _t('Please Confirm Large Amount'),
                    body:  _t('Are you sure that the customer wants to  pay') +
                           ' ' +
                           this.format_currency(order.get_total_paid()) +
                           ' ' +
                           _t('for an order of') +
                           ' ' +
                           this.format_currency(order.get_total_with_tax()) +
                           ' ' +
                           _t('? Clicking "Confirm" will validate the payment.'),
                    confirm: function() {
                        self.validate_order('confirm');
                    },
                });
                return false;
            }

            return true;
        },
    });

    PosActionpadWidget.include({
        events: _.extend({}, PosActionpadWidget.prototype.events, {
            'click .ps-pay': '_onClick'
        }),
        _onClick : function(){
            var self = this;
            console.log(self.gui.current_screen.product_list_widget.product_list)
            var order = self.pos.get_order();
            console.log(order.orderlines);
            var arr = [];
            var product_list = self.gui.current_screen.product_list_widget.product_list
            _.each(order.orderlines.models, function (line) {
                arr.push([line.product.id, line.quantity]);
            });
            console.log(arr)
            var newarr = [];
            for(var i = 0; i < product_list.length; i++){
                var num = 0;
                var id = 0;
                for(var j = 0; j < arr.length; j++){
                    if(arr[j][0] == product_list[i].id){
                        num = arr[j][1] + num;
                        id = arr[j][0];
                    }
                }
                newarr.push([num, id]);
            }
            console.log(newarr)
            console.log(order);
            rpc.query({
                model: 'stock.quant',
                method: 'judging_excess',
                args: [newarr,order.pos.company.id],
            }).then(function(res){
                console.log(res)
                if(res === true){
                    var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                        return line.has_valid_product_lot();
                    });
                    if(!has_valid_product_lot){
                        self.gui.show_popup('confirm',{'title': _t('Empty Serial/Lot Number')
                            ,
                            'body':  _t('One or more product(s) required serial/lot number.'),
                            confirm: function(){
                                self.gui.show_screen('payment');
                            }
                        });
                    }else{
                        self.gui.show_screen('payment');
                    }
                }else{
                    return self.gui.show_popup('error',_t(' Quantity on hand is not enough, please re-enter the quantity.'));
                }
            })

        }
    });
});
