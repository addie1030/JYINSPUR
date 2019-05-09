odoo.define('web.stock.mobile_barcode', function (require) {
"use strict";

var BarcodeMainMenu = require('stock_barcode.MainMenu').MainMenu;
var mobile = require('web_mobile.rpc');

BarcodeMainMenu.include({
    events: _.defaults({
        'click .o_stock_mobile_barcode': 'open_mobile_scanner'
    }, BarcodeMainMenu.prototype.events),
    start: function(){
        if(!mobile.methods.scanBarcode){
            this.$el.find(".o_stock_mobile_barcode").remove();
        }
        return this._super.apply(this, arguments);
        
    },
    open_mobile_scanner: function(){
        var self = this;
        mobile.methods.scanBarcode().then(function(response){
            var barcode = response.data;
            if(barcode){
                self._onBarcodeScanned(barcode);
                mobile.methods.vibrate({'duration': 100});
            }else{
                mobile.methods.showToast({'message':'Please, Scan again !!'});
            }
        });
    }
});


});
