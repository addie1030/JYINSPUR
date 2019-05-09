odoo.define('web_studio.ReportEditorSidebar_tests', function (require) {
"use strict";

var config = require('web.config');
var testUtils = require('web.test_utils');

var studioTestUtils = require('web_studio.testUtils');

QUnit.module('Studio', {}, function () {

    QUnit.module('ReportEditorSidebar', {
        beforeEach: function () {
            this.data = {
                'report.paperformat': {
                    fields: {
                        display_name: {string: "Name", type: "char"},
                    },
                    records: [{
                        id: 42,
                        display_name: 'My Awesome Format',
                    }],
                },
                'res.groups': {
                    fields: {
                        display_name: {string: "Name", type: "char"},
                    },
                    records: [{
                        id: 6,
                        display_name: 'Group6',
                    }, {
                        id: 7,
                        display_name: 'Group7',
                    }],
                },
                'x_mymodel': {
                    fields: {
                        display_name: {string: "Name", type: "char"},
                    },
                },
            };

            this.widgetsOptions = {
                image: {},
                integer: {},
                text: {},
            };
        },
    }, function () {
        QUnit.test("basic rendering", function (assert) {
            assert.expect(5);

            var sidebar = studioTestUtils.createSidebar({
                state: { mode: 'report' },
                report: {},
            });

            assert.ok(sidebar.$('.o_web_studio_sidebar_header [name="report"]').hasClass('active'),
                "the report tab should be active");
            assert.ok(sidebar.$('.o_web_studio_sidebar_header [name="options"]').hasClass('inactive'),
                "the options tab should be inactive");

            testUtils.intercept(sidebar, 'sidebar_tab_changed', function (ev) {
                assert.step(ev.data.mode);
            });
            sidebar.$('.o_web_studio_sidebar_header [name="new"]').click();
            assert.verifySteps(['new'], "the sidebar should be updated");

            sidebar.$('.o_web_studio_sidebar_header [name="options"]').click();
            assert.verifySteps(['new'], "one should not be able to select options");

            sidebar.destroy();
        });

        QUnit.test("'Report' tab behaviour", function (assert) {
            assert.expect(6);

            var sidebar = studioTestUtils.createSidebar({
                data: this.data,
                state: { mode: 'report' },
                report: {
                    name: 'Kikou',
                },
            });

            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_header > .active').attr('name'), "report",
                "the 'Report' tab should be active");
            assert.strictEqual(sidebar.$('input[name="name"]').val(), "Kikou",
                "the report name should be displayed");

            testUtils.intercept(sidebar, 'studio_edit_report', function (ev) {
                if (ev.data.name) {
                    assert.deepEqual(ev.data, { name: "wow_report" });
                } else if ('paperformat_id' in ev.data) {
                    paperformatValues.push(ev.data);
                } else if (ev.data.groups_id) {
                    assert.deepEqual(ev.data, { groups_id: [7] });
                }
            });
            // edit report name
            sidebar.$('input[name="name"]').val("wow_report").trigger('change');

            // edit the report paperformat
            var paperformatValues = [];
            var $dropdown1 = sidebar.$('[name="paperformat_id"] input').autocomplete('widget');
            sidebar.$('[name="paperformat_id"] input').click();
            $dropdown1.find('li:contains(My Awesome Format)').mouseenter().click();
            assert.deepEqual(paperformatValues, [{ paperformat_id: 42 }]);

            // remove the report paperformat
            sidebar.$('[name="paperformat_id"] input').val('').trigger('keyup').trigger('focusout');
            assert.deepEqual(paperformatValues, [{ paperformat_id: 42 }, { paperformat_id: false }]);

            // edit groups
            var $dropdown2 = sidebar.$('[name="groups_id"] input').autocomplete('widget');
            sidebar.$('[name="groups_id"] input').click();
            $dropdown2.find('li:contains(Group7)').mouseenter().click();

            sidebar.destroy();
        });

        QUnit.test("'Add' tab behaviour", function (assert) {
            assert.expect(2);

            var sidebar = studioTestUtils.createSidebar({
                state: { mode: 'new' },
            });

            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_header > .active').attr('name'), "new",
                "the 'Add' tab should be active");
            assert.ok(sidebar.$('.ui-draggable').length,
                "there should be draggable components");

            sidebar.destroy();
        });

        QUnit.test("basic 'Options' tab behaviour", function (assert) {
            assert.expect(4);

            var node = {
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                    },
                    tag: 'span',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                state: {
                    mode: 'properties',
                    nodes: [node],
                },
            });

            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_header > .active').attr('name'), "options",
                "the 'Options' tab should be active");
            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .collapse').length, 1,
                "there should be one node in the accordion");
            assert.ok(sidebar.$('.o_web_studio_sidebar_content .collapse').hasClass('show'),
                "the node should be expanded by default");

            // remove the element
            testUtils.intercept(sidebar, 'element_removed', function (ev) {
                assert.deepEqual(ev.data.node, node.node);
            });
            sidebar.$('.o_web_studio_sidebar_content .collapse .o_web_studio_remove').click();

            sidebar.destroy();
        });

        QUnit.test("'Options' tab with multiple nodes", function (assert) {
            var done = assert.async();
            assert.expect(9);

            var node1 = {
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                    },
                    tag: 'span',
                },
            };

            var node2 = {
                node: {
                    attrs: {
                        'data-oe-id': '40',
                        'data-oe-xpath': '/t/t',
                    },
                    tag: 'div',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                state: {
                    mode: 'properties',
                    nodes: [node1, node2],
                },
            });

            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_header > .active').attr('name'), "options",
                "the 'Options' tab should be active");
            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .card').length, 2,
                "there should be one node in the accordion");
            assert.ok(sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(span)) .collapse').hasClass('show'),
                "the 'span' node should be expanded by default");
            assert.ok(!sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(div)) .collapse').hasClass('show'),
                "the 'div' node shouldn't be expanded");
            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .o_web_studio_accordion > .card:last .card-header').text().trim(), "span",
                "the last node should be the span");

            // expand the first node
            sidebar.$('.o_web_studio_sidebar_content .o_web_studio_accordion > .card:first [data-toggle="collapse"]').click();
            // BS4 collapsing is asynchronous
            setTimeout(function () {
                assert.ok(!sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(span)) .collapse').hasClass('show'),
                    "the 'span' node should have been closed");
                assert.ok(sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(div)) .collapse').hasClass('show'),
                    "the 'div' node should be expanded");

                // reexpand the second node
                sidebar.$('.o_web_studio_sidebar_content .o_web_studio_accordion > .card:last [data-toggle="collapse"]').click();
                setTimeout(function () {
                    assert.ok(sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(span)) .collapse').hasClass('show'),
                        "the 'span' node should be expanded again");
                    assert.ok(!sidebar.$('.o_web_studio_sidebar_content .card:has(.o_text:contains(div)) .collapse').hasClass('show'),
                        "the 'div' node shouldn't be expanded anymore");

                    done();
                    sidebar.destroy();
                }, 0);
            },0);
        });

        QUnit.test("'Options' tab with layout component can be expanded", function (assert) {
            assert.expect(3);

            var node = {
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                    },
                    tag: 'span',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                state: {
                    mode: 'properties',
                    nodes: [node],
                },
            });

            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .collapse').length, 1,
                "there should be one node in the accordion");
            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .o_web_studio_layout').length, 1,
                "there should be a layout component");

            // expand options
            sidebar.$('.o_web_studio_sidebar_content .o_web_studio_layout .expandLayout').click();
            assert.strictEqual(sidebar.$('.o_web_studio_sidebar_content .o_web_studio_layout .o_web_studio_margin').length, 1,
                "there should be a margin section in the layout component");

            sidebar.destroy();
        });

        QUnit.test("'Options' tab with layout component can be expanded on open ", function (assert) {
            assert.expect(1);

            var node = {
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                    },
                    tag: 'span',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                state: {
                    mode: 'properties',
                    nodes: [node],
                },
                previousState: {
                    "42/t/t/div": { 'layout': { showAll: true } }, // opens the layout expanded
                },
            });

            assert.equal(sidebar.$('.o_web_studio_width:visible').length, 1);

            sidebar.destroy();
        });

        QUnit.test("'Options' tab with widget selection (tOptions) component", function (assert) {
            assert.expect(4);

            var node = {
                context: {
                    'doc': 'x_mymodel',
                },
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                        't-field': 'doc.id',
                        't-options-widget': '"text"',
                    },
                    tag: 'span',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                state: {
                    mode: 'properties',
                    nodes: [node],
                },
                widgetsOptions: this.widgetsOptions,
            });

            assert.strictEqual(sidebar.$('.o_web_studio_tfield_fieldexpression').length, 1,
                "the t-field component should be displayed");
            assert.strictEqual(sidebar.$('.o_web_studio_toption_widget').length, 1,
                "the t-options component should be displayed");
            assert.strictEqual(sidebar.$('.o_web_studio_toption_widget select').text().replace(/\s/g, ''), "imageintegertext",
                "all widgets should be selectable");
            assert.strictEqual(sidebar.$('.o_web_studio_toption_widget select').val(), "text",
                "the correct widget should be selected");

            sidebar.destroy();
        });

        QUnit.test("'Options' tab with FieldSelector does not flicker", function (assert) {
            assert.expect(3);
            var done = assert.async();
            var def = $.Deferred();

            var node = {
                context: {
                    'doc': 'x_mymodel',
                },
                node: {
                    attrs: {
                        'data-oe-id': '42',
                        'data-oe-xpath': '/t/t/div',
                        't-field': 'doc.id',
                        't-options-widget': '"text"',
                    },
                    context: {
                        'doc': 'x_mymodel',
                    },
                    tag: 'span',
                },
            };
            var sidebar = studioTestUtils.createSidebar({
                data: this.data,
                models: {
                    'x_mymodel': 'My Model',
                },
                state: {
                    mode: 'properties',
                    nodes: [node],
                },
                widgetsOptions: this.widgetsOptions,
                mockRPC: function (route, args) {
                    if (args.model === 'x_mymodel' && args.method === 'fields_get') {
                        // Block the 'read' call
                        var result = this._super.apply(this, arguments);
                        return $.when(def).then(_.constant(result));
                    }
                    return this._super.apply(this, arguments);
                },
            });

            assert.strictEqual($('.o_web_studio_tfield_fieldexpression').length, 0,
                "the sidebar should wait its components to be rendered before its insertion");

            // release the fields_get
            def.resolve();

            $.when(def).then(function () {
                assert.strictEqual($('.o_web_studio_tfield_fieldexpression').length, 1,
                    "the t-field component should be displayed");
                assert.strictEqual(sidebar.$('.o_web_studio_tfield_fieldexpression .o_field_selector_value').text().replace(/\s/g, ''), "doc(MyModel)ID",
                    "the field chain should be correctly displayed");

                done();
                sidebar.destroy();
            });
        });

        QUnit.test('Various layout changes', function (assert) {
            // this test is a combinaison of multiple tests, to avoid copy
            // pasting multiple times de sidebar create/intercept/destroy

            var layoutChangeNode = {
                attrs: {
                    'data-oe-id': '99',
                    'data-oe-xpath': '/t/t/div',
                },
                tag: 'span',
            };
            var nodeWithAllLayoutPropertiesSet = {
                tag: "span",
                attrs: {
                    //width: "1",
                    style: "margin-top:2px;width:1px;margin-right:3px;margin-bottom:4px;margin-left:5px;",
                    class: "o_bold o_italic h3 bg-gamma text-beta o_underline",
                    'data-oe-id': '99',
                    'data-oe-xpath': '/t/t/div',
                }
            };

            var nodeWithAllLayoutPropertiesFontAndBackgroundSet = {
                tag: "span",
                attrs: {
                    //width: "1",
                    style: "margin-top:2px;margin-right:3px;width:1px;margin-bottom:4px;margin-left:5px;background-color:#00FF00;color:#00FF00",
                    class: "o_bold o_italic h3 o_underline",
                    'data-oe-id': '99',
                    'data-oe-xpath': '/t/t/div',
                }
            };
            var layoutChangesOperations = [
                {
                testName: "add a margin top in pixels",
                nodeToUse: layoutChangeNode,
                eventToTrigger: "change",
                sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-top"]',
                valueToPut: "42",
                expectedRPC: {
                    inheritance: [{
                        content: "<attribute name=\"style\" separator=\";\" add=\"margin-top:42px\"/>",
                        position: "attributes",
                        view_id: 99,
                        xpath: "/t/t/div"
                    }]
                }
                }, {
                    testName: "add a margin bottom in pixels",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-bottom"]',
                    valueToPut: "42",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"margin-bottom:42px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "add a margin left in pixels",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-left"]',
                    valueToPut: "42",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"margin-left:42px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "add a margin right in pixels",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-right"]',
                    valueToPut: "42",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"margin-right:42px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "add a width",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_width input',
                    valueToPut: "42",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"width:42px;display:inline-block\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "add a class",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_classes input',
                    valueToPut: "new_class",
                    expectedRPC: {
                        new_attrs: {
                        class: "new_class"
                        },
                        type: "attributes",
                    },
                }, {
                    testName: "set the heading level",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_font_size select',
                    valueToPut: "h3",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" add=\"h3\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                }, {
                    testName: "set the background color to a theme color",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_background_colorpicker button[data-color="gamma"]',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" add=\"bg-gamma\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                }, {
                    testName: "set the background color to a standard color",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_background_colorpicker button[data-value="#00FF00"]',
                    valueToPut: "h3",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"background-color:#00FF00\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                }, {
                    testName: "set the font color to a theme color",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_font_colorpicker button[data-color="gamma"]',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" add=\"text-gamma\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                }, {
                    testName: "set the font color to a standard color",
                    nodeToUse: layoutChangeNode,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_font_colorpicker button[data-value="#00FF00"]',
                    valueToPut: "h3",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" add=\"color:#00FF00\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                },{
                testName: "remove margin top in pixels",
                nodeToUse: nodeWithAllLayoutPropertiesSet,
                eventToTrigger: "change",
                sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-top"]',
                valueToPut: "",
                expectedRPC: {
                    inheritance: [{
                        content: "<attribute name=\"style\" separator=\";\" remove=\"margin-top:2px\"/>",
                        position: "attributes",
                        view_id: 99,
                        xpath: "/t/t/div"
                    }]
                }
                }, {
                    testName: "remove a margin bottom in pixels",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-bottom"]',
                    valueToPut: "",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"margin-bottom:4px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "remove a margin left in pixels",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-left"]',
                    valueToPut: "",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"margin-left:5px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "remove a margin right in pixels",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_margin [data-margin="margin-right"]',
                    valueToPut: "",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"margin-right:3px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "remove the width",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_width input',
                    valueToPut: "",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"width:1px\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    }
                }, {
                    testName: "remove a class",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_classes input',
                    valueToPut: "o_bold o_italic bg-gamma text-beta o_underline",
                    expectedRPC: {
                        new_attrs: {
                            class: "o_bold o_italic bg-gamma text-beta o_underline"
                        },
                        type: "attributes",
                    },
                },{
                    testName: "unset the heading level",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "change",
                    sidebarOperationInputSelector: '.o_web_studio_font_size select',
                    valueToPut: "",
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" remove=\"h3\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                },  {
                    testName: "unset the background color to a theme color",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_background_colorpicker .o_web_studio_reset_color',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" remove=\"bg-gamma\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                },{
                    testName: "unset the background color to a standard color",
                    nodeToUse: nodeWithAllLayoutPropertiesFontAndBackgroundSet,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_background_colorpicker .o_web_studio_reset_color',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"background-color:#00FF00\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                },  {
                    testName: "unset the font color to a theme color",
                    nodeToUse: nodeWithAllLayoutPropertiesSet,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_font_colorpicker .o_web_studio_reset_color',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"class\" separator=\" \" remove=\"text-beta\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                }, {
                    testName: "unset the font color to a standard color",
                    nodeToUse: nodeWithAllLayoutPropertiesFontAndBackgroundSet,
                    eventToTrigger: "click",
                    sidebarOperationInputSelector: '.o_web_studio_colors .o_web_studio_font_colorpicker button.o_web_studio_reset_color',
                    expectedRPC: {
                        inheritance: [{
                            content: "<attribute name=\"style\" separator=\";\" remove=\"color:#00FF00\"/>",
                            position: "attributes",
                            view_id: 99,
                            xpath: "/t/t/div"
                        }]
                    },
                },
            ];

            // there is one assert by operation
            assert.expect(layoutChangesOperations.length);

            var initialDebugMode = config.debug;
            // show 'class' in the sidebar
            config.debug = true;

            _.each(layoutChangesOperations, function (changeOperation) {
                var node = {
                    node: changeOperation.nodeToUse,
                };
                var sidebar = studioTestUtils.createSidebar({
                    state: {
                        mode: 'properties',
                        nodes: [node],
                    },
                    previousState: {
                        "99/t/t/div": { 'layout': { showAll: true } }, // opens the layout expanded
                    },
                });

                testUtils.intercept(sidebar, 'view_change', function (ev) {
                    assert.deepEqual(ev.data.operation, changeOperation.expectedRPC, changeOperation.testName);
                });
                sidebar.$(changeOperation.sidebarOperationInputSelector)
                    .val(changeOperation.valueToPut)
                    .trigger(changeOperation.eventToTrigger);

                sidebar.destroy();
            });

            config.debug = initialDebugMode;
        });
    });

});

});
