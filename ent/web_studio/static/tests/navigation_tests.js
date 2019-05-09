odoo.define('web_studio.navigation_tests', function (require) {
"use strict";

var bus = require('web_studio.bus');
var testUtils = require('web.test_utils');

var createActionManager = testUtils.createActionManager;

QUnit.module('Studio Navigation', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    foo: {string: "Foo", type: "char"},
                    bar: {string: "Bar", type: "many2one", relation: 'partner'},
                },
                records: [
                    {id: 1, display_name: "First record", foo: "yop"},
                    {id: 2, display_name: "Second record", foo: "blip"},
                    {id: 3, display_name: "Third record", foo: "gnap"},
                    {id: 4, display_name: "Fourth record", foo: "plop"},
                    {id: 5, display_name: "Fifth record", foo: "zoup"},
                ],
            },
            pony: {
                fields: {
                    name: {string: 'Name', type: 'char'},
                },
                records: [
                    {id: 4, name: 'Twilight Sparkle'},
                    {id: 6, name: 'Applejack'},
                    {id: 9, name: 'Fluttershy'},
                ],
            },
        };

        this.actions = [{
            id: 1,
            name: 'Partners Action 4',
            res_model: 'partner',
            type: 'ir.actions.act_window',
            views: [[1, 'kanban'], [2, 'list'], [false, 'form']],
        }, {
            id: 2,
            name: 'Favorite Ponies',
            res_model: 'pony',
            type: 'ir.actions.act_window',
            views: [[false, 'list'], [false, 'form']],
        }];

        this.archs = {
            // kanban views
            'partner,1,kanban': '<kanban><templates><t t-name="kanban-box">' +
                    '<div class="oe_kanban_global_click"><field name="foo"/></div>' +
                '</t></templates></kanban>',

            // list views
            'partner,false,list': '<tree><field name="foo"/></tree>',
            'partner,2,list': '<tree><field name="foo"/></tree>',
            'pony,false,list': '<tree><field name="name"/></tree>',

            // form views
            'partner,false,form': '<form>' +
                    '<header>' +
                        '<button name="object" string="Call method" type="object"/>' +
                        '<button name="4" string="Execute action" type="action"/>' +
                    '</header>' +
                    '<group>' +
                        '<field name="display_name"/>' +
                        '<field name="foo"/>' +
                    '</group>' +
                '</form>',
            'pony,false,form': '<form>' +
                    '<field name="name"/>' +
                '</form>',

            // search views
            'partner,false,search': '<search><field name="foo" string="Foo"/></search>',
            'pony,false,search': '<search></search>',
        };
    },
}, function () {
    QUnit.module('Misc');

    QUnit.test('open Studio with act_window', function (assert) {
        assert.expect(16);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route) {
                assert.step(route);
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(1);  // open a act_window_action

        var rpcs = ['/web/action/load', '/web/dataset/call_kw/partner', '/web/dataset/search_read'];
        assert.verifySteps(rpcs, "should have loaded the action");

        actionManager.doAction('action_web_studio_action_editor', {
            action: actionManager.getCurrentAction(),
        });
        bus.trigger('studio_toggled', 'main');

        rpcs.push('/web_studio/get_studio_view_arch');
        rpcs.push('/web/dataset/call_kw/partner');  // load_views with studio in context
        rpcs.push('/web/dataset/search_read');
        assert.verifySteps(rpcs, "should have opened the action in Studio");

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_kanban_view_editor').length, 1,
            "the kanban view should be opened");
        assert.strictEqual(actionManager.$('.o_kanban_record:contains(yop)').length, 1,
            "the first partner should be displayed");

        actionManager.restoreStudioAction();  // simulate leaving Studio

        rpcs.push('/web/action/load');
        rpcs.push('/web/dataset/call_kw/partner');  // load_views
        rpcs.push('/web/dataset/search_read');
        assert.verifySteps(rpcs, "should have reloaded the previous action edited by Studio");

        assert.strictEqual(actionManager.$('.o_web_studio_client_action').length, 0,
            "Studio should be closed");
        assert.strictEqual(actionManager.$('.o_kanban_view .o_kanban_record:contains(yop)').length, 1,
            "the first partner should be displayed in kanban");

        actionManager.destroy();
    });

    QUnit.test('open Studio with act_window and viewType', function (assert) {
        assert.expect(2);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route) {
                if (route === '/web_studio/chatter_allowed') {
                    return $.when(true);
                }
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(1);  // open a act_window_action
        actionManager.doAction('action_web_studio_action_editor', {
            action: actionManager.getCurrentAction(),
            viewType: 'form',
        });
        bus.trigger('studio_toggled', 'main');

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_form_view_editor').length, 1,
            "the form view should be opened");
        assert.strictEqual(actionManager.$('.o_field_widget[name="foo"]').text(), "yop",
            "the first partner should be displayed");

        actionManager.destroy();
    });

    QUnit.test('switch view and close Studio', function (assert) {
        assert.expect(3);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route) {
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(1);  // open a act_window_action

        var action = actionManager.getCurrentAction();
        actionManager.doAction('action_web_studio_action_editor', {
            action: action,
        });
        bus.trigger('studio_toggled', 'main');

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_kanban_view_editor').length, 1,
            "the kanban view should be opened");
        actionManager.doAction('action_web_studio_action_editor', {
            action: action,
            pushState: false,
            replace_last_action: true,
            viewType: 'list',
        });
        actionManager.restoreStudioAction();  // simulate leaving Studio

        assert.strictEqual(actionManager.$('.o_web_studio_client_action').length, 0,
            "Studio should be closed");
        assert.strictEqual(actionManager.$('.o_list_view').length, 1,
            "the list view should be opened");

        actionManager.destroy();
    });

    QUnit.test('navigation in Studio with act_window', function (assert) {
        assert.expect(25);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route) {
                assert.step(route);
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(1);  // open a act_window_action

        var rpcs = ['/web/action/load', '/web/dataset/call_kw/partner', '/web/dataset/search_read'];
        assert.verifySteps(rpcs, "should have loaded the action");

        actionManager.doAction('action_web_studio_action_editor', {
            action: actionManager.getCurrentAction(),
        });
        bus.trigger('studio_toggled', 'main');

        rpcs.push('/web_studio/get_studio_view_arch');
        rpcs.push('/web/dataset/call_kw/partner');  // load_views with studio in context
        rpcs.push('/web/dataset/search_read');
        assert.verifySteps(rpcs, "should have opened the action in Studio");

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_kanban_view_editor').length, 1,
            "the kanban view should be opened");
        assert.strictEqual(actionManager.$('.o_kanban_record:contains(yop)').length, 1,
            "the first partner should be displayed");

        this.actions[1].studioNavigation = true;  // is normally set by the webclient
        actionManager.doAction(2);  // favourite ponies

        rpcs.push('/web/action/load');
        assert.verifySteps(rpcs, "should not have done any extra rpc for the new action");

        actionManager.doAction('action_web_studio_action_editor', {
            action: actionManager.getCurrentAction(),
            studio_clear_breadcrumbs: true,  // is normally set by the webclient
        });

        rpcs.push('/web_studio/get_studio_view_arch');
        rpcs.push('/web/dataset/call_kw/pony');  // load_views with studio in context
        rpcs.push('/web/dataset/search_read');
        assert.verifySteps(rpcs, "should have opened the navigated action in Studio");

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_list_view_editor').length, 1,
            "the list view should be opened");
        assert.strictEqual(actionManager.$('.o_list_view .o_data_cell').text(), "Twilight SparkleApplejackFluttershy",
            "the list of ponies should be correctly displayed");

        this.actions[1].studioNavigation = false;
        actionManager.restoreStudioAction();  // simulate leaving Studio

        rpcs.push('/web/action/load');
        rpcs.push('/web/dataset/call_kw/pony');  // load_views
        rpcs.push('/web/dataset/search_read');
        assert.verifySteps(rpcs, "should have reloaded the previous action edited by Studio");

        assert.strictEqual(actionManager.$('.o_web_studio_client_action').length, 0,
            "Studio should be closed");
        assert.strictEqual(actionManager.$('.o_list_view').length, 1,
            "the list view should be opened");
        assert.strictEqual(actionManager.$('.o_list_view .o_data_cell').text(), "Twilight SparkleApplejackFluttershy",
            "the list of ponies should be correctly displayed");

        actionManager.destroy();
    });

    QUnit.test('keep action context when leaving Studio', function (assert) {
        assert.expect(2);

        this.actions[0].context = "{'active_id': 1}";
        var nbLoadAction = 0;

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route, args) {
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                } else if (route === '/web/action/load') {
                    nbLoadAction++;
                    if (nbLoadAction === 2) {
                        assert.deepEqual(args.kwargs.additional_context, {
                            active_id: 1,
                        }, "the context should be correctly passed when leaving Studio");
                    }
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(1);  // open a act_window_action
        actionManager.doAction('action_web_studio_action_editor', {
            action: actionManager.getCurrentAction(),
        });
        bus.trigger('studio_toggled', 'main');
        actionManager.restoreStudioAction();  // simulate leaving Studio
        assert.strictEqual(nbLoadAction, 2, "the action should have been loaded twice");
        actionManager.destroy();
    });

    QUnit.test('open same record when leaving form', function (assert) {
        assert.expect(3);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
            mockRPC: function (route) {
                if (route === '/web_studio/chatter_allowed') {
                    return $.when(true);
                }
                if (route === '/web_studio/get_studio_view_arch') {
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        actionManager.doAction(2);  // open a act_window_action
        actionManager.$('.o_list_view tbody tr:first td:contains(Twilight Sparkle)').click();

        var action = actionManager.getCurrentAction();
        actionManager.doAction('action_web_studio_action_editor', {
            action: action,
            viewType: 'form',  // is normally set by the webclient
        });
        bus.trigger('studio_toggled', 'main');

        assert.strictEqual(actionManager.$('.o_web_studio_client_action .o_web_studio_form_view_editor').length, 1,
            "the form view should be opened");
        actionManager.restoreStudioAction();  // simulate leaving Studio
        assert.strictEqual(actionManager.$('.o_form_view').length, 1,
            "the form view should be opened");
        assert.strictEqual(actionManager.$('.o_form_view span:contains(Twilight Sparkle)').length, 1,
            "should have open the same record");

        actionManager.destroy();
    });
});

});
