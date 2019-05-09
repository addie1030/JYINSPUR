odoo.define('web.control_panel_mobile_tests', function (require) {
"use strict";

var testUtils = require('web.test_utils');

var createActionManager = testUtils.createActionManager;

QUnit.module('Control Panel', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    foo: {string: "Foo", type: "char"},
                },
                records: [
                    {id: 1, display_name: "First record", foo: "yop"},
                ],
            },
        };

        this.actions = [{
            id: 1,
            name: 'Partners Action 1',
            res_model: 'partner',
            type: 'ir.actions.act_window',
            views: [[false, 'list']],
        }];

        this.archs = {
            // list views
            'partner,false,list': '<tree><field name="foo"/></tree>',

            // search views
            'partner,false,search': '<search><field name="foo" string="Foo"/></search>',
        };
    },
}, function () {
    QUnit.test('searchview should be hidden by default', function (assert) {
        assert.expect(4);

        var actionManager = createActionManager({
            actions: this.actions,
            archs: this.archs,
            data: this.data,
        });

        actionManager.doAction(1);

        assert.ok($('.o_control_panel').hasClass('o_breadcrumb_full'),
            "should use full width to display the breadcrumbs by default");
        assert.notOk($('.o_control_panel .o_mobile_search').is(':visible'),
            "search options are hidden by default");
        assert.strictEqual($('.o_control_panel .o_enable_searchview').length, 1,
            "should display a button to toggle the searchview");

        // toggle the searchview
        $('.o_control_panel .o_enable_searchview').click();

        assert.ok($('.o_control_panel .o_mobile_search').is(':visible'),
            "search options should now be visible");

        actionManager.destroy();
    });

});

});
