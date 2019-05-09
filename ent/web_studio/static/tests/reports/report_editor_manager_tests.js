odoo.define('web_studio.ReportEditorManager_tests', function (require) {
"use strict";

var ace = require('web_editor.ace');
var config = require('web.config');
var NotificationService = require('web.NotificationService');
var testUtils = require('web.test_utils');
var studioTestUtils = require('web_studio.testUtils');
var session = require('web.session');

function getFloatSizeFromPropertyInPixels($element, propertyName) {
    var size = $element.css(propertyName);
    size = size.slice(0, size.length - 2); // remove the 'px' at the end
    return parseFloat(size);
}

/**
 * Some tests need the style assets inside the iframe, mainly to correctly
 * display the hooks (the hooks sizes are taken into account to decide which
 * ones are the closest ones). This function loads the iframe assets
 * (server-side) and insert them inside the corresponding test template[0] HTML.
 *
 * As a server-side call needs to be done before executing the test, this
 * function wraps the original function.
 *
 * **Warning** only use this function when it's really needed as it's quite
 * expensive.
 */
var loadIframeCss = function (callback) {
    return function WrapLoadIframeCss(assert) {
        var self = this;
        var done = assert.async();
        if (loadIframeCss.assets) {
            var html = self.templates[0].arch.replace('<head/>', loadIframeCss.head);
            self.templates[0].arch = html;
            return callback.call(self, assert, done);
        }

        session.rpc('/web_studio/edit_report/test_load_assets').then(function (assets) {
            loadIframeCss.assets = assets;
            loadIframeCss.head = '<head>';
            loadIframeCss.head += _.map(loadIframeCss.assets.css, function (cssCode, cssFileName) {
                cssCode = cssCode
                    .replace(/\\/g, "\\\\")
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;")
                    .replace(/}/g, "}\n");

                var style = '<style data-href="' + cssFileName + '">\n' + cssCode + '\n</style>';
                var htmlForValidation = '<html><head>' + style + '</head><body></body></html>';
                var xmlDoc = new DOMParser().parseFromString(htmlForValidation, "text/xml");
                if ($('parsererror', xmlDoc).length) {
                    var error = $('div', xmlDoc).text();
                    throw new Error(error);
                }
                return style;
            }).join('\n');
            loadIframeCss.head += '</head>';

            var html = self.templates[0].arch.replace('<head/>', loadIframeCss.head);
            self.templates[0].arch = html;
            return callback.call(self, assert, done);
        });
    };
};


QUnit.module('Studio', {}, function () {

QUnit.module('ReportEditorManager', {
    beforeEach: function () {
        this.models = {
            'model.test': 'Model Test',
            'model.test.child': 'Model Test Child',
        };
        this.data = {
            'model.test': {
                fields: {
                    name: {string: "Name", type: "char"},
                    child: {string: "Child", type: 'many2one', relation: 'model.test.child', searchable: true},
                    child_bis: {string: "Child Bis", type: 'many2one', relation: 'model.test.child', searchable: true},
                    children: {string: "Children", type: 'many2many', relation: 'model.test.child', searchable: true},
                },
                records: [],
            },
            'model.test.child': {
                fields: {
                    name: { string: "Name", type: "char"},
                },
                records: [],
            },
        };
        this.templates = [{
            key: 'template0',
            view_id: 42,
            arch:
                '<kikou>' +
                    '<t t-name="template0">' +
                        '<html>\n' +
                            '<head/>\n' +
                            '<body>' +
                                '<div id="wrapwrap">' +
                                    '<main>' +
                                        '<div class="page">' +
                                            '<t t-call="template1"/>' +
                                        '</div>' +
                                    '</main>' +
                                '</div>' +
                            '</body>\n' +
                        '</html>' +
                    '</t>' +
                '</kikou>',
        }];
    }
}, function () {

    QUnit.test('empty editor rendering', function (assert) {
        var done = assert.async();
        assert.expect(5);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            mockRPC: function (route, args) {
                if (route === '/web_studio/print_report') {
                    assert.strictEqual(args.report_name, 'awesome_report',
                        "the correct report should be printed");
                    assert.strictEqual(args.record_id, 42,
                        "the report should be printed with the correct record");
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('.o_web_studio_sidebar').length, 1,
                "a sidebar should be rendered");

            // no content helper
            assert.strictEqual(rem.$('iframe').contents().find('.page .o_no_content_helper').length, 1,
                "the iframe should be rendered with a no content helper");
            testUtils.intercept(rem, 'node_clicked', function () {
                throw new Error("The no content helper shouldn't be clickable.");
            });
            rem.$('iframe').contents().find('.page .o_no_content_helper').click();

            // printing the report
            assert.strictEqual(rem.$('.o_web_studio_report_print').length, 1,
                "it should be possible to print the report");
            rem.$('.o_web_studio_report_print').click();

            rem.destroy();
            done();
        });
    });

    QUnit.test('basic editor rendering', function (assert) {
        var done = assert.async();
        assert.expect(8);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="class1">' +
                            '<span>First span</span>' +
                        '</div>' +
                        '<t t-call="template2"/>' +
                    '</t>' +
                '</kikou>',
        });
        this.templates.push({
            key: 'template2',
            view_id: 56,
            arch:
                '<kikou>' +
                    '<t t-name="template2">' +
                        '<span>Second span</span>' +
                    '</t>' +
                '</kikou>'
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('.o_web_studio_sidebar').length, 1,
                "a sidebar should be rendered");
            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"First spanSecond span",
                "the iframe should be rendered");

            var iframeContainerwidth = getFloatSizeFromPropertyInPixels(rem.$('.o_web_studio_report_iframe_container'),'width');
            assert.ok(Math.abs(iframeContainerwidth - 794) <= 1,"the default width should be A4 (794px = 210mm) +/- 1px");

            var iframeMinHeight = getFloatSizeFromPropertyInPixels(rem.$('.o_web_studio_report_iframe_container'), 'min-height');
            var heightDifference  = Math.abs( 1122.52 - iframeMinHeight);
            assert.ok( heightDifference <= 1, "the default height should be A4 (1122.52px = 297mm) at +/- 1 px because of decimals");

            // click to edit a span
            rem.$('iframe').contents().find('span:contains(Second)').click();

            assert.ok(rem.$('iframe').contents().find('span:contains(Second)').hasClass('o_web_studio_report_selected'),
                "the corresponding nodes should be selected");
            assert.ok(rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="options"]').hasClass('active'),
                "the sidebar should have been updated");
            assert.strictEqual(rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_content .card').length, 2,
                "there should be 2 cards in the sidebar");

            // click on "Options" (shouldn't do anything)
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="options"]').click();
            assert.strictEqual(rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_content .card').length, 2,
                "there should still be 2 cards in the sidebar");

            rem.destroy();
            done();
        });
    });

    QUnit.test('editor rendering with paperformat', function (assert) {
        var done = assert.async();
        assert.expect(2);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="class1">' +
                            '<span>First span</span>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            paperFormat: {
                print_page_width: 200,
                print_page_height: 400,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
        });

        rem.editorIframeDef.then(function () {
            var iframeWidth = getFloatSizeFromPropertyInPixels(rem.$('.o_web_studio_report_iframe_container'),'width');
            assert.ok(Math.abs(iframeWidth-756) <= 1,"the width should be taken from the paperFormat +/- 1px");

            var iframeHeight = getFloatSizeFromPropertyInPixels(rem.$('.o_web_studio_report_iframe_container'), 'min-height');
            var heightDifference  = Math.abs( 1511.81 - iframeHeight) ;
            assert.ok(heightDifference <= 1, "the height should be taken from the paperFormat +/- 1 px");

            rem.destroy();
            done();
        });
    });

    QUnit.test('use pager', function (assert) {
        var done = assert.async();
        assert.expect(6);
        var self = this;

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="class1">' +
                            '<span>First span</span>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/get_report_views') {
                    assert.strictEqual(args.record_id, 43,
                        "the record id should be correctly set");
                    self.templates[1].arch = '<kikou>' +
                        '<t t-name="template1">' +
                            '<div class="row">' +
                                '<div class="col-12">' +
                                    '<span>hello</span>' +
                                '</div>' +
                            '</div>' +
                        '</t>' +
                    '</kikou>';
                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('iframe').contents().find('.page').text(), "First span",
                "the iframe should be rendered");
            assert.strictEqual(rem.$('.o_web_studio_report_pager').length, 1,
                "there should be a pager");
            assert.strictEqual(rem.$('.o_web_studio_report_pager').text().trim(), "1 / 2",
                "the pager should be correctly rendered");

            // click to switch between records
            rem.$('.o_web_studio_report_pager .o_pager_next').click();

            assert.strictEqual(rem.$('iframe').contents().find('.page').text(), "hello",
                "the iframe should be updated");
            assert.strictEqual(rem.$('.o_web_studio_report_pager').text().trim(), "2 / 2",
                "the pager should be correctly updated");

            rem.destroy();
            done();
        });
    });

    QUnit.test('components edition', function (assert) {
        var done = assert.async();
        assert.expect(7);

        var self = this;
        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>First span</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    assert.deepEqual(args, {
                        context: {},
                        operations: [{
                            context: {},
                            inheritance: [{
                                content: "<span>hello</span>",
                                position: "replace",
                                view_id: 55,
                                xpath: "/t/div/div/span"
                            }],
                            view_id: 55,
                            xpath: '/t/div/div/span',
                        }],
                        record_id: 42,
                        report_name: "awesome_report",
                        report_views: studioTestUtils.getReportViews(self.templates),
                    });

                    // directly apply the operation on the view
                    self.templates[1].arch = '<kikou>' +
                        '<t t-name="template1">' +
                            '<div class="row">' +
                                '<div class="col-12">' +
                                    '<span>hello</span>' +
                                '</div>' +
                            '</div>' +
                        '</t>' +
                    '</kikou>';

                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"First span",
                "the iframe should be rendered");

            // click to edit a span
            rem.$('iframe').contents().find('span:contains(First)').click();

            var $textarea = rem.$('.o_web_studio_sidebar .o_web_studio_active textarea[name="text"]');
            assert.strictEqual($textarea.length, 1,
                "there should be a textarea to edit the node text");
            assert.strictEqual($textarea.val(), "First span",
                "the Text component should be correctly set");

            // change the text (should trigger the report edition)
            $textarea.val("hello").trigger('input');

            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"hello",
                "the iframe should have been updated");
            var $newTextarea = rem.$('.o_web_studio_sidebar .o_web_studio_active textarea[name="text"]');
            assert.strictEqual($newTextarea.length, 1,
                "there should still be a textarea to edit the node text");
            assert.strictEqual($newTextarea.val(), "hello",
                "the Text component should have been updated");

            rem.destroy();
            done();
        });
    });

    QUnit.test('components edition 2', function (assert) {
        var done = assert.async();
        assert.expect(6);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>First span</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('.o_web_studio_sidebar_header .active').attr('name'), 'new',
                "the 'Add' tab should be active");
            assert.strictEqual(rem.$('iframe').contents().find('.o_web_studio_report_selected').length, 0,
                "there should be no selected node");

            // click to edit a span
            rem.$('iframe').contents().find('span:contains(First)').click();
            assert.strictEqual(rem.$('.o_web_studio_sidebar_header .active').attr('name'), 'options',
                "the 'Options' tab should be active");
            assert.strictEqual(rem.$('iframe').contents().find('.o_web_studio_report_selected').length, 1,
                "the span should be selected");

            // switch tab
            rem.$('.o_web_studio_sidebar_header [name="report"]').click();
            assert.strictEqual(rem.$('.o_web_studio_sidebar_header .active').attr('name'), 'report',
                "the 'Report' tab should be active");
            assert.strictEqual(rem.$('iframe').contents().find('.o_web_studio_report_selected').length, 0,
                "there should be no selected node anymore");

            rem.destroy();
            done();
        });
    });

    QUnit.test('remove components - when no node is available to select, the add tab is activated', function (assert) {
        var self = this;
        var done = assert.async();
        assert.expect(1);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>First span</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: { },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    self.templates[1].arch = '<kikou>' +
                        '<t t-name="template1">' +
                        '</t>' +
                    '</kikou>';
                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            // click to edit a span
            rem.$('iframe').contents().find('span:contains(First)').click();

            // remove the span from the dom
            rem.$('.o_web_studio_active .o_web_studio_remove').click();
            $('.modal-content .btn-primary').click(); // confirm the deletion
            assert.strictEqual(rem.$('.o_web_studio_sidebar_header .active').attr('name'), 'new',
                "after the remove, 'Add' tab should be active");

            rem.destroy();
            done();
        });
    });

    QUnit.test('drag & drop text component', function (assert) {
        var done = assert.async();
        assert.expect(1);

        var self = this;
        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>First span</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    assert.deepEqual(args, {
                        context: {},
                        operations: [{
                            context: {},
                            inheritance: [{
                                content: "<span>New Text Block</span>",
                                position: "after",
                                view_id: 55,
                                xpath: "/t/div/div/span"
                            }],
                            position: "after",
                            type: "add",
                            view_id: 55,
                            xpath: "/t/div/div/span"
                        }],
                        record_id: 42,
                        report_name: "awesome_report",
                        report_views: studioTestUtils.getReportViews(self.templates),
                    });

                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            // drag and drop a Text component, which should trigger a view edition
            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_component:contains(Text)');
            testUtils.dragAndDrop($text, rem.$('iframe').contents().find('span:contains(First span)'));

            rem.destroy();
            done();
        });
    });

    QUnit.test('drag & drop text component in existing col', loadIframeCss(function (assert, done) {
        assert.expect(1);

        var self = this;
        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-6"/>' +
                            '<div class="col-6"/>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {},
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    assert.deepEqual(args.operations, [{
                        context: {},
                        inheritance: [{
                            content: "<span>New Text Block</span>",
                            position: "inside",
                            view_id: 55,
                            xpath: "/t/div/div[1]"
                        }],
                        position: "inside",
                        type: "add",
                        view_id: 55,
                        xpath: "/t/div/div[1]"
                    }]);

                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            // drag and drop a Text component, which should trigger a view edition
            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_component:contains(Text):eq(1)');
            testUtils.dragAndDrop($text, rem.$('iframe').contents().find('.col-6:eq(1)'));

            rem.destroy();
            done();
        });
    }));

    QUnit.test('drag & drop components and cancel', function (assert) {
        var done = assert.async();
        assert.expect(4);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-3">' +
                                '<span>First span</span>' +
                            '</div>' +
                            '<div class="col-3">' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            // drag and drop a Text component
            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_component:contains(Field):eq(1)');
            testUtils.dragAndDrop($text, rem.$('iframe').contents().find('.col-3:last'));
            assert.strictEqual($('.o_web_studio_field_modal').length, 1, "a field modal should be opened");

            // cancel the field selection
            $('.o_web_studio_field_modal .btn-secondary').click();
            assert.strictEqual(rem.$('iframe').contents().find('.o_web_studio_hook').length, 0, "Must cancel the dragAndDrop");

            // drag and drop an Address component
            var $address = rem.$('.o_web_studio_sidebar .o_web_studio_component:contains(Address)');
            testUtils.dragAndDrop($address, rem.$('iframe').contents().find('.col-3:last'));
            assert.strictEqual($('.o_web_studio_field_modal').length, 1, "a field modal should be opened");

            // cancel the field selection
            $('.o_web_studio_field_modal .btn-secondary').click();
            assert.strictEqual(rem.$('iframe').contents().find('.o_web_studio_hook').length, 0, "Must cancel the dragAndDrop");

            rem.destroy();
            done();
        });
    });

    QUnit.test('drag & drop field block', function (assert) {
        assert.expect(1);
        var done = assert.async();

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                    '</t>' +
                '</kikou>',
        });

        var templateData = {
            dataOeContext: '{"o": "model.test"}'
        };

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        // this is to deal with undo operation (which is
                        // triggered after the first deferred reject)
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance[0].content, "<div class='row'><div class='col'><span t-field=\"o.child.name\"></span></div></div>",
                        "the block should be correctly added");
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            var $field = rem.$('.o_web_studio_sidebar .o_web_studio_field_type_container:eq(0) .o_web_studio_component:contains(Field):eq(0)');
            var $target = rem.$('iframe').contents().find('.page');

            // drag and drop a Field component, which should trigger a view edition
            testUtils.dragAndDrop($field, $target, {position: 'inside'});

            $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="child"]').trigger('click');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="name"]').trigger('click');
            $('.o_web_studio_field_modal .btn-primary').trigger('click');

            rem.destroy();
            done();
        });
    });

    QUnit.test('drag & drop field in row', loadIframeCss(function (assert, done) {
        assert.expect(4); // 2 asserts by test

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-6">' +
                                '<span>Coucou</span>' +
                            '</div>' +
                            '<div class="col-6">' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });
        var templateData = {
            docs: [
                {firstname: 'firstname 1', name: 'name 1', product: 'product 1', price: 10, quantity: 1000, total: 10000},
                {firstname: 'firstname 2', name: 'name 2', product: 'product 2', price: 20, quantity: 2000, total: 40000},
                {firstname: 'firstname 3', name: 'name 3', product: 'product 3', price: 30, quantity: 3000, total: 90000}
            ],
            sum: function (list) {
                return list.reduce(function (a, b) {
                    return a + b;
                }, 0);
            },
            dataOeContext: '{"o": "model.test"}'
        };
        templateData.docs.mapped = function (fieldName) {return _.pluck(this, fieldName);};

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        // this is to deal with undo operation (which is
                        // triggered after the first deferred reject)
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, tests[testIndex].inheritance, tests[testIndex].text);
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        // create multiple tests to avoid duplicating very similar tests
        var tests = [
            {
                text: "Should select the hook next to the span",
                selector: '.row:first .col-6:eq(0)',
                position: 'center',
                nearestHookNumber: 1,
                inheritance: [{
                    content: '<span t-field="o.child.name"></span>',
                    position: 'after',
                    view_id: 55,
                    xpath: '/t/div/div/span',
                }],
            }, {
                text: "Should select the hook inside the col",
                selector: '.row:first .col-6:eq(1)',
                position: 'bottom',
                nearestHookNumber: 1,
                inheritance: [{
                    content: '<span><strong>Name:</strong><br/></span><span t-field="o.child.name"></span>',
                    position: 'inside',
                    view_id: 55,
                    xpath: '/t/div/div[1]',
                }],
            },
        ];
        var testIndex = 0;

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            var $field = rem.$('.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_component:contains(Field)');

            for (testIndex; testIndex < tests.length; testIndex++) {
                var test = tests[testIndex];
                var $target = rem.$('iframe').contents().find(test.selector);
                // drag and drop a Field component, which should trigger a view edition
                testUtils.dragAndDrop($field, $target, {position: test.position});
                var $nearestHook = rem.$('iframe').contents().find('.o_web_studio_nearest_hook');
                assert.strictEqual($nearestHook.length, test.nearestHookNumber, test.text + ' (nearestHook number)');

                $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="child"]').trigger('click');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="name"]').trigger('click');
                $('.o_web_studio_field_modal .btn-primary').trigger('click');
            }

            rem.destroy();
            done();
        });
    }));

    QUnit.test('drag & drop field in table', loadIframeCss(function (assert, done) {
        assert.expect(20);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<table class="table table-sm" style="width: 600px">' +
                            '<thead>' +
                                '<tr>' +
                                    '<th colspan="2"><span>Titre 1</span></th>' +
                                    '<th><span>Titre 2</span></th>' +
                                    '<th colspan="2"><span>Titre 3</span></th>' +
                                    '<th><span>Titre 4</span></th>' +
                                '</tr>' +
                            '</thead>' +
                            '<tbody>' +
                                '<tr t-foreach="docs" t-as="l">' +
                                    '<td width="100px"><span><t t-esc="l.firstname"/></span></td>' +
                                    '<td width="100px"><span><t t-esc="l.name"/></span></td>' +
                                    '<td width="100px"><span><t t-esc="l.product"/></span></td>' +
                                    '<td width="100px"><span><t t-esc="l.price"/></span></td>' +
                                    '<td width="100px"><span><t t-esc="l.quantity"/></span></td>' +
                                    '<td width="100px"><span><t t-esc="l.total"/></span></td>' +
                                '</tr>' +
                                '<tr>' +
                                    '<td/>' +
                                    '<td/>' +
                                    '<td/>' +
                                    '<td class="text-right" colspan="2"><span class="o_bold">Total</span></td>' +
                                    '<td class="text-right"><span class="o_bold"><t t-esc="sum(docs.mapped(\'total\'))"/></span></td>' +
                                '</tr>' +
                            '</tbody>' +
                        '</table>' +
                    '</t>' +
                '</kikou>',
        });
        var templateData = {
            docs: [
                {firstname: 'firstname 1', name: 'name 1', product: 'product 1', price: 10, quantity: 1000, total: 10000},
                {firstname: 'firstname 2', name: 'name 2', product: 'product 2', price: 20, quantity: 2000, total: 40000},
                {firstname: 'firstname 3', name: 'name 3', product: 'product 3', price: 30, quantity: 3000, total: 90000}
            ],
            sum: function (list) {
                return list.reduce(function (a, b) {
                    return a + b;
                }, 0);
            },
            dataOeContext: '{"o": "model.test"}'
        };
        templateData.docs.mapped = function (fieldName) {return _.pluck(this, fieldName);};

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, tests[testIndex].inheritance, tests[testIndex].text);
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        var testIndex = 0;
        var tests = [
            {
                text: "Should select the hooks inside the th",
                selector: 'thead tr th:eq(0)',
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_component:contains(Field)',
                position: 'left',
                nearestHookNumber: 1,
                inheritance: [{
                    content: "<span t-field=\"o.child.name\"></span>",
                    position: "before",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th/span"
                }],
            }, {
                text: "Should select the column (1)",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:eq(1) td:first',
                position: {left: 20, top: 0},
                nearestHookNumber: 5,
                inheritance: [{
                    content: "<th><span>Name</span></th>",
                    position: "before",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th"
                }, {
                    content: "<td><span t-field=\"o.child.name\"></span></td>",
                    position: "before",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td"
                }, {
                    content: "<td></td>",
                    position: "before",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td"
                }],
                onDragAndDrop: function ($table) {
                    assert.strictEqual($table.find('tr th:first-child.o_web_studio_nearest_hook').length, 1,
                            "Should select the first title cell");
                    assert.strictEqual($table.find('tr td:first-child.o_web_studio_nearest_hook').length, 4,
                            "Should select the first cell of each line");
                },
            }, {
                text: "Should select the hooks inside the td, on the left",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_component:contains(Field)',
                selector: 'tbody tr:eq(1) td:first',
                position: 'left',
                nearestHookNumber: 3,
                inheritance: [{
                    content: "<span t-field=\"o.child.name\"></span>",
                    position: "before",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td/span"
                }]
            }, {
                text: "Should select the hooks inside the td, on the right",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_component:contains(Field)',
                selector: 'tbody tr:eq(1) td:eq(0)',
                position: 'center',
                nearestHookNumber: 3,
                inheritance: [{
                    content: "<span t-field=\"o.child.name\"></span>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td/span"
                }],
            },{
                text: "Should select column without the header because it's colspan=2",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:eq(1) td:eq(1)',
                position: {left: -10, top: 0},
                nearestHookNumber: 4,
                inheritance: [{
                    content: "<td><span t-field=\"o.child.name\"></span></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td"
                }, {
                    content: "<td></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td"
                }, {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th"
                }],
            }, {
                text: "Should insert between 2nd and 3rd column",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:eq(1) td:eq(2)',
                position: {left: -10, top: 0},
                nearestHookNumber: 5,
                inheritance: [{
                    content: "<th><span>Name</span></th>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th"
                }, {
                    content: "<td><span t-field=\"o.child.name\"></span></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td[1]"
                  },
                  {
                    content: "<td></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td[1]"
                  },
                  {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th"
                  }],
            }, {
                text: "Should select column without the header because there are two colspan=2",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:eq(1) td:eq(4)',
                position: {top: 0, left: -10},
                nearestHookNumber: 3,
                inheritance: [{
                    content: "<td><span t-field=\"o.child.name\"></span></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td[3]"
                }, {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th[2]"
                }, {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td[3]"
                }],
            }, {
                text: "Should select the column (3)",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:eq(1) td:eq(5)',
                position: 'left',
                nearestHookNumber: 5,
                inheritance: [{
                    content: "<th><span>Name</span></th>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th[2]"
                }, {
                    content: "<td><span t-field=\"o.child.name\"></span></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr/td[4]"
                }, {
                    content: "<td></td>",
                    position: "after",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td[3]"
                }, {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/tbody/tr[1]/td[3]"
                }, {
                    content: "<attribute name=\"colspan\">3</attribute>",
                    position: "attributes",
                    view_id: 55,
                    xpath: "/t/table/thead/tr/th[2]"
                }],
            }, {
                text: "Should select the column (4)",
                buildingBlockSelector: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Field Column)',
                selector: 'tbody tr:first td:eq(5)',
                position: 'right',
                nearestHookNumber: 5,
                inheritance: [{
                        content: "<th><span>Name</span></th>",
                        position: "after",
                        view_id: 55,
                        xpath: "/t/table/thead/tr/th[3]"
                      },
                      {
                        content: "<td><span t-field=\"o.child.name\"></span></td>",
                        position: "after",
                        view_id: 55,
                        xpath: "/t/table/tbody/tr/td[5]"
                      },
                      {
                        content: "<td></td>",
                        position: "after",
                        view_id: 55,
                        xpath: "/t/table/tbody/tr[1]/td[4]"
                      }
                ],
            },
        ];


        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();

            // drag and drop a Text component, which should trigger a view edition
            var $table = rem.$('iframe').contents().find('table');

            for (testIndex; testIndex < tests.length; testIndex++) {
                var test = tests[testIndex];
                var $buildingBlock = rem.$(test.buildingBlockSelector);
                var $target = $table.find(test.selector);
                $target.css('border','1px solid black'); // makes debugging easier
                testUtils.dragAndDrop($buildingBlock, $target, {position: test.position});
                var $nearestHook = $table.find('.o_web_studio_nearest_hook');
                assert.strictEqual($nearestHook.length, test.nearestHookNumber, test.text + ' (nearestHook number)');
                if (test.onDragAndDrop) {
                    test.onDragAndDrop($table);
                }
                $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="child"]').trigger('click');
                $('.o_web_studio_field_modal .o_field_selector_item[data-name="name"]').trigger('click');
                $('.o_web_studio_field_modal .btn-primary').trigger('click');
            }
            rem.destroy();
            done();
        });
    }));

    QUnit.test('drag & drop block "Accounting Total"', loadIframeCss(function (assert, done) {
        assert.expect(1);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>Content</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });
        this.models['account.invoice'] = 'Invoice';
        this.data['account.invoice'] = {
            fields: {
                name: { string: "Name", type: "char"},
            },
            records: [],
        };
        var templateData = {
            dataOeContext: '{"o": "account.invoice"}'
        };
        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, [{
                        content:
                            '<div class="row">' +
                                '<div class="col-5">' +
                                    '<table class="table table-sm o_report_block_total">' +
                                        '<t t-set="total_currency_id" t-value="o.currency_id"/>' +
                                        '<t t-set="total_amount_total" t-value="o.amount_total"/>' +
                                        '<t t-set="total_amount_untaxed" t-value="o.amount_untaxed"/>' +
                                        '<t t-set="total_amount_by_groups" t-value="o.amount_by_group"/>' +
                                        '<tr t-if="total_amount_untaxed != total_amount_total">' +
                                            '<th>Subtotal</th>' +
                                            '<td colspan="2" class="text-right">' +
                                                '<span t-esc="total_amount_untaxed" t-options="{\'widget\': \'monetary\', \'display_currency\': total_currency_id}"/>' +
                                            '</td>' +
                                        '</tr>' +
                                        '<t t-foreach="total_amount_by_groups" t-as="total_amount_by_group">' +
                                            '<tr>' +
                                                '<th><span t-esc="total_amount_by_group[0]"/></th>' +
                                                '<td><small t-if="len(total_amount_by_group) > 4 and total_amount_by_group[2] and total_amount_untaxed != total_amount_by_group[2]">on <span t-esc="total_amount_by_group[4]"/></small></td>' +
                                                '<td class="text-right">' +
                                                    '<span t-esc="total_amount_by_group[3]"/>' +
                                                '</td>' +
                                            '</tr>' +
                                        '</t>' +
                                        '<t t-if="total_amount_by_groups is None and total_amount_total != total_amount_untaxed">' +
                                            '<tr>' +
                                                '<th>Taxes</th>' +
                                                '<td></td>' +
                                                '<td class="text-right">' +
                                                    '<span t-esc="total_amount_total - total_amount_untaxed" t-options="{\'widget\': \'monetary\', \'display_currency\': total_currency_id}"/>' +
                                                '</td>' +
                                            '</tr>' +
                                        '</t>' +
                                        '<tr class="border-black">' +
                                            '<th>Total</th>' +
                                            '<td colspan="2" class="text-right">' +
                                                '<span t-esc="total_amount_total" t-options="{\'widget\': \'monetary\', \'display_currency\': total_currency_id}"/>' +
                                            '</td>' +
                                        '</tr>' +
                                    '</table>' +
                                '</div>' +
                                '<div class="col-5 offset-2"></div>' +
                            '</div>',
                        position: "after",
                        view_id: 55,
                        xpath: "/t/div"
                    }], 'Should send the xpath node with the content');
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();
            var $main = rem.$('iframe').contents().find('main');

            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_field_type_container:eq(2) .o_web_studio_component:contains(Subtotal & Total)');
            testUtils.dragAndDrop($text, $main, {position: {top: 50, left: 100}});
            $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
            $('.o_web_studio_field_modal .btn-primary').trigger('click');

            rem.destroy();
            done();
        });
    }));

    QUnit.test('edit block "Accounting Total"', loadIframeCss(function (assert, done) {
        assert.expect(2);

        var initialDebugMode = config.debug;
        // show all nodes in the sidebar
        config.debug = true;

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-5">' +
                                '<table class="table table-sm o_report_block_total">' +
                                    '<t t-set="total_currency_id" t-value="o.child"/>' +
                                    '<t t-set="total_amount_total" t-value="o.child"/>' +
                                    '<t t-set="total_amount_untaxed" t-value="o.child"/>' +
                                    '<t t-set="total_amount_by_groups" t-value="o.child"/>' +
                                    '<tr>' +
                                        '<th>Subtotal</th>' +
                                        // not need to add content for this test
                                    '</tr>' +
                                '</table>' +
                            '</div>' +
                            '<div class="col-5 offset-2"></div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });
        var templateData = {
            dataOeContext: '{"o": "model.test"}',
            o: {
                currency_id: 1,
                amount_total: 55,
                amount_untaxed: 55,
                amount_by_group: null,
            }
        };
        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, [{
                        content: '<attribute name="t-value">o.child_bis</attribute>',
                        position: "attributes",
                        view_id: 55,
                        xpath: "/t/div/div/table//t[@t-set='total_currency_id']"
                    }], 'Should send the xpath node with the content');
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('iframe').contents().find('main th').click();
            var $card = rem.$('.o_web_studio_sidebar .card:has(.o_text:contains(table))');
            $card.find('[data-toggle="collapse"]').click();

            assert.strictEqual($card.find('.o_web_studio_report_currency_id .o_field_selector_chain_part').text().replace(/\s+/g, ' '),
                ' o (Model Test) Child ', 'Should display the t-foreach value');

            rem.$('.o_web_studio_report_currency_id .o_field_selector').trigger('focusin');
            rem.$('.o_web_studio_report_currency_id .o_field_selector_item[data-name="child_bis"]').trigger('click');
            rem.$('.o_web_studio_report_currency_id .o_field_selector_close').trigger('click');

            rem.destroy();
            config.debug = initialDebugMode;
            done();
        });
    }));

    QUnit.test('drag & drop block "Data table"', loadIframeCss(function (assert, done) {
        assert.expect(2);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>Content</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });
        var templateData = {
            dataOeContext: '{"o": "model.test"}'
        };
        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, [{
                        content:
                            '<table class="table o_report_block_table">' +
                                '<thead>' +
                                    '<tr>' +
                                        '<th><span>Name</span></th>' +
                                    '</tr>' +
                                '</thead>' +
                                '<tbody>' +
                                    '<tr t-foreach="o.children" t-as="table_line">' +
                                        '<td><span t-field="table_line.display_name"/></td>' +
                                    '</tr>' +
                                '</tbody>' +
                            '</table>',
                        position: "after",
                        view_id: 55,
                        xpath: "/t/div"
                    }], 'Should send the xpath node with the content');
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();
            var $main = rem.$('iframe').contents().find('main');

            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_component:contains(Data table)');
            testUtils.dragAndDrop($text, $main, {position: {top: 50, left: 300}});
            $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
            $('.o_web_studio_field_modal .btn-primary').trigger('click');

            assert.strictEqual($('.o_technical_modal h4:contains(Alert)').length, 1, "Should display an alert because the selected field is wrong");

            $('.o_technical_modal:contains(Alert) .btn-primary').trigger('click');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="children"]').trigger('click');
            $('.o_web_studio_field_modal .btn-primary').trigger('click');

            rem.destroy();
            done();
        });
    }));

    QUnit.test('drag & drop block "Address"', function (assert) {
        assert.expect(1);
        var done = assert.async();

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch: '<kikou><t t-name="template1"/></kikou>',
        });

        var templateData = {
            dataOeContext: '{"o": "model.test"}',
        };

        // the address block requires a many2one to res.partner
        this.data['model.test'].fields.partner = {
            string: "Partner", type: 'many2one', relation: 'res.partner', 'searchable': true,
        };

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {},
            reportHTML: studioTestUtils.getReportHTML(this.templates, templateData),
            reportViews: studioTestUtils.getReportViews(this.templates, templateData),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, [{
                        content:
                            '<div class="row address">' +
                                '<div class="col-5"></div>' +
                                '<div class="col-5 offset-2">' +
                                    "<div t-field=\"o.partner\" t-options-widget=\"'contact'\"/>" +
                                '</div>' +
                            '</div>',
                        position: "inside",
                        view_id: 42,
                        xpath: "/t/html/body/div/main/div",
                    }], 'Should send the xpath node with the content');
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('.o_web_studio_sidebar .o_web_studio_sidebar_header div[name="new"]').click();
            var $page = rem.$('iframe').contents().find('.page');

            var $text = rem.$('.o_web_studio_sidebar .o_web_studio_component:contains(Address)');
            testUtils.dragAndDrop($text, $page, {position: 'inside'});
            $('.o_web_studio_field_modal .o_field_selector').trigger('focusin');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="o"]').trigger('click');
            $('.o_web_studio_field_modal .o_field_selector_item[data-name="partner"]').trigger('click');
            $('.o_web_studio_field_modal .btn-primary').trigger('click');

            rem.destroy();
            done();
        });
    });

    QUnit.test('edit text', function (assert) {
        var done = assert.async();
        assert.expect(2);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<span>taratata <strong>bo</strong></span>' +
                    '</t>' +
                '</kikou>',
        });
        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    var operation = _.last(args.operations);
                    if (!operation) {
                        return $.Deferred().reject();
                    }
                    assert.deepEqual(operation.inheritance, [{
                        content: '<span>toto <small>titi</small></span>',
                        position: "replace",
                        view_id: 55,
                        xpath: "/t/span"
                    }], 'Should replace the title content');
                    return $.Deferred().reject();
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('iframe').contents().find('span').click();

            var $editable = rem.$('.o_web_studio_sidebar .card.o_web_studio_active .note-editable');

            assert.strictEqual($editable.html(), 'taratata <strong>bo</strong>', 'Should display the text content');

            $editable.focusIn();
            $editable.html('toto <small>titi</small>');
            $editable.find('span').focusIn();
            $editable.keydown();
            $editable.blur();

            rem.destroy();
            done();
        });
    });

    QUnit.test('open XML editor after modification', function (assert) {
        var done = assert.async();
        assert.expect(7);

        // the XML editor lazy loads its libs and its templates so its start
        // method is monkey-patched to know when the widget has started
        var XMLEditorDef = $.Deferred();
        testUtils.patch(ace, {
            start: function () {
                return this._super.apply(this, arguments).then(function () {
                    XMLEditorDef.resolve();
                });
            },
        });
        var initialDebugMode = config.debug;
        // the XML editor button is only available in debug mode
        config.debug = true;

        var self = this;
        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<div class="row">' +
                            '<div class="col-12">' +
                                '<span>First span</span>' +
                            '</div>' +
                        '</div>' +
                    '</t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            data: this.data,
            models: this.models,
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {
                report_name: 'awesome_report',
            },
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    // directly apply the operation on the view
                    self.templates[1].arch = '<kikou>' +
                        '<t t-name="template1">' +
                            '<div class="row">' +
                                '<div class="col-12">' +
                                    '<span>hello</span>' +
                                '</div>' +
                            '</div>' +
                        '</t>' +
                    '</kikou>';

                    return $.when({
                        report_html: studioTestUtils.getReportHTML(self.templates),
                        views: studioTestUtils.getReportViews(self.templates),
                    });
                } else if (route === '/web_editor/get_assets_editor_resources') {
                    assert.strictEqual(args.key, self.templates[0].view_id, "the correct view should be fetched");
                    return $.when({
                        views: [{
                            active: true,
                            arch: self.templates[0].arch,
                            id: self.templates[0].view_id,
                            inherit_id: false,
                        }],
                        scss: [],
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        rem.editorIframeDef.then(function () {
            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"First span",
                "the iframe should be rendered");

            // click to edit a span and change the text (should trigger the report edition)
            rem.$('iframe').contents().find('span:contains(First)').click();
            rem.$('.o_web_studio_sidebar .o_web_studio_active textarea[name="text"]').val("hello").trigger('input');

            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"hello",
                "the iframe should have been updated");
            var $newTextarea = rem.$('.o_web_studio_sidebar .o_web_studio_active textarea[name="text"]');
            assert.strictEqual($newTextarea.length, 1,
                "there should still be a textarea to edit the node text");
            assert.strictEqual($newTextarea.val(), "hello",
                "the Text component should have been updated");
            assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"hello",
                "the iframe should be re-rendered");

            // switch tab
            rem.$('.o_web_studio_sidebar_header [name="report"]').click();
            // open the XML editor
            rem.$('.o_web_studio_sidebar .o_web_studio_xml_editor').click();

            XMLEditorDef.then(function () {
                assert.strictEqual(rem.$('iframe').contents().find('.page').text(),"hello",
                    "the iframe should be re-rendered");

                config.debug = initialDebugMode;
                testUtils.unpatch(ace);
                rem.destroy();
                done();
            });
        });
    });

    QUnit.test('automatic undo of correct operation', function (assert) {
        var self = this;
        var done = assert.async();
        assert.expect(5);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1"><span>First span</span></t>' +
                '</kikou>',
        });

        var rem = studioTestUtils.createReportEditorManager({
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {},
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    nbEdit++;
                    switch (nbEdit) {
                        case 1:
                            assert.strictEqual(args.operations.length, 1);
                            assert.deepEqual(args.operations[0].inheritance, [{
                                content: '<attribute name="class" separator=" " add="o_bold"/>',
                                position: 'attributes',
                                view_id: 55,
                                xpath: '/t/span',
                            }]);
                            // first rpc that we will make fail
                            return firstDef;
                        case 2:
                            // NB: undo RPC and second op RPC are dropped by
                            // MutexedDropPrevious
                            assert.strictEqual(args.operations.length, 2,
                                "should have undone the first operation");
                            assert.deepEqual(args.operations[0].inheritance, [{
                                content: '<attribute name="class" separator=" " add="o_italic"/>',
                                position: 'attributes',
                                view_id: 55,
                                xpath: '/t/span',
                            }]);
                            assert.deepEqual(args.operations[1].inheritance, [{
                                content: '<attribute name="class" separator=" " add="o_underline"/>',
                                position: 'attributes',
                                view_id: 55,
                                xpath: '/t/span',
                            }]);
                            // second rpc that succeeds
                            return $.when({
                                report_html: studioTestUtils.getReportHTML(self.templates),
                                views: studioTestUtils.getReportViews(self.templates),
                            });
                        case 3:
                            assert.ok(false, "should not edit a third time");
                    }

                }
                return this._super.apply(this, arguments);
            },
        });

        var nbEdit = 0;
        var firstDef = $.Deferred();
        rem.editorIframeDef.then(function () {
            rem.$('iframe').contents().find('span:contains(First span)').click();

            // trigger a modification
            rem.$('.o_web_studio_sidebar .card:eq(1) .o_web_studio_text_decoration button[data-property="bold"]').click();

            // trigger a second modification before the first one has finished
            rem.$('.o_web_studio_sidebar .card:eq(1) .o_web_studio_text_decoration button[data-property="italic"]').click();

            // trigger a third modification before the first one has finished
            rem.$('.o_web_studio_sidebar .card:eq(1) .o_web_studio_text_decoration button[data-property="underline"]').click();

            // make the first op fail (will release the MutexedDropPrevious)
            firstDef.reject();

            rem.destroy();
            done();
        });
    });

    QUnit.test('automatic undo on AST error', function (assert) {
        var self = this;
        var done = assert.async();
        assert.expect(4);

        this.templates.push({
            key: 'template1',
            view_id: 55,
            arch:
                '<kikou>' +
                    '<t t-name="template1">' +
                        '<span>Kikou</span>' +
                    '</t>' +
                '</kikou>',
        });
        var nbEdit = 0;
        var rem = studioTestUtils.createReportEditorManager({
            env: {
                modelName: 'kikou',
                ids: [42, 43],
                currentId: 42,
            },
            report: {},
            reportHTML: studioTestUtils.getReportHTML(this.templates),
            reportViews: studioTestUtils.getReportViews(this.templates),
            reportMainViewID: 42,
            mockRPC: function (route, args) {
                if (route === '/web_studio/edit_report_view') {
                    nbEdit++;
                    if (nbEdit === 1) {
                        assert.strictEqual(args.operations.length, 1, "the operation is correctly applied");
                        // simulate an AST error
                        return $.when({
                            report_html: {
                                error: 'AST error',
                                message: 'You have probably done something wrong',
                            },
                        });
                    }
                    if (nbEdit === 2) {
                        assert.strictEqual(args.operations.length, 0, "the operation should be undone");
                        return $.when({
                            report_html: studioTestUtils.getReportHTML(self.templates),
                            views: studioTestUtils.getReportViews(self.templates),
                        });
                    }
                }
                return this._super.apply(this, arguments);
            },
            services: {
                notification: NotificationService.extend({
                    notify: function (params) {
                        assert.step(params.type);
                    }
                }),
            },
        });

        rem.editorIframeDef.then(function () {
            rem.$('iframe').contents().find('span:contains(Kikou)').click();

            // trigger a modification that will fail
            rem.$('.o_web_studio_sidebar .card:eq(1) .o_web_studio_text_decoration button[data-property="bold"]').click();

            assert.verifySteps(['warning'], "should have undone the operation");

            rem.destroy();
            done();
        });
    });

});

});

});
