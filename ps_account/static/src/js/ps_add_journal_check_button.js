odoo.define('account_china.button', function (require){
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var _t = core._t;
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
            this.$buttons.on('click', '.o_button_aaa', function () {
                $.ajax({
                        url: '/print',
                        data: JSON.stringify({ // 转换成JSON
                            "params":''
                        }),
                        dataType: 'json',
                        type: "POST",
                        async: false,
                        contentType: "application/json",
                        success: function (data) {
                            alert(_t("Successfully saved!"));
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            alert(_t('Save failed!'));
                        }
                    });
                // var state = self.model.get(self.handle, {raw: true});
                // self.do_action({
                //     type: 'ir.actions.client',
                //     tag: 'import',
                //     params: {
                //         model: self.modelName,
                //         context: state.getContext(),
                //     }
                // }, {
                //     on_reverse_breadcrumb: self.reload.bind(self),
                // });
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
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);
            // this.init.call(this);
            if(this.modelName!=="ps.account.move.check"){
                this.$buttons.find(".o_button_aaa").css("display","none");
            }
            if(this.modelName=="ps.account.move.check"){
                this.$buttons.find(".o_list_button_add").css("display","none");
                this.$buttons.find(".o_button_import").css("display","none");
            }
        }
    });
});