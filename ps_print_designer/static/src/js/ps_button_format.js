odoo.define('ps_print_format.button', function (require){
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
            this.$buttons.on('click', '.o_button_account_ps_print_format', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 var id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        id.push(state.res_ids[i]);
                    }
                 }
                 check_id.push(id);
                 var ctx = state.context;
                 if(check_id == null||check_id == ''){
                     alert("请选择要打印单据!")
                     return
                 }
                 check_id[check_id.length] = modelName;
                 ctx['active_ids'] = check_id;
                 $.ajax({
                    url: '/print_format',
                    data: JSON.stringify({
                        "params":ctx
                    }),
                    dataType: 'json',
                    type: "POST",
                    async: false,
                    contentType: "application/json",
                    success: function (data) {
                        self.do_action({
                             "name":"选择打印格式",
                             "type":"ir.actions.client",
                             "tag":"test_template",
                             "target":"new",
                             "params":data
                         })
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        alert('加载格式失败！');
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
                this.$buttons.find(".o_button_account_ps_print_format").css("display","inline-block");
            }
        }
    });
}
);