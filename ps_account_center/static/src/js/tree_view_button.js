odoo.define('ps_account_center.tree_view_button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require('web.ListController');
    var FormView = require('web.FormView');
    var FormController = require('web.FormController');
    var BasicRenderer = require('web.BasicRenderer');
    var QWeb = core.qweb;
    var _t = core._t;


    var ImportViewMixin = {
        init: function (viewInfo, params) {
            var importEnabled = 'import_enabled' in params ? params.import_enabled : true;
            this.controllerParams.importEnabled = importEnabled;
        },
    };

    var ImportControllerMixin = {
        init: function (parent, model, renderer, params) {
            this.importEnabled = params.importEnabled;
        },

        _bindImport: function () {
            if (!this.$buttons) {
                return;
            }
            var self = this;

            //批量设置按钮
            this.$buttons.on('click', '.o_list_tender_button_volume_setting', function () {
                var state = self.model.get(self.handle, {raw: true});
                var check_id = [];

                for (var i = 0; i < $('tbody .o_list_record_selector input').length; i++) {
                    if ($('tbody .o_list_record_selector input')[i].checked === true) {
                        // console.log(state.model);
                        console.log(state);
                        check_id.push(state.res_ids[i]);
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;
                // alert(check_id);

                var resmodel = "";
                var resname = "";
                if (state.model == "product.template") {
                    resname = _t('Product Volume Setting');
                    resmodel = 'ps.product.account.bulk.setting.wizard';
                }

                if (state.model == "res.partner") {
                    resname = _t('Customer Volume Setting');
                    resmodel = 'ps.partner.account.bulk.setting.wizard'
                }


                if (state.model == "product.category") {
                    resname = _t('Product Category Accounting Setting');
                    resmodel = 'ps.product.category.account.bulk.setting.wizard';
                }


                if (check_id.length >= 1) {
                    self.do_action
                    ({
                            type: 'ir.actions.act_window',
                            name: resname,
                            res_model: resmodel,
                            views: [[false, 'form']],
                            target: 'new',
                            context: {
                                active_ids: check_id,
                            },
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        });
                }
                else {
                    $(function () {
                        var $div = $("<div>", {id: "dialog-message", title: _t("Tips")});
                        var $p = $("<p>").html(_t("Please select the record you want to open."));
                        $div = $div.append($p);
                        $div.dialog({
                            modal: true,
                            buttons: {
                                确定: function () {
                                    $(this).dialog("close");
                                }
                            }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("confirm")').css({
                            "color": "white",
                            "background-color": "#00a09d",
                            "border-color": "#00a09d"
                        });
                    });
                }
            });
        }
    };

    ListView.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportViewMixin.init.apply(this, arguments);
        },
    });

    BasicRenderer.include({
        _renderNoContentHelper: function () {
            var $msg = $('<div>')
                .addClass('oe_view_nocontent')
                .html(this.noContentHelp);
            this.$el.html($msg);
            if(this.activeActions.create==false){
                var $msg = $('<div>')
                this.$el.html($msg);
            }
        },
    });

    ListController.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin.init.apply(this, arguments);
        },

        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);
            if (this.modelName == "product.template" && !this.renderer.activeActions.create) {
                this.$buttons.find(".o_list_tender_button_volume_setting").css("display", "inline-block");
            }
            if (this.modelName == "res.partner" && !this.renderer.activeActions.create && this.renderer.arch.attrs.name != 'member_usage_statistics') {
                this.$buttons.find(".o_list_tender_button_volume_setting").css("display", "inline-block");
            }
            if (this.modelName == "product.category" && !this.renderer.activeActions.create) {
                this.$buttons.find(".o_list_tender_button_volume_setting").css("display", "inline-block");
            }
            if (this.modelName == "product.template" && this.searchView.action.xml_id.indexOf("action_window_ps_account_center_product_price_maintenance") != -1) {
                this.$buttons.find(".o_list_tender_button_volume_setting").css("display", "none");
            }
        }
    });

    FormView.include({
        init: function (viewInfo) {
            this._super.apply(this, arguments);
            this.controllerParams.viewID = viewInfo.view_id;
            ImportViewMixin.init.apply(this, arguments);
        },
    });

    FormController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.viewID = params.viewID;
            ImportControllerMixin.init.apply(this, arguments);
        },

        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);
        }
    });
});