odoo.define('sign.document_backend_tests', function (require) {
"use strict";

var testUtils = require('web.test_utils');
var createActionManager = testUtils.createActionManager;

QUnit.module('document_backend_tests', function () {
    QUnit.test('simple rendering', function (assert) {
        assert.expect(1);

        var actionManager = createActionManager({
            actions: [{
                id: 9,
                name: 'A Client Action',
                tag: 'sign.Document',
                type: 'ir.actions.client',
                context: {id: 5, token: 'abc'},
            }],
            mockRPC: function (route) {
                if (route === '/sign/get_document/5/abc') {
                    return $.when('<span>def</span>');
                }
                return this._super.apply(this, arguments);
            },
        });


        actionManager.doAction(9, {context: {id: 4}});

        assert.strictEqual(actionManager.$('.o_sign_document').text(), 'def',
            'should display text from server');

        actionManager.destroy();
    });

    QUnit.test('do not crash when leaving the action', function (assert) {
        assert.expect(0);

        var actionManager = createActionManager({
            actions: [{
                id: 9,
                name: 'A Client Action',
                tag: 'sign.Document',
                type: 'ir.actions.client',
                context: {id: 5, token: 'abc'},
            }],
            mockRPC: function (route) {
                if (route === '/sign/get_document/5/abc') {
                    return $.when('<span>def</span>');
                }
                return this._super.apply(this, arguments);
            },
        });


        actionManager.doAction(9, {context: {id: 4}});
        actionManager.doAction(9, {context: {id: 4}});

        actionManager.destroy();
    });

});

});