odoo.define('ps_mrp_expenses_pull.button', function (require) {
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var FormController = require('web.FormController');
    var _t = core._t;
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
            // this.init.call(this);
            if (this.modelName == "ps.mrp.in.product.cost.calculation") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_cost_calculation").css("display", "inline-block");
                var self = this;
                //在产品计算
                this.$buttons.on('click', '.o_button_cost_calculation', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("In Product Cost Calculation"),
                            res_model: "ps.mrp.in.product.cost.calculation.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }
            if (this.modelName == "ps.mrp.completed.warehouse.qty") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_complete_warehouse_qty").css("display", "inline-block");
                var self = this;
                //完工入库数量
                this.$buttons.on('click', '.o_button_complete_warehouse_qty', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("Complete Warehouse Quantity"),
                            res_model: "ps.mrp.complete.warehouse.qty.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }
            if (this.modelName == "ps.mrp.expenses.pull.wizard") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
            }
            if (this.modelName == "ps.mrp.cost.allocation") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_cost_allocation").css("display", "inline-block");
                var self = this;
                this.$buttons.on('click', '.o_button_cost_allocation', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("Mrp Cost Allocation"),
                            res_model: "ps.mrp.cost.allocation.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }
            if (this.modelName == "ps.mrp.invest.yield.collection") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_invest_yield_collect").css("display", "inline-block");
                var self = this;
                //费用归集向导视图
                this.$buttons.on('click', '.o_button_invest_yield_collect', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("Invest Yield Collection"),
                            res_model: "ps.mrp.invest.yield.collection.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }
            if (this.modelName == "ps.mrp.expenses.pull") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_expenses_pull").css("display", "inline-block");
                var self = this;
                //费用方案引入向导视图
                this.$buttons.on('click', '.o_button_expenses_pull', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("Expenses Plan Pull"),
                            res_model: "ps.mrp.expenses.pull.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }

            if (this.modelName == "ps.mrp.expense.distribution") {
                this.$buttons.find(".o_list_button_add").css("display", "none");
                this.$buttons.find(".o_button_import").css("display", "none");
                this.$buttons.find(".o_button_expense_distribution").css("display", "inline-block");
                var self = this;
                //费用分配按钮
                this.$buttons.on('click', '.o_button_expense_distribution', function () {
                    self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("Expense Distribution Period"),
                            res_model: "ps.mrp.expense.distribution.wizard",
                            views: [[false, 'form']],
                            target: 'new',
                            view_type: 'form',
                            view_mode: 'form',
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                        {
                            on_reverse_breadcrumb: function () {
                                self.reload();
                            },
                            on_close: function () {
                                self.reload();
                            }
                        }
                    );
                });
            }
        },


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
            // ImportControllerMixin._bindImport.call(this);
            if (this.modelName == "ps.mrp.expenses.pull") {
                this.$buttons.find(".o_form_button_edit").css("display", "none");
                this.$buttons.find(".o_form_button_create").css("display", "none");
            }
            if (this.modelName == "ps.mrp.completed.warehouse.qty") {
                this.$buttons.find(".o_form_button_edit").css("display", "none");
                this.$buttons.find(".o_form_button_create").css("display", "none");
            }
            if (this.modelName == "ps.mrp.invest.yield.collection") {
                this.$buttons.find(".o_form_button_edit").css("display", "none");
                this.$buttons.find(".o_form_button_create").css("display", "none");
            }
        }
    });
});