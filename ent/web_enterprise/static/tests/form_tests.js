odoo.define('web_enterprise.form_tests', function (require) {
"use strict";

var FormView = require('web.FormView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('web_enterprise', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    display_name: { string: "Displayed name", type: "char" },
                    trululu: {string: "Trululu", type: "many2one", relation: 'partner'},
                },
                records: [{
                    id: 1,
                    display_name: "first record",
                    trululu: 4,
                }, {
                    id: 2,
                    display_name: "second record",
                    trululu: 1,
                }, {
                    id: 4,
                    display_name: "aaa",
                }],
            },
        };
    }
}, function () {

    QUnit.module('Mobile FormView');

    QUnit.test('statusbar buttons are correctly rendered in mobile', function (assert) {
        assert.expect(5);

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form string="Partners">' +
                    '<header>' +
                        '<button string="Confirm"/>' +
                        '<button string="Do it"/>' +
                    '</header>' +
                    '<sheet>' +
                        '<group>' +
                            '<button name="display_name"/>' +
                        '</group>' +
                    '</sheet>' +
                '</form>',
            res_id: 1,
        });

        assert.strictEqual(form.$('.o_statusbar_buttons a:contains(Action)').length, 1,
            "statusbar should contain a button 'Action'");
        assert.strictEqual(form.$('.o_statusbar_buttons .dropdown-menu').length, 1,
            "statusbar should contain a dropdown");
        assert.strictEqual(form.$('.o_statusbar_buttons .dropdown-menu:visible').length, 0,
            "dropdown should be hidden");

        // open the dropdown
        form.$('.o_statusbar_buttons a').click();
        assert.strictEqual(form.$('.o_statusbar_buttons .dropdown-menu:visible').length, 1,
            "dropdown should be visible");
        assert.strictEqual(form.$('.o_statusbar_buttons .dropdown-menu > button').length, 2,
            "dropdown should contain 2 buttons");

        form.destroy();
    });

    QUnit.test('statusbar "Action" button not displayed if no buttons', function (assert) {
        assert.expect(1);

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form string="Partners">' +
                    '<header><field name="trululu" widget="statusbar"/></header>' +
                    '<sheet>' +
                        '<group>' +
                            '<button name="display_name"/>' +
                        '</group>' +
                    '</sheet>' +
                '</form>',
            res_id: 1,
        });

        assert.strictEqual(form.$('.o_statusbar_buttons').length, 0,
            "statusbar buttons are not displayed as there is no button");

        form.destroy();
    });
});

});
