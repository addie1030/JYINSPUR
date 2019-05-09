odoo.define('stock_center.tree_view_button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require('web.ListController');
    var FormView = require('web.FormView');
    var FormController = require('web.FormController');
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

            //库存生成凭证按钮
            this.$buttons.on('click', '.o_form_button_stock_create_move', function () {
                var state = self.model.get(self.handle, {raw: true});
                var ctx = state.context;
                var check_id = [];
                var is_merge = '0';
                // var movedate = "";
                if ($('tbody tr input[type="checkbox"]')[0].checked) {
                    var movedate = $('tbody tr input[name="date"]').val();
                    is_merge = '1';
                } else {
                    is_merge = '0';
                }
                for (var i = 0; i < $('tbody tr input[name="check"]').length; i++) {
                    if ($('tbody tr input[name="check"]')[i].checked) {
                        check_id.push($('tbody tr input[name="check"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML)
                    }
                }

                ctx['stock_active_ids'] = check_id;
                ctx['stock_is_merge'] = is_merge;
                ctx['stock_move_date'] = $('tbody tr input[name="date"]').val();

                if (check_id.length > 0 && String(check_id[0]) != 'undefined') {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t('Create Move'),
                            res_model: "ps.stock.create.account.move",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            context: ctx,
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        }
                        ,
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                } else {
                    $(function () {
                        var $div = $("<div>", {id: "dialog-message", title: _t("Prompt")});
                        var $p = $("<p>").html(_t("Please select records to create moves."));//请选择要生成凭证的记录
                        $div = $div.append($p);
                        $div.dialog({
                            modal: true,
                            buttons: {
                                确定: function () {
                                    $(this).dialog("close");
                                }
                            }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({
                            "color": "white",
                            "background-color": "#00a09d",
                            "border-color": "#00a09d"
                        });

                    });
                }
            });

            //取消生成凭证按钮
            this.$buttons.on('click', '.o_list_tender_button_cancel_move', function () {
                var state = self.model.get(self.handle, {raw: true});
                var check_id = [];

                for (var i = 0; i < $('tbody .o_list_record_selector input').length; i++) {
                    if ($('tbody .o_list_record_selector input')[i].checked === true) {
                        check_id.push(state.res_ids[i]);
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;
                // alert(check_id);
                var resmodel = "";
                var resname = "";
                if (state.model == "ps.stock.account.china.center.cancel.move") {
                    resname = _t('Cancel Selected Item(s)');
                    resmodel = 'ps.cancel.move';
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
                        var $div = $("<div>", {id: "dialog-message", title: _t("Prompt")});
                        var $p = $("<p>").html(_t("Please select a record to cancel."));
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

            //自动核销按钮
            this.$buttons.on('click', '.o_form_button_purchase_stock_verification_auto', function () {
                var state = self.model.get(self.handle, {raw: true});
                var ctx = state.context;
                var invoice_check_id = [];
                var stock_move_check_id = [];
                //取采购发票选中记录ID
                for (var i = 0; i < $('tbody tr input[name="check"]').length; i++) {
                    if ($('tbody tr input[name="check"]')[i].checked) {
                        invoice_check_id.push($('tbody tr input[name="check"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML)
                    }
                }
                //取库存单据选中记录ID
                for (var i = 0; i < $('tbody tr input[name="stockcheck"]').length; i++) {
                    if ($('tbody tr input[name="stockcheck"]')[i].checked) {
                        stock_move_check_id.push($('tbody tr input[name="stockcheck"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML)
                    }
                }

                ctx['invoice_active_ids'] = invoice_check_id;
                ctx['validate_type'] = 'auto';
                ctx['stock_move_active_ids'] = stock_move_check_id;
                ctx['stock_move_type'] = $('tbody td select[name="stock_move_type"]').val();

                if (invoice_check_id.length > 0 && stock_move_check_id.length > 0) {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t('Invoice Stock Move Validate'),
                            res_model: "ps.invoice.stock.move.validate",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            context: ctx,
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        }
                        ,
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                } else {
                    $(function () {
                        var $div = $("<div>", {id: "dialog-message", title: _t("Prompt")});
                        var $p = $("<p>").html(_t("Please select invoice records and stock records."));//请选择要核销的发票和入库单记录
                        $div = $div.append($p);
                        $div.dialog({
                            modal: true,
                            buttons: {
                                确定: function () {
                                    $(this).dialog("close");
                                }
                            }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({
                            "color": "white",
                            "background-color": "#00a09d",
                            "border-color": "#00a09d"
                        });

                    });

                }
            });

            //手工核销按钮
            this.$buttons.on('click', '.o_form_button_purchase_stock_verification_manual', function () {
                var state = self.model.get(self.handle, {raw: true});
                var ctx = state.context;
                var invoice_check_id = [];
                var stock_move_check_id = [];
                var dic_stock_moves = {};
                var key = 0;
                var value = 0;
                var key_sp = 0;
                var value_sp = 0;
                //取采购发票选中记录ID
                for (var i = 0; i < $('tbody tr input[name="check"]').length; i++) {
                    if ($('tbody tr input[name="check"]')[i].checked) {
                        invoice_check_id.push($('tbody tr input[name="check"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML);
                    }
                }

                //取库存单据选中记录ID
                    //*******  处理失去输入完直接点按钮，不能获得输入值问题  *********
                    if ($('tbody tr span[name="ps_stock_move_id"]')[0] != undefined){
                        key_sp = $('tbody tr span[name="ps_stock_move_id"]')[0].innerHTML;
                        value_sp = $('tbody tr input[name="ps_the_cancelled_quantity"]')[0].value;
                    }
                    //*******  处理失去输入完直接点按钮，不能获得输入值问题  **********

                for (var i = 0; i < $('tbody tr input[name="stockcheck"]').length; i++) {
                    if ($('tbody tr input[name="stockcheck"]')[i].checked) {
                        stock_move_check_id.push($('tbody tr input[name="stockcheck"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML);
                        key = $('tbody tr input[name="stockcheck"]')[i].parentNode.parentNode.lastChild.firstChild.innerHTML;
                        value = $('tbody tr input[name="stockcheck"]')[i].parentNode.parentNode.lastChild.previousSibling.firstChild.innerHTML;

                        if(key != null && key != ""){
                            dic_stock_moves[key.toString()] = parseInt(value);
                        }

                    }
                }

                //********  添加因失去焦点未获得到的数据 *********
                if(key_sp != null && key_sp != ""){
                    dic_stock_moves[key_sp.toString()] = parseInt(value_sp);
                }

                ctx['invoice_active_ids'] = invoice_check_id;
                ctx['validate_type'] = 'manual';
                ctx['dic_stock_moves'] = dic_stock_moves;
                ctx['stock_move_type'] = $('tbody td select[name="stock_move_type"]').val();

                if (invoice_check_id.length > 0 && Object.keys(dic_stock_moves).length > 0 && stock_move_check_id.length > 0) {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t('Invoice Stock Move Validate'),
                            res_model: "ps.invoice.stock.move.validate",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            context: ctx,
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        }
                        ,
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                } else {
                    $(function () {
                        var $div = $("<div>", {id: "dialog-message", title: _t("Prompt")});
                        var $p = $("<p>").html(_t("Please select invoice records and stock records."));
                        $div = $div.append($p);
                        $div.dialog({
                            modal: true,
                            buttons: {
                                确定: function () {
                                    $(this).dialog("close");
                                }
                            }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({
                            "color": "white",
                            "background-color": "#00a09d",
                            "border-color": "#00a09d"
                        });
                    });
                }
            });


            //入库单据价格维护
            this.$buttons.on('click', '.o_list_tender_button_cost_maintenance', function () {
                var state = self.model.get(self.handle, {raw: true});
                var check_id = [];

                for (var i = 0; i < $('tbody .o_list_record_selector input').length; i++) {
                    if ($('tbody .o_list_record_selector input')[i].checked === true) {
                        check_id.push(state.res_ids[i]);
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;
                var resmodel = "ps.maintenance.cost";
                var resname = _t('Import From The Price Maintenance Table');
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
                        var $div = $("<div>", {id: "dialog-message", title: _t("Prompt")});
                        var $p = $("<p>").html(_t("Please select at least one record first"));
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

        },
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

        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);

            if (this.modelName == "ps.stock.account.china.center.cancel.move" && this.searchView.action.xml_id.indexOf("ps_stock_account") != -1) {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_list_tender_button_cancel_move").css("display", "inline-block");
            }
            if (this.modelName == "product.template" && this.searchView.action.xml_id.indexOf("action_window_account_china_center_product_price_maintenance") != -1) {
                this.$buttons.find(".o_list_tender_button_volume_setting").css("display", "none");
            }

            if (this.modelName == "stock.move"
                && this.searchView.action.xml_id.indexOf("action_window_stock_cost_maintenance_action") != -1) {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_list_tender_button_cost_maintenance").css("display", "inline-block");
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
            if (this.modelName == "ps.stock.picking.create.move") {
                this.$buttons.find(".o_form_button_save").css("display", "none");
                this.$buttons.find(".o_form_button_cancel").css("display", "none");
                this.$buttons.find(".o_form_button_stock_refresh_data").css("display", "inline-block");
                this.$buttons.find(".o_form_button_stock_create_move").css("display", "inline-block");
            }

            if (this.modelName == "ps.purchase.stock.verification") {
                this.$buttons.find(".o_form_button_save").css("display", "none");
                this.$buttons.find(".o_form_button_cancel").css("display", "none");
                this.$buttons.find(".o_form_button_purchase_stock_verification_auto").css("display", "inline-block");
                this.$buttons.find(".o_form_button_purchase_stock_verification_manual").css("display", "inline-block");
            }
        }
    });
});