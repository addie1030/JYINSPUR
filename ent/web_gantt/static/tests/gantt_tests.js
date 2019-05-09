odoo.define('web.gantt_tests', function (require) {
"use strict";

var GanttView = require('web_gantt.GanttView');
var testUtils = require('web.test_utils');

var initialDate = new Date("2016-12-12T08:00:00Z");

var createActionManager = testUtils.createActionManager;
var createAsyncView = testUtils.createAsyncView;

QUnit.module('Views', {
    beforeEach: function () {
        this.data = {
            task: {
                fields: {
                    id: {string: "ID", type: "integer"},
                    name: {string: "name", type: "char"},
                    start: {string: "start", type: "datetime"},
                    stop: {string: "stop", type: "datetime"},
                    progress: {string: "progress", type: "integer"},
                    time: {string: "Time", type: "float"},
                    user_id: {string: "User", type: "many2one", relation: 'user'},
                    active: {string: "active", type: "boolean", default: true},
                },
                records: [
                    {id: 1, name: "task 1", start: "2016-12-11 00:00:00", stop: "2016-12-13 00:00:00", progress: 50, time: 174.3, user_id: 3, active: true},
                    {id: 2, name: "task 2", start: "2016-12-12 10:55:05", stop: "2016-12-12 14:55:05", progress: 30, time: 88.4, user_id: 3, active: true},
                    {id: 3, name: "task 3", start: "2016-12-27 15:55:05", stop: "2016-12-29 16:55:05", progress: 20, time: 31.0, user_id: 61, active: true},
                    {id: 4, name: "task 4", start: "2016-12-14 15:55:05", stop: "2016-12-14 18:55:05", progress: 90, time: 99.1, user_id: 3, active: true},
                    {id: 5, name: "task 5", start: "2016-12-23 15:55:05", stop: "2016-12-31 18:55:05", progress: 10, time: 41.1, user_id: 61, active: true},
                    {id: 6, name: "task 6", start: "2016-12-28 08:00:00", stop: "2016-12-31 09:00:00", progress: 30, time: 10.9, user_id: 3, active: true},
                ]
            },
            user: {
                fields: {
                    name: {string: "Name", type: "char"}
                },
                records: [{
                    id: 3,
                    name: "jack",
                }, {
                    id: 61,
                    name: "john",
                }]
            },
        };
    }
}, function () {
    QUnit.module('GanttView');

    QUnit.test('simple gantt view', function (assert) {
        assert.expect(10);
        var done = assert.async();

        createAsyncView({
            View: GanttView,
            model: 'task',
            data: this.data,
            arch: '<gantt date_start="start" date_stop="stop" progress="progress"></gantt>',
            viewOptions: {
                initialDate: initialDate,
                action: {name: "Forecasts"}
            },
        }).then(function (gantt) {
            assert.strictEqual(gantt.get('title'), "Forecasts", "should have correct title");
            assert.ok(gantt.$('.gantt_task_scale').length, "should gantt scale part");
            assert.ok(gantt.$('.gantt_data_area').length, "should gantt data part");
            assert.ok(gantt.$('.gantt_hor_scroll').length, "should gantt horizontal scroll bar");
            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 6,
                "should display 6 tasks");

            gantt.$buttons.find('.o_gantt_button_scale[data-value="day"]').trigger('click');
            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 3,
                "should display 3 tasks in day mode");
            assert.strictEqual(gantt.get('title'), "Forecasts (12 Dec)", "should have correct title");

            gantt.$buttons.find('.o_gantt_button_right').trigger('click');
            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 3,
                "should now display 3 tasks");

            gantt.$buttons.find('.o_gantt_button_left').trigger('click');
            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 3,
                "should now display 3 tasks");

            gantt.reload({domain: [['name', 'like', '2']]});

            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 1,
                "should apply the the domain filter");

            gantt.destroy();
            done();
        });
    });

    QUnit.test('breadcrumbs are updated with the displayed period', function (assert) {
        assert.expect(5);

        var archs = {
            'task,1,gantt': '<gantt date_start="start" date_stop="stop" progress="progress"></gantt>',
            'task,false,search': '<search></search>',
        };

        var actions = [{
            id: 1,
            flags: {
                initialDate: initialDate,
            },
            name: 'Forecast Test',
            res_model: 'task',
            type: 'ir.actions.act_window',
            views: [[1, 'gantt']],
        }];

        var actionManager = createActionManager({
            actions: actions,
            archs: archs,
            data: this.data,
        });

        actionManager.doAction(1);

        // there is no selected period by default
        assert.strictEqual(actionManager.controlPanel.$('.breadcrumb-item').text(),
            'Forecast Test', "should display no period");

        // switch to day mode
        actionManager.controlPanel.$('.o_gantt_button_scale[data-value=day]').click();
        assert.strictEqual(actionManager.controlPanel.$('.breadcrumb-item').text(),
            'Forecast Test (12 Dec)', "should display the current day");

        // switch to week mode
        actionManager.controlPanel.$('.o_gantt_button_scale[data-value=week]').click();
        assert.strictEqual(actionManager.controlPanel.$('.breadcrumb-item').text(),
            'Forecast Test (11 Dec - 17 Dec)', "should display the current week");

        // switch to month mode
        actionManager.controlPanel.$('.o_gantt_button_scale[data-value=month]').click();
        assert.strictEqual(actionManager.controlPanel.$('.breadcrumb-item').text(),
            'Forecast Test (December 2016)', "should display the current month");

        // switch to year mode
        actionManager.controlPanel.$('.o_gantt_button_scale[data-value=year]').click();
        assert.strictEqual(actionManager.controlPanel.$('.breadcrumb-item').text(),
            'Forecast Test (2016)', "should display the current year");

        actionManager.destroy();
    });

    QUnit.test('create a task', function (assert) {
        assert.expect(5);
        var done = assert.async();

        var self = this;

        var rpcCount = 0;

        createAsyncView({
            View: GanttView,
            model: 'task',
            data: this.data,
            arch: '<gantt date_start="start" date_stop="stop" progress="progress"></gantt>',
            archs: {
                'task,false,form':
                    '<form string="Task">' +
                        '<field name="name"/>' +
                        '<field name="start"/>' +
                        '<field name="stop"/>' +
                        '<field name="user_id" context="{\'employee_id\': start}"/>' +
                    '</form>',
            },
            viewOptions: {
                initialDate: new Date("2026-04-04T08:00:00Z"),
                action: {name: "Forecasts"}
            },
            mockRPC: function (route, args) {
                rpcCount++;
                return this._super(route, args);
            },
            debounce: false,
        }).then(function (gantt) {

            // when no tasks are present, the gantt library will add an empty
            // task line
            assert.strictEqual(gantt.$('.gantt_bars_area .gantt_task_line').length, 1,
                "should display 1 tasks line");

            gantt.$('.gantt_task_cell').first().click();
            $('.modal .modal-body input:first').val('new task').trigger('input');

            rpcCount = 0;
            $('.modal .modal-footer button.btn-primary').click();  // save

            assert.strictEqual(rpcCount, 2, "should have done 2 rpcs (1 write and 1 searchread to reload)");

            assert.notOk($('.modal').length, "should have closed the modal");
            assert.ok($('div.gantt_tree_content:contains(new task)').length,
                "should display the task name in the dom");

            assert.strictEqual(self.data.task.records.length, 7, "should have created a task");

            // open formViewDialog
            gantt.$('.gantt_cell.gantt_last_cell').click();
            $('.modal .o_field_many2one[name="user_id"] input').click();

            gantt.destroy();
            done();
        });
    });

    QUnit.test('gantt view with consolidation', function (assert) {
        assert.expect(6);
        var done = assert.async();

        createAsyncView({
            View: GanttView,
            model: 'task',
            data: this.data,
            arch: '<gantt type="consolidate" ' +
                    'date_start="start" date_stop="stop" ' +
                    'consolidation="time" ' +
                    'consolidation_max="{&quot;user_id&quot;: 100}">' +
                '</gantt>',
            viewOptions: {
                initialDate: initialDate,
                action: {name: "Forecasts"},
                groupBy: ['user_id']
            },
            mockRPC: function (route, args) {
                assert.step(args.method);
                if (args.method === 'search_read') {
                    assert.deepEqual(args.kwargs.fields, ['name', 'start', 'stop', 'time', 'user_id', 'display_name'],
                        "should fetch only necessary fields");
                }
                return this._super(route, args);
            },
        }).then(function (gantt) {
            assert.strictEqual(gantt.$('.inside_task_bar.o_gantt_color_red[consolidation_ids="gantt_task_1"]').length, 2,
                "should have 2 task bars for task 1, in red");
            assert.strictEqual(gantt.$('.inside_task_bar.o_gantt_colorgreen_3[consolidation_ids="gantt_task_5"]').length, 2,
                "should have 2 task bars for task 5, in green");
            assert.strictEqual(gantt.$('.inside_task_bar[consolidation_ids="gantt_task_5"]:nth-child(3)').text(), '41.10 Time',
                "the number should be rounded to 41.10");

            assert.verifySteps(['search_read']);
            gantt.destroy();
            done();
        });
    });

    QUnit.test('gantt view readonly', function (assert) {
        assert.expect(1);
        var done = assert.async();

        createAsyncView({
            View: GanttView,
            model: 'task',
            data: this.data,
            arch: '<gantt edit="false" date_start="start" date_stop="stop" progress="progress"></gantt>',
            archs: {
                'task,false,form':
                    '<form string="Task">' +
                        '<field name="name"/>' +
                        '<field name="start"/>' +
                        '<field name="stop"/>' +
                        '<field name="user_id" context="{\'employee_id\': start}"/>' +
                    '</form>',
            },
            viewOptions: {
                initialDate: initialDate,
                action: {name: "Forecasts"}
            },
        }).then(function (gantt) {

            // create a task
            gantt.$('.gantt_task_cell').first().click();
            $('.modal .modal-body input:first').val('new task').trigger('input');

            // save it
            $('.modal .modal-footer button.btn-primary').click();

            // open formViewDialog
            gantt.$('.gantt_cell.gantt_last_cell').click();

            assert.ok(gantt.$('.o_form_readonly'),
                "the form dialog should be in readonly mode");

            gantt.destroy();
            done();
        });
    });

    QUnit.test('gantt view disabled create', function (assert) {
        assert.expect(2);
        var done = assert.async();

        createAsyncView({
            View: GanttView,
            model: 'task',
            data: this.data,
            arch: '<gantt create="false" date_start="start" date_stop="stop" progress="progress"></gantt>',
            archs: {
                'task,false,form':
                    '<form string="Task">' +
                        '<field name="name"/>' +
                        '<field name="start"/>' +
                        '<field name="stop"/>' +
                        '<field name="user_id" context="{\'employee_id\': start}"/>' +
                    '</form>',
            },
            viewOptions: {
                initialDate: initialDate,
                action: {name: "Forecasts"}
            },
        }).then(function (gantt) {

            assert.notOk($('body').hasClass('modal-open'),
                "no form dialog should be displayed initially");

            // try create a task
            gantt.$('.gantt_task_cell').first().click();

            assert.notOk($('body').hasClass('modal-open'),
                "no form dialog should be displayed when trying to create a task");

            gantt.destroy();
            done();
        });
    });
});
});
