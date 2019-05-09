odoo.define('web_mobile.tests', function (require) {
"use strict";

var FormView = require('web.FormView');
var KanbanView = require('web.KanbanView');
var testUtils = require('web.test_utils');

var mobile = require('web_mobile.rpc');

var createView = testUtils.createView;

QUnit.module('web_mobile', {
    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    name: {string: "name", type: "char"},
                    image: {},
                    parent_id: {string: "Parent", type: "many2one", relation: 'partner'},
                    sibling_ids: {string: "Sibling", type: "many2many", relation: 'partner'},
                    phone: {},
                    mobile: {},
                    email: {},
                    street: {},
                    street2: {},
                    city: {},
                    state_id: {},
                    zip: {},
                    country_id: {},
                    website: {},
                    function: {},
                    title: {},
                },
                records: [{
                    id: 1,
                    name: 'coucou1',
                }, {
                    id: 2,
                    name: 'coucou2',
                }, {
                    id: 11,
                    name: 'coucou3',
                    image: 'image',
                    parent_id: 1,
                    phone: 'phone',
                    mobile: 'mobile',
                    email: 'email',
                    street: 'street',
                    street2: 'street2',
                    city: 'city',
                    state_id: 'state_id',
                    zip: 'zip',
                    country_id: 'country_id',
                    website: 'website',
                    function: 'function',
                    title: 'title',
                }],
            },
        };
    },
}, function () {

    QUnit.test("contact sync in a non-mobile environment", function (assert) {
        assert.expect(2);

        var rpcCount = 0;

        var form = createView({
            View: FormView,
            arch: '<form>' +
                    '<sheet>' +
                        '<div name="button_box">' +
                            '<contactsync> </contactsync>' +
                        '</div>' +
                        '<field name="name"/>' +
                    '</sheet>' +
                  '</form>',
            data: this.data,
            model: 'partner',
            mockRPC: function () {
                rpcCount++;
                return this._super.apply(this, arguments);
            },
            res_id: 11,
        });

        var $button = form.$('button.oe_stat_button[widget="contact_sync"]');

        assert.strictEqual($button.length, 0, "the tag should not be visible in a non-mobile environment");
        assert.strictEqual(rpcCount, 1, "no extra rpc should be done by the widget (only the one from the view)");

        form.destroy();
    });

    QUnit.test("contact sync in a mobile environment", function (assert) {
        assert.expect(5);


        var __addContact = mobile.methods.addContact;
        var addContactRecord;
        // override addContact to simulate a mobile environment
        mobile.methods.addContact = function (r) {
            addContactRecord = r;
        };

        var rpcDone;
        var rpcCount = 0;

        var form = createView({
            View: FormView,
            arch:
                '<form>' +
                    '<sheet>' +
                        '<div name="button_box">' +
                            '<contactsync> </contactsync>' +
                        '</div>' +
                        '<field name="name"/>' +
                    '</sheet>' +
                '</form>',
            data: this.data,
            model: 'partner',
            mockRPC: function (route, args) {
                if (args.method === "read" && args.args[0] === 11 && _.contains(args.args[1], 'phone')) {
                    rpcDone = true;
                }
                rpcCount++;
                return this._super(route, args);
            },
            res_id: 11,
        });

        var $button = form.$('button.oe_stat_button[widget="contact_sync"]');

        assert.strictEqual($button.length, 1, "the tag should be visible in a mobile environment");
        assert.strictEqual(rpcCount, 1, "no extra rpc should be done by the widget (only the one from the view)");

        $button.click();

        assert.strictEqual(rpcCount, 2, "an extra rpc should be done on click");
        assert.ok(rpcDone, "a read rpc should have been done");
        assert.deepEqual(addContactRecord, {
            "city": "city",
            "country_id": "country_id",
            "email": "email",
            "function": "function",
            "id": 11,
            "image": "image",
            "mobile": "mobile",
            "name": "coucou3",
            "parent_id":  [
                1,
                "coucou1",
            ],
            "phone": "phone",
            "state_id": "state_id",
            "street": "street",
            "street2": "street2",
            "title": "title",
            "website": "website",
            "zip": "zip"
        }, "all data should be correctly passed");

        mobile.methods.addContact = __addContact;

        form.destroy();
    });

    QUnit.test("many2one in a mobile environment [REQUIRE FOCUS]", function (assert) {
        assert.expect(4);

        var mobileDialogCall = 0;

        // override addContact to simulate a mobile environment
        var __addContact = mobile.methods.addContact;
        var __many2oneDialog = mobile.methods.many2oneDialog;

        mobile.methods.addContact = true;
        mobile.methods.many2oneDialog = function () {
            mobileDialogCall++;
            return $.when({data: {}});
        };

        var form = createView({
            View: FormView,
            arch:
                '<form>' +
                    '<sheet>' +
                        '<field name="parent_id"/>' +
                    '</sheet>' +
                '</form>',
            data: this.data,
            model: 'partner',
            res_id: 2,
            viewOptions: {mode: 'edit'},
        });

        var $input = form.$('input');

        assert.notStrictEqual($input[0], document.activeElement,
            "autofocus should be disabled");

        assert.strictEqual(mobileDialogCall, 0,
            "the many2one mobile dialog shouldn't be called yet");
        assert.notOk($input.hasClass('ui-autocomplete-input'),
            "autocomplete should not be visible in a mobile environment");

        $input.click();

        assert.strictEqual(mobileDialogCall, 1,
            "the many2one should call a special dialog in a mobile environment");

        mobile.methods.addContact = __addContact;
        mobile.methods.many2oneDialog = __many2oneDialog;

        form.destroy();
    });

    QUnit.test("many2many_tags in a mobile environment", function (assert) {
        assert.expect(6);

        var mobileDialogCall = 0;
        var rpcReadCount = 0;

        // override many2oneDialog to simulate a mobile environment
        var __many2oneDialog = mobile.methods.many2oneDialog;

        mobile.methods.many2oneDialog = function (args) {
            mobileDialogCall++;
            if (mobileDialogCall === 1) {
                // mock a search on 'coucou3'
                return $.when({'data': {'action': 'search', 'term': 'coucou3'}});
            } else if (mobileDialogCall === 2) {
                // then mock selection of first record found
                assert.strictEqual(args.records.length, 2, "there should be 1 record and create action");
                return $.when({'data': {'action': 'select', 'value': {'id': args.records[0].id}}});
            }
        };

        var form = createView({
            View: FormView,
            arch:
                '<form>' +
                    '<sheet>' +
                        '<field name="sibling_ids" widget="many2many_tags"/>' +
                    '</sheet>' +
                '</form>',
            data: this.data,
            model: 'partner',
            res_id: 2,
            viewOptions: {mode: 'edit'},
            mockRPC: function (route, args) {
                if (args.method === "read" && args.model === "partner") {
                    if (rpcReadCount === 0) {
                        assert.deepEqual(args.args[0], [2], "form should initially show partner 2");
                    } else if (rpcReadCount === 1) {
                        assert.deepEqual(args.args[0], [11], "partner 11 should have been selected");
                    }
                    rpcReadCount++;
                }
                return this._super.apply(this, arguments);
            },
        });

        var $input = form.$('input');

        assert.strictEqual(mobileDialogCall, 0, "the many2many_tags should be disabled in a mobile environment");

        $input.click();

        assert.strictEqual(mobileDialogCall, 2, "the many2many_tags should call mobileDialog with and without search");
        assert.strictEqual(rpcReadCount, 2, "there should be a read for current form record and selected sibling");

        mobile.methods.many2oneDialog = __many2oneDialog;

        form.destroy();
    });

    QUnit.test('autofocus quick create form', function (assert) {
        assert.expect(2);

        var kanban = createView({
            View: KanbanView,
            model: 'partner',
            data: this.data,
            arch: '<kanban on_create="quick_create">' +
                    '<templates><t t-name="kanban-box">' +
                        '<div><field name="name"/></div>' +
                    '</t></templates>' +
                '</kanban>',
            groupBy: ['parent_id'],
        });

        // quick create in first column
        kanban.$buttons.find('.o-kanban-button-new').click();
        assert.ok(kanban.$('.o_kanban_group:nth(0) > div:nth(1)').hasClass('o_kanban_quick_create'),
            "clicking on create should open the quick_create in the first column");
        assert.strictEqual(document.activeElement, kanban.$('.o_kanban_quick_create .o_input:first')[0],
            "the first input field should get the focus when the quick_create is opened");

        kanban.destroy();
    });
});
});
