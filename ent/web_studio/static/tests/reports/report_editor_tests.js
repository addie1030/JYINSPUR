odoo.define('web_studio.ReportEditor_tests', function (require) {
"use strict";

var studioTestUtils = require('web_studio.testUtils');

QUnit.module('Studio', {}, function () {

QUnit.module('ReportEditor', {
    beforeEach: function () {
    },
}, function () {
    QUnit.test('basic report rendering', function (assert) {
        assert.expect(2);

        var nodesArchs = {
            42: {
                attrs: {
                    'data-oe-id': '42',
                    'data-oe-xpath': '/t',
                    name: "Layout",
                    't-name': '42',
                },
            },
            id: 42,
            key: 'report.layout',
            parent: null,
            tag: 't',
        };
        var reportHTML = "<html><body><t/></body></html>";
        var editor = studioTestUtils.createReportEditor({
            nodesArchs: nodesArchs,
            reportHTML: reportHTML,
        });

        assert.strictEqual(editor.$('iframe').length, 1,
            "an iframe should be rendered");
        assert.strictEqual(editor.$('iframe').attr('src'), "about:blank",
            "the source should be correctly set");

        editor.destroy();
    });
});

});

});
