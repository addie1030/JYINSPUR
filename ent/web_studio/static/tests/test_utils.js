odoo.define('web_studio.testUtils', function (require) {
"use strict";

var dom = require('web.dom');
var QWeb = require('web.QWeb');
var testUtils = require('web.test_utils');
var utils = require('web.utils');
var Widget = require('web.Widget');

var ReportEditor = require('web_studio.ReportEditor');
var ReportEditorManager = require('web_studio.ReportEditorManager');
var ReportEditorSidebar = require('web_studio.ReportEditorSidebar');
var ViewEditorManager = require('web_studio.ViewEditorManager');

/**
 * Test Utils
 *
 * In this module, we define some utility functions to create Studio objects.
 */

/**
 * Create a ReportEditorManager widget.
 *
 * @param {Object} params
 * @return {ReportEditorManager}
 */
function createReportEditor (params) {
    var Parent = Widget.extend({
        start: function () {
            var self = this;
            this._super.apply(this, arguments).then(function () {
                var $studio = $.parseHTML(
                    "<div class='o_web_studio_client_action'>" +
                            "<div class='o_web_studio_editor_manager o_web_studio_report_editor_manager'/>" +
                        "</div>" +
                    "</div>");
                self.$el.append($studio);
            });
        },
    });
    var parent = new Parent();
    var selector = params.debug ? 'body' : '#qunit-fixture';
    parent.appendTo(selector);
    testUtils.addMockEnvironment(parent, _.extend(params, {
        // TODO
    }));

    var editor = new ReportEditor(parent, params);
    // override 'destroy' of editor so that it calls 'destroy' on the parent
    // instead
    editor.destroy = function () {
        // remove the override to properly destroy editor and its children
        // when it will be called the second time (by its parent)
        delete editor.destroy;
        // TODO: call super?
        parent.destroy();
    };
    editor.appendTo(parent.$('.o_web_studio_editor_manager'));
    return editor;
}

/**
 * Create a ReportEditorManager widget.
 *
 * @param {Object} params
 * @return {ReportEditorManager}
 */
function createReportEditorManager (params) {
    var parent = new StudioEnvironment();
    testUtils.addMockEnvironment(parent, params);

    var rem = new ReportEditorManager(parent, params);
    // also destroy to parent widget to avoid memory leak
    rem.destroy = function () {
        delete rem.destroy;
        parent.destroy();
    };

    var fragment = document.createDocumentFragment();
    var selector = params.debug ? 'body' : '#qunit-fixture';
    if (params.debug) {
        $('body').addClass('debug');
    }
    parent.prependTo(selector);
    rem.appendTo(fragment).then(function () {
        // use dom.append to call on_attach_callback
        dom.append(parent.$('.o_web_studio_client_action'), fragment, {
            callbacks: [{widget: rem}],
            in_DOM: true,
        });
    });
    return rem;
}

/**
 * Create a sidebar widget.
 *
 * @param {Object} params
 * @return {ReportEditorSidebar}
 */
function createSidebar (params) {
    var Parent = Widget.extend({
        start: function () {
            var self = this;
            this._super.apply(this, arguments).then(function () {
                var $studio = $.parseHTML(
                    "<div class='o_web_studio_client_action'>" +
                            "<div class='o_web_studio_editor_manager o_web_studio_report_editor_manager'/>" +
                    "</div>");
                self.$el.append($studio);
            });
        },
    });
    var parent = new Parent();
    testUtils.addMockEnvironment(parent, params);

    var sidebar = new ReportEditorSidebar(parent, params);
    sidebar.destroy = function () {
        // remove the override to properly destroy sidebar and its children
        // when it will be called the second time (by its parent)
        delete sidebar.destroy;
        parent.destroy();
    };

    var selector = params.debug ? 'body' : '#qunit-fixture';
    if (params.debug) {
        $('body').addClass('debug');
    }
    parent.appendTo(selector);

    var fragment = document.createDocumentFragment();
    sidebar.appendTo(fragment).then(function () {
        sidebar.$el.appendTo(parent.$('.o_web_studio_editor_manager'));
    });
    return sidebar;
}

/**
 * Create a ViewEditorManager widget.
 *
 * @param {Object} params
 * @return {ViewEditorManager}
 */
function createViewEditorManager (params) {
    var parent = new StudioEnvironment();
    var mockServer = testUtils.addMockEnvironment(parent, params);
    var fieldsView = testUtils.fieldsViewGet(mockServer, params);
    if (params.viewID) {
        fieldsView.view_id = params.viewID;
    }
    var env = {
        modelName: params.model,
        ids: 'res_id' in params ? [params.res_id] : undefined,
        currentId: 'res_id' in params ? params.res_id : undefined,
        domain: params.domain || [],
        context: params.context || {},
        groupBy: params.groupBy || [],
    };
    var vem = new ViewEditorManager(parent, {
        fields_view: fieldsView,
        viewType: fieldsView.type,
        env: env,
        studio_view_id: params.studioViewID,
        chatter_allowed: params.chatter_allowed,
    });

    // also destroy to parent widget to avoid memory leak
    var originalDestroy = ViewEditorManager.prototype.destroy;
    vem.destroy = function () {
        vem.destroy = originalDestroy;
        parent.destroy();
    };

    var fragment = document.createDocumentFragment();
    var selector = params.debug ? 'body' : '#qunit-fixture';
    if (params.debug) {
        $('body').addClass('debug');
    }
    parent.prependTo(selector);
    vem.appendTo(fragment).then(function () {
        dom.append(parent.$('.o_web_studio_client_action'), fragment, {
            callbacks: [{widget: vem}],
            in_DOM: true,
        });
    });
    return vem;
}

/**
 * Renders a list of templates.
 *
 * @param {Array<Object>} templates
 * @param {Object} data
 * @param {String} [data.dataOeContext]
 * @returns {string}
 */
function getReportHTML (templates, data) {
    _brandTemplates(templates, data && data.dataOeContext);

    var qweb = new QWeb();
    _.each(templates, function (template) {
        qweb.add_template(template.arch);
    });
    var render = qweb.render('template0', data);
    return render;
}

/**
 * Builds the report views object.
 *
 * @param {Array<Object>} templates
 * @param {Object} [data]
 * @param {String} [data.dataOeContext]
 * @returns {Object}
 */
function getReportViews (templates, data) {
    _brandTemplates(templates, data && data.dataOeContext);

    var reportViews = {};
    _.each(templates, function (template) {
        reportViews[template.view_id] = {
            arch: template.arch,
            key: template.key,
            studio_arch: '</data>',
            studio_view_id: false,
            view_id: template.view_id,
        };
    });
    return reportViews;
}

/**
 * Brands (in place) a list of templates.
 *
 * @private
 * @param {Array<Object>} templates
 * @param {String} [dataOeContext]
 */
function _brandTemplates (templates, dataOeContext) {

    _.each(templates, function (template) {
        brandTemplate(template);
    });

    function brandTemplate (template) {
        var doc = $.parseXML(template.arch).documentElement;
        var rootNode = utils.xml_to_json(doc, true);
        brandNode([rootNode], rootNode, '');

        function brandNode (siblings, node, xpath) {
            // do not brand already branded nodes
            if (_.isObject(node) && !node.attrs['data-oe-id']) {
                if (node.tag !== 'kikou') {
                    xpath += ('/' + node.tag);
                    var index = _.filter(siblings, {tag: node.tag}).indexOf(node);
                    if (index > 0) {
                        xpath += '[' + index + ']';
                    }
                    node.attrs['data-oe-id'] = template.view_id;
                    node.attrs['data-oe-xpath'] = xpath;
                    node.attrs['data-oe-context'] = dataOeContext || '{}';
                }

                _.each(node.children, function (child) {
                    brandNode(node.children, child, xpath);
                });
            }
        }
        template.arch = utils.json_node_to_xml(rootNode);
    }
}

var StudioEnvironment = Widget.extend({
    className: 'o_web_client o_in_studio',
    start: function () {
        var self = this;
        this._super.apply(this, arguments).then(function () {
            // reproduce the DOM environment of Studio
            var $studio = $.parseHTML(
                "<div class='o_content'>" +
                    "<div class='o_web_studio_client_action'/>" +
                "</div>"
            );
            self.$el.append($studio);
        });
    },
});

return {
    createReportEditor: createReportEditor,
    createReportEditorManager: createReportEditorManager,
    createSidebar: createSidebar,
    createViewEditorManager: createViewEditorManager,
    getReportHTML: getReportHTML,
    getReportViews: getReportViews,
};

});
