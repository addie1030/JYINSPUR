odoo.define('sale_subscription_dashboard.sale_subscription_tests', function (require) {
    "use strict";

    var testUtils = require('web.test_utils');

    var SubscriptionDashBoard = require('sale_subscription_dashboard.dashboard');
    SubscriptionDashBoard.sale_subscription_dashboard_main.include({
        update_cp: function () {},
    });
    SubscriptionDashBoard.sale_subscription_dashboard_salesman.include({
        update_cp: function () {},
    });
    QUnit.module('sale_subscription_dashboard', {
        beforeEach: function () {
            this.data = {
                fetch_data: {
                    stat_types: {
                        net_revenue: {
                            prior: 1,
                            add_symbol: "currency",
                            code: "net_revenue",
                            name: "Net Revenue",
                            dir: "up",
                            type: "sum"
                        }
                    },
                    forecast_stat_types: {
                        mrr_forecast: {
                            prior: 1,
                            add_symbol: "currency",
                            code: "mrr_forecast",
                            name: "Forecasted Annual MRR Growth"
                        },
                    },
                    currency_id: 3,
                    contract_templates: [{
                        id: 1,
                        name: "Odoo Monthly"
                    }, {
                        id: 2,
                        name: "Odoo Yearly"
                    }],
                    tags: [{
                        id: 1,
                        name: "Contracts"
                    }, {
                        id: 2,
                        name: "Odoo Online"
                    }],
                    companies: {
                        id: 1,
                        name: "YourCompany"
                    },
                    has_mrr: true,
                    has_def_revenues: true,
                    has_template: true
                },
                compute_stats_graph: {
                    graph: [{
                        0: "2017-08-15",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-16",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-17",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-18",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-19",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-20",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-21",
                        1: 0,
                        series: 0
                    }, {
                        0: "2017-08-22",
                        1: 240,
                        series: 0
                    }, {
                        0: "2017-08-23",
                        1: 40,
                        series: 0
                    }, {
                        0: "2017-08-24",
                        1: 0,
                        series: 0
                    }],
                    stats: {
                        perc: 0,
                        value_1: "0",
                        value_2: "280"
                    }

                },
                forecast_values: {
                    starting_value: 1056,
                    projection_time: 12,
                    churn: 0,
                    expon_growth: 15,
                    linear_growth: 0
                },
                fetch_salesman: {
                    currency_id: 3,
                    default_salesman: {
                        id: 1,
                        name: "Mitchell Admin"
                    },
                    salesman_ids: [{
                        id: 1,
                        name: "Mitchell Admin"
                    }, {
                        id: 5,
                        name: "Marc Demo"
                    }]
                },
                salesman_values: {
                    new: 625,
                    churn: 0,
                    up: 50,
                    down: 0,
                    net_new: 600,
                    contract_modifications: [{
                        partner: "Agrolait",
                        account_analytic: "Agrolait",
                        account_analytic_template: "Odoo Monthly",
                        previous_mrr: 500,
                        current_mrr: 800,
                        diff: 300,
                        type: 'up',
                    }],
                    nrr: 1195,
                    nrr_invoices: [{
                        partner: "Joel Willis",
                        account_analytic_template: "Odoo Monthly",
                        nrr: "20.0",
                        account_analytic: false
                    }, {
                        partner: "Agrolait",
                        account_analytic_template: "Odoo Monthly",
                        nrr: "525.0",
                        account_analytic: false
                    }, {
                        partner: "Agrolait",
                        account_analytic_template: "Odoo Monthly",
                        nrr: "650.0",
                        account_analytic: false
                    }]
                },
                get_stats_by_plan: [{
                    name: "Odoo Monthly",
                    nb_customers: 0,
                    value: 0
                }, {
                    name: "Odoo Yearly",
                    nb_customers: 0,
                    value: 0
                }],
                get_stats_history: {
                    value_1_months_ago: 0,
                    value_3_months_ago: 0,
                    value_12_months_ago: 0
                },
                compute_stat: 10495,
            };
        }
    }, function () {

        QUnit.test('sale_subscription_test', function (assert) {
            var done = assert.async();
            var self = this;
            assert.expect(2);
            var subscription_dashboard = new SubscriptionDashBoard.sale_subscription_dashboard_main(null, {
                id: 1
            });
            testUtils.addMockEnvironment(subscription_dashboard, {
                mockRPC: function (route, args) {
                    if (route === '/sale_subscription_dashboard/fetch_data') {
                        return $.when(self.data.fetch_data);
                    }
                    if (route === '/sale_subscription_dashboard/compute_graph_and_stats') {
                        return $.when(self.data.compute_stats_graph);
                    }
                    if (route === '/sale_subscription_dashboard/get_default_values_forecast') {
                        return $.when(self.data.forecast_values);
                    }
                    return $.when();
                },
            });
            subscription_dashboard.appendTo($('#qunit-fixture'));
            assert.strictEqual(subscription_dashboard.$('.on_stat_box .o_stat_box_card_amount').text().trim(), "280", "Should contain net revenue amount '280'");
            assert.strictEqual(subscription_dashboard.$('.on_forecast_box .o_stat_box_card_amount').text().trim(), "1k", "Should contain forecasted annual amount '1k'");
            subscription_dashboard.destroy();
            done();
        });

        QUnit.test('sale_subscription_forecast', function (assert) {
            var done = assert.async();
            var self = this;
            assert.expect(10);
            var dashboard = new SubscriptionDashBoard.sale_subscription_dashboard_forecast(null, null, {
                main_dashboard_action_id: null,
                start_date: moment(),
                end_date: moment().add(1, 'month'),
                currency_id: 3,
                contract_templates: null,
                tags: null,
                companies: null,
                filters: null,
            });
            testUtils.addMockEnvironment(dashboard, {
                mockRPC: function (route, args) {
                    if (route === '/sale_subscription_dashboard/get_default_values_forecast') {
                        assert.deepEqual(_.keys(args).sort(), ['end_date', 'filters', 'forecast_type'], "should be requested only with defined parameters");
                        return $.when(self.data.forecast_values);
                    }
                    return $.when();
                },
                session: {
                    currencies: {
                        3: {
                            digits: [69, 2],
                            position: "before",
                            symbol: "$"
                        }
                    }
                },
            });
            dashboard.appendTo($('#qunit-fixture'));
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard').length, 1, "should have a dashboard");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box').length, 2, "should have a dashboard with 2 forecasts");

            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:first #forecast_summary_mrr').length, 1, "first forecast should have summary header");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:first .o_forecast_options').length, 1, "first forecast should have options");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:first #forecast_chart_div_mrr').length, 1, "first forecast should have chart");

            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:last #forecast_summary_contracts').length, 1, "last forecast should have summary header");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:last .o_forecast_options').length, 1, "last forecast should have options");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box:last #forecast_chart_div_contracts').length, 1, "last forecast should have chart");
            dashboard.destroy();
            done();
        });

        QUnit.test('sale_subscription_detailed', function (assert) {
            var done = assert.async();
            var self = this;
            assert.expect(8);
            var dashboard = new SubscriptionDashBoard.sale_subscription_dashboard_detailed(null, null, {
                main_dashboard_action_id: null,
                stat_types: this.data.fetch_data.stat_types,
                start_date: moment(),
                end_date: moment().add(1, 'month'),
                selected_stat: 'net_revenue',
                currency_id: 3,
                contract_templates: this.data.fetch_data.contract_templates,
                tags: null,
                companies: null,
                filters: {},
            });
            testUtils.addMockEnvironment(dashboard, {
                mockRPC: function (route, args) {
                    if (route === '/sale_subscription_dashboard/compute_stat') {
                        return $.when(self.data.compute_stat);
                    }
                    if (route === '/sale_subscription_dashboard/get_stats_history') {
                        return $.when(self.data.get_stats_history);
                    }
                    if (route === '/sale_subscription_dashboard/compute_graph') {
                        return $.when(self.data.compute_stats_graph.graph);
                    }
                    if (route === '/sale_subscription_dashboard/get_stats_by_plan') {
                        return $.when(self.data.get_stats_by_plan);
                    }
                    return $.when();
                },
                session: {
                    currencies: {
                        3: {
                            digits: [69, 2],
                            position: "before",
                            symbol: "$"
                        }
                    }
                },
            });
            dashboard.appendTo($('#qunit-fixture'));
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard').length, 1, "should have a dashboard");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box').length, 3, "should have a dashboard with 3 boxes");

            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box.o_graph_detailed').length, 1, "should have in first a graph box");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box.o_graph_detailed .o_metric_current').length, 1, "should have the current metric");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box.o_graph_detailed .o_metric_current').text().trim(), "$10k", "should format correctly the current metric value");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box.o_graph_detailed #stat_chart_div').length, 1, "should display a chart");

            assert.strictEqual(dashboard.$('.o_account_contract_dashboard #o-stat-history-box.box').length, 1, "should have in second a history box");
            assert.strictEqual(dashboard.$('.o_account_contract_dashboard .box table').length, 1, "should have in third a table box");

            dashboard.destroy();
            done();
        });

        QUnit.test('sale_subscription_salesman', function (assert) {
            var done = assert.async();
            var self = this;
            assert.expect(9);
            var salesman_dashboard = new SubscriptionDashBoard.sale_subscription_dashboard_salesman();
            testUtils.addMockEnvironment(salesman_dashboard, {
                mockRPC: function (route, args) {
                    if (route === '/sale_subscription_dashboard/fetch_salesmen') {
                        return $.when(self.data.fetch_salesman);
                    }
                    if (route === '/sale_subscription_dashboard/get_values_salesman') {
                        return $.when(self.data.salesman_values);
                    }
                    return $.when();
                },
            });
            salesman_dashboard.appendTo($('#qunit-fixture'));
            assert.strictEqual(salesman_dashboard.$('#mrr_growth_salesman').length, 1, "should display the salesman graph");
            assert.strictEqual(salesman_dashboard.$('h3').first().text(), "MRR : 600", "should contain the MRR Amount '600'");
            assert.strictEqual(salesman_dashboard.$('h3').last().text(), "NRR : 1k", "should contain the NRR Amount '1k'");
            assert.strictEqual(salesman_dashboard.$('#contract_modifications .table-responsive').length, 1, "should display the list of subscription");
            assert.strictEqual(salesman_dashboard.$('#contract_modifications .table-responsive tr:odd td:eq(1)').text() , "Agrolait", "should contain subscription modifications partner 'Agrolait'");
            assert.strictEqual(salesman_dashboard.$('#contract_modifications .table-responsive tr:odd td:last').text() , "800 (300)", "should contain current MRR Amount '800 (300)'");
            assert.strictEqual(salesman_dashboard.$('#NRR_invoices .table-responsive').length, 1, "should display the list of NRR Invoices");
            assert.strictEqual(salesman_dashboard.$('#NRR_invoices .table-responsive tr:eq(2) td:first').text(), "Agrolait", "should contain NRR Invoices partner 'Agrolait'");
            assert.strictEqual(salesman_dashboard.$('#NRR_invoices .table-responsive tr:eq(2) td:last').text(), "525", "should contain NRR Invoices Amount '525'");
            salesman_dashboard.destroy();
            done();
        });
    });
});
