odoo.define('account.dashboard_setup_bar', function (require) {
    "use strict";

    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var KanbanView = require('web.KanbanView');
    var KanbanModel = require('web.KanbanModel');
    var KanbanRenderer = require('web.KanbanRenderer');
    var KanbanController = require('web.KanbanController');
    var session = require('web.session');
    var view_registry = require('web.view_registry');
    var ControlPanel = require('web.ControlPanel');
    var rpc = require('web.rpc');

    var QWeb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var COMPANY_METHOD_TYPE = "company_object";

    ControlPanel.include({
        update: function(status, options) {
            var self = this;
            self._super(status, options);
            //仪表盘增加显示当前会计期间
            if(self.searchview && self.searchview.action.xml_id == "account.open_account_journal_dashboard_kanban"){
                self._rpc({
                    model: 'ps.account.period',
                    method: 'get_all_period1',
                }).then(function(result){
                    if(result.length>0){
                        for(var i=0;i<result.length;i++){
                            if(result[i].state==1){
                                var year = result[i].year;
                                for(var j=0;j<result[i].month.length;j++){
                                    if(result[i].month[j].state==1){
                                        var month = result[i].month[j].displayname;
                                        month = month.slice(0,2);
                                    }
                                }
                            }
                        }
                        var $span = $("<span>").html(_t("Current accounting period:")+year+_t("year")+month+_t("period"));
                    }else{
                        var $span = $("<span>").html(_t("Accounting period not set"));
                    }
                    $span.css({"font-size":"14px","color":"#8f8f8f","display":"block","padding-top":"5px"});
                    $(".breadcrumb").css("display","block");
                    $(".breadcrumb").children("span").remove();
                    $(".breadcrumb").append($span);
                })
            }
        },
    }) ;

    var AccountSetupBarRenderer;
    AccountSetupBarRenderer = KanbanRenderer.extend({
        events: _.extend({}, KanbanRenderer.prototype.events, {
            'click .account_setup_dashboard_action': 'onActionClicked',
            'click .seepz': 'onSeepzClicked',
            'click .addpz': 'onAddpzClicked',
            'click .trialbalance':'onTrialbalanceClicked',
            'click .balancesheet':'onBalancesheetClicked',
            'click .incomestatement':'onIncomestatementClicked',
            'click .detailbalance':'onDetailBalanceClicked',
        }),

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Notifies the controller that the target has changed.
         *
         * @private
         * @param {string} target_name the name of the changed target
         * @param {string} value the new value
         */
        _notifyTargetChange: function (target_name, value) {
            this.trigger_up('dashboard_edit_target', {
                target_name: target_name,
                target_value: value,
            });
        },
        /**
         * @override
         * @private
         * @returns {Deferred}
         */
        _render: function () {
            var self = this;
            // this._rpc({
            //         model: 'account.move',
            //         method: 'get_year_profit',
            //     })
            //     .then(function(result) {
            //         var month = new Array()
            //         var amount = new Array()
            //         for(var i=0;i<result.length;i++){
            //             month[i] = result[i].month;
            //             amount[i] = result[i].amount;
            //         }
            //         $("#mouth").val(month);
            //         $("#amount").val(amount);
            //         });

            return this._super.apply(this, arguments).then(function () {
                var values = self.state.dashboardValues;
                var account_dashboard = QWeb.render('account.AccountDashboardSetupBar', {
                    widget: self,
                    values: values,
                });
                self.$el.prepend(account_dashboard);
            });
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {MouseEvent}
         */
        onActionClicked: function (e) {
            e.preventDefault();
            var self = this;
            var $action = $(e.currentTarget);
            var name_attr = $action.attr('name');
            var type_attr = $action.attr('type');
            var action_context = $action.data('context');

            if (type_attr == COMPANY_METHOD_TYPE) {
                self.trigger_up('company_button_action', {rpc_method: name_attr, context: action_context})
            }
        },
        onSeepzClicked: function (e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: "account.move",
                method: "get_pz_view_id",
            }).then(function(result){
                var view_id=result[0];
                var search_view_id=result[1][0];
                var form_view_id=result[2];
                var name=_t('Journal Entries');
                self.do_action({
                    'type': 'ir.actions.act_window',
                    'name': name,
                    'res_model': 'account.move',
                    'target': 'current',
                    'view_type': 'form',
                    'view_mode' : 'tree,kanban,form',
                    'views': [[view_id || false, 'list'],[form_view_id || false, 'form']],
                    'search_view_id': [search_view_id],
                    'context': {'search_default_misc_filter':1, 'view_no_maturity': 1, 'manual_move':'1'}
                });
            })
        },
        onAddpzClicked: function (e) {
            e.preventDefault();
            var self = this;
            self.do_action({
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'target': 'current',
                'views': [[false, 'form']],
                'context': {
                    'search_default_misc_filter':1,
                    'view_no_maturity': 1,
                    'manual_move':'1'
                }
            });
        },
        onTrialbalanceClicked: function (e) {
            // 科目余额账
            e.preventDefault();
            var self = this;
            self.do_action({
                'name': _t('Account balance account'),
                'type': 'ir.actions.client',
                'tag': 'account_china_report',
                'context': {'model': 'account.china.balance.report'},
            });
        },
        onDetailBalanceClicked: function (e) {
            // 科目明细账
            e.preventDefault();
            var self = this;
           self.do_action({
                'name': _t('Detail account'),
                'type': 'ir.actions.client',
                'tag': 'account_china_report',
                'context': {'model': 'account.china.tri.ledger.report'},
            });
        },
        onBalancesheetClicked: function (e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'ps.statement.statements',
                method: 'get_fiscalperiod'
            }).then(function (result){
                if (result){
                    self._rpc({
                        model: 'ps.statement.statements',
                        method: 'getdata',
                        args: ['0001',result],
                    }).then(function(res){
                        console.log(res)
                         self.do_action({
                            'name': _t('Balance sheet'),
                            'type': 'ir.actions.client',
                            'tag': 'statements',
                            'context' : {'report_code' : res.report_code,'isnew' : 0,'report_name' : '资产负债表','report_date':res.report_date,'category':res.category,'titlerows':res.title_rows,'headrows':res.head_rows,'bodyrows':res.body_rows,'tailrows':res.tail_rows,'bodycols':res.total_cols},
                        });
                    })
                }else{
                    alert(_t('If you do not find the corresponding accounting period, please first maintain the accounting period in financial accounting!'));
                    return;
                }
            })
        },
        onIncomestatementClicked: function (e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'ps.statement.statements',
                method: 'get_fiscalperiod'
            }).then(function (result){
                if (result){
                    self._rpc({
                        model: 'ps.statement.statements',
                        method: 'getdata',
                        args: ['0002',result],
                    }).then(function(res){
                        console.log(res)
                         self.do_action({
                            'name': _t('Income statement'),
                            'type': 'ir.actions.client',
                            'tag': 'statements',
                            'context' : {'report_code' : res.report_code,'isnew' : 0,'report_name' : '利润表','report_date':res.report_date,'category':res.category,'titlerows':res.title_rows,'headrows':res.head_rows,'bodyrows':res.body_rows,'tailrows':res.tail_rows,'bodycols':res.total_cols},
                        });
                    })
                }else{
                    alert(_t('If you do not find the corresponding accounting period, please first maintain the accounting period in financial accounting!'));
                    return;
                }
            })
        },


    });

    var AccountSetupBarModel = KanbanModel.extend({
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        /**
         * @override
         */
        init: function () {
            this.dashboardValues = {};
            this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        get: function (localID) {
            var result = this._super.apply(this, arguments);
            if (this.dashboardValues[localID]) {
                result.dashboardValues = this.dashboardValues[localID];
            }
            return result;
        },


        /**
         * @œverride
         * @returns {Deferred}
         */
        load: function () {
            return this._loadDashboard(this._super.apply(this, arguments));
        },
        /**
         * @œverride
         * @returns {Deferred}
         */
        reload: function () {
            return this._loadDashboard(this._super.apply(this, arguments));
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------


        /**
         * @private
         * @param {Deferred} super_def a deferred that resolves with a dataPoint id
         * @returns {Deferred<string>} resolves to the dataPoint id
         */
        _loadDashboard: function (super_def) {
            var self = this;

            return $.when(super_def).then(function (id, dashboardValues) {
                self.dashboardValues[id] = dashboardValues;
                return id;
            });
        },
    });

    var AccountSetupBarController = KanbanController.extend({
        /* The company_button_action action allows the buttons of the setup bar to
        * trigger Python code defined in api.model functions in res.company model,
        * and to execute the action returned them.
        * It uses the 'type' attributes on buttons : if 'company_object', it will
        * run Python function 'name' of company model.
        */
        custom_events: _.extend({}, KanbanController.prototype.custom_events, {
            dashboard_open_action: '_onDashboardOpenAction',
            company_button_action: '_triggerCompanyButtonAction',
        }),

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         * @param {OdooEvent} e
         */
        _onDashboardOpenAction: function (e) {
            var action_name = e.data.action_name;
            var action_context = e.data.action_context;
            return this.do_action(action_name, {
                additional_context: action_context,
            });
        },

        /**
         * Manages the clicks on the setup bar buttons.
         **/
        _triggerCompanyButtonAction: function (odooEvent) {
            var self = this
            if (odooEvent.data.rpc_method !== undefined) {
                self._rpc({
                    model: 'res.company',
                    method: odooEvent.data.rpc_method,
                    args: [],
                })
                    .then(
                        function(rslt_action) {
                            if (rslt_action !== undefined) {
                                self.do_action(rslt_action, {
                                    action_context: odooEvent.data.context,
                                    on_close: function () {
                                        self.trigger_up('reload'); //Reloads the dashboard to refresh the status of the setup bar.
                                    },
                                });
                            }
                            else { //Happens for any button not returning anything, like the cross to close the setup bar, for example.
                                self.trigger_up('reload');
                            }
                        });
            }
        }
    });

    var AccountDashboardView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Model: AccountSetupBarModel,
            Renderer: AccountSetupBarRenderer,
            Controller: AccountSetupBarController,
        }),
        display_name: _lt('Dashboard'),
        icon: 'fa-dashboard',
        searchview_hidden: false,
    });

    view_registry.add('account_setup_bar', AccountDashboardView);

    return {
        Model: AccountSetupBarModel,
        Renderer: AccountSetupBarRenderer,
        Controller: AccountSetupBarController,
    };

});