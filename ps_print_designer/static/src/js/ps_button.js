odoo.define('ps_print.button', function (require){
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var QWeb = core.qweb;


    var ImportViewMixin = {
        /**
         * @override
         */
        init: function (viewInfo, params) {
            var importEnabled = 'import_enabled' in params ? params.import_enabled : true;
            // if true, the 'Import' button will be visible
            this.controllerParams.importEnabled = importEnabled;
        },
    };
    var ImportControllerMixin = {
        /**
         * @override
         */
        init: function (parent, model, renderer, params) {
            this.importEnabled = params.importEnabled;
        },
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        /**
         * Adds an event listener on the import button.
         *
         * @private
         */
        _bindImport: function () {
            if (!this.$buttons) {
                return;
            }
            var self = this;
            var modelName = self.modelName;
            this.$buttons.on('click', '.o_button_account_ps_print', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        check_id.push(state.res_ids[i]);
                    }
                 }
                 var ctx = state.context;
                 check_id[check_id.length] = modelName;
                 ctx['active_ids'] = check_id;
                 $.ajax({
                    url: '/print_account_data',
                    data: JSON.stringify({ // 转换成JSON
                        "params":ctx
                    }),
                    dataType: 'json',
                    type: "POST",
                    async: false,
                    contentType: "application/json",
                    success: function (data) {
                        var report = data['result']['report']
                        var fields_data = data['result']['data'];
                        console.log(report);
                        console.log(fields_data);
                        $.ajax({
                            // url: 'https://www.reportbro.com/report/run',
                            url: 'http://localhost:8888/reportbro/report/run',
                            data: JSON.stringify({
                                report: JSON.parse(report),
                                outputFormat: 'pdf',
                                data: fields_data,
                                isTestData: false
                            }),
                            type: "PUT",
                            async: false,
                            contentType: "application/json",
                            success: function (data) {
                                self.reportKey = data.substr(4);
                                // window.open('https://www.reportbro.com/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                                window.open('http://localhost:8888/reportbro/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                            },
                            error: function (jqXHR, textStatus, errorThrown) {
                                alert('服务器响应失败！');
                            }
                        });
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        alert('请求异常！');
                    }
                 });
            });
        }
    };
    ListView.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportViewMixin.init.apply(this, arguments);
        },
    });
    ListController.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin.init.apply(this, arguments);
        },
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin._bindImport.call(this);
            console.log(this.modelName)
            // if(this.modelName!=="print.design.define"){
            //     this.$buttons.find(".o_button_ps_print").css("display","none");
            // }
            if(this.modelName=="account.move"){
                this.$buttons.find(".o_button_account_ps_print").css("display","inline-block");
            }
        }
    });
}
);