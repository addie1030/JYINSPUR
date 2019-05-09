odoo.define('documents.documents_kanban_tests', function (require) {
"use strict";

var DocumentsKanbanView = require('documents.DocumentsKanbanView');

var mailTestUtils = require('mail.testUtils');

var concurrency = require('web.concurrency');
var relationalFields = require('web.relational_fields');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('Views');

QUnit.module('DocumentsKanbanView', {
    beforeEach: function () {
        this.data = {
            'ir.attachment': {
                fields: {
                    active: {string: "Active", type: 'boolean', default: true},
                    available_rule_ids: {string: "Rules", type: 'many2many', relation: 'documents.workflow.rule'},
                    file_size: {string: "Size", type: 'integer'},
                    folder_id: {string: "Folders", type: 'many2one', relation: 'documents.folder'},
                    lock_uid: {string: "Locked by", type: "many2one", relation: 'user'},
                    message_follower_ids: {string: "Followers", type: 'one2many', relation: 'mail.followers'},
                    message_ids: {string: "Messages", type: 'one2many', relation: 'mail.message'},
                    mimetype: {string: "Mimetype", type: 'char', default: ''},
                    name: {string: "Name", type: 'char', default: ' '},
                    owner_id: {string: "Owner", type: "many2one", relation: 'user'},
                    partner_id: {string: "Related partner", type: 'many2one', relation: 'user'},
                    public: {string: "Is public", type: 'boolean'},
                    res_id: {string: "Resource id", type: 'integer'},
                    res_model: {string: "Model (technical)", type: 'char'},
                    res_model_name: {string: "Resource model", type: 'char'},
                    res_name: {string: "Resource name", type: 'char'},
                    share_ids: {string: "Shares", type: "many2many", relation: 'documents.share'},
                    tag_ids: {string: "Tags", type: 'many2many', relation: 'documents.tag'},
                    type: {string: "Type", type: 'selection', selection: [['url', "URL"], ['binary', "File"]], default: 1},
                    url: {string: "Url", type: 'char'},
                    activity_ids: {string: 'Activities', type: 'one2many', relation: 'mail.activity',
                        relation_field: 'res_id'},
                    activity_state: {string: 'State', type: 'selection',
                        selection: [['overdue', 'Overdue'], ['today', 'Today'], ['planned', 'Planned']]},
                },
                records: [
                    {id: 1, name: 'yop', file_size: 30000, owner_id: 1, partner_id: 2,
                        public: true, res_id: 1, res_model: 'task', res_model_name: 'Task', activity_ids: [1,],
                        activity_state: 'today', res_name: 'Write specs', tag_ids: [1, 2], share_ids: [], folder_id: 1,
                        available_rule_ids: [1, 2]},
                    {id: 2, name: 'blip', file_size: 20000, owner_id: 2, partner_id: 2,
                        public: false, res_id: 2, res_model: 'task', res_model_name: 'Task',
                        res_name: 'Write tests', tag_ids: [2], share_ids: [], folder_id: 1, available_rule_ids: [1]},
                    {id: 3, name: 'gnap', file_size: 15000, lock_uid: 3, owner_id: 2, partner_id: 1,
                        public: false, res_id: 2, res_model: 'task', res_model_name: 'Task',
                        res_name: 'Write doc', tag_ids: [1, 2, 5], share_ids: [], folder_id: 1, available_rule_ids: [1, 2, 3]},
                    {id: 4, name: 'burp', file_size: 10000, mimetype: 'image/png', owner_id: 1, partner_id: 3,
                        public: true, res_id: 1, res_model: 'order', res_model_name: 'Sale Order',
                        res_name: 'SO 0001', tag_ids: [], share_ids: [], folder_id: 1, available_rule_ids: []},
                    {id: 5, name: 'zip', file_size: 40000, lock_uid: 1, owner_id: 2, partner_id: 2,
                        public: false, res_id: 3, res_model: false, res_model_name: false,
                        res_name: false, tag_ids: [], share_ids: [], folder_id: 1, available_rule_ids: [1, 2]},
                    {id: 6, name: 'pom', file_size: 70000, partner_id: 3,
                        public: true, res_id: 1, res_model: 'order', res_model_name: 'Sale order',
                        res_name: 'SO 0003', tag_ids: [], share_ids: [], folder_id: 2, available_rule_ids: []},
                    {id: 7, name: 'zoup', file_size: 20000, mimetype: 'image/png',
                        owner_id: 3, partner_id: 3, public: true, res_id: false, res_model: false,
                        res_model_name: false, res_name: false, tag_ids: [], share_ids: [], folder_id: false, available_rule_ids: []},
                    {id: 8, active: false, name: 'wip', file_size: 70000, owner_id: 3, partner_id: 3,
                        public: true, res_id: 1, res_model: 'order', res_model_name: 'Sale Order',
                        res_name: 'SO 0003', tag_ids: [], share_ids: [], folder_id: 1, available_rule_ids: []},
                    {id: 9, active: false, name: 'zorro', file_size: 20000, mimetype: 'image/png',
                        owner_id: 3, partner_id: 3, public: true, res_id: false, res_model: false,
                        res_model_name: false, res_name: false, tag_ids: [], share_ids: [], folder_id: 1, available_rule_ids: []},
                ],
            },
            user: {
                fields: {
                    display_name: {string: "Name", type: 'char'},
                },
                records: [
                    {id: 1, display_name: 'Hazard'},
                    {id: 2, display_name: 'Lukaku'},
                    {id: 3, display_name: 'De Bruyne'},
                ],
            },
            task: {
                fields: {},
                get_formview_id: function () {
                    return $.when();
                },
            },
            'documents.folder': {
                fields: {
                    name: {string: 'Name', type: 'char'},
                    parent_folder_id: {string: 'Parent Folder', type: 'many2one', relation: 'documents.folder'},
                    description: {string: 'Description', type:'text'},
                },
                records: [
                        {id: 1, name: 'Folder1', description: '_F1-test-description_', parent_folder_id: false},
                        {id: 2, name: 'Folder2', parent_folder_id: false},
                        {id: 3, name: 'Folder3', parent_folder_id: 1},
                ],
            },
            'documents.tag': {
                fields: {},
                group_by_documents: function () {
                    return $.when([{
                      facet_id: 2,
                      facet_name: 'Priority',
                      facet_sequence: 10,
                      facet_tooltip: 'A priority tooltip',
                      tag_id: 5,
                      tag_name: 'No stress',
                      tag_sequence: 10,
                      __count: 0,
                    }, {
                      facet_id: 1,
                      facet_name: 'Status',
                      facet_sequence: 11,
                      facet_tooltip: 'A Status tooltip',
                      tag_id: 2,
                      tag_name: 'Draft',
                      tag_sequence: 10,
                      __count: 0,
                    }, {
                      facet_id: 1,
                      facet_name: 'Status',
                      facet_sequence: 11,
                      facet_tooltip: 'A Status tooltip',
                      tag_id: 1,
                      tag_name: 'New',
                      tag_sequence: 11,
                      __count: 0,
                    }]);
                },
            },
            'documents.share': {
                fields: {
                    name: {string: 'Name', type: 'char'},
                },
                records: [
                    {id: 1, name: 'Share1'},
                    {id: 2, name: 'Share2'},
                    {id: 3, name: 'Share3'},
                ],
                create_share: function () {
                    return $.when();
                },
            },
            'documents.workflow.rule': {
                fields: {
                    display_name: {string: 'Name', type: 'char'},
                    note: {string: 'Tooltip', type: 'char'},
                },
                records: [
                    {id: 1, display_name: 'Convincing AI not to turn evil', note:'Racing for AI Supremacy'},
                    {id: 2, display_name: 'Follow the white rabbit'},
                    {id: 3, display_name: 'Entangling superstrings'},
                ],
            },
            'mail.followers': {
                fields: {},
                records: [],
            },
            'mail.message': {
                fields: {
                    body: {string: "Body", type: 'char'},
                    model: {string: "Related Document Model", type: 'char'},
                    res_id: {string: "Related Document ID", type: 'integer'},
                },
                records: [],
            },
            'mail.activity': {
                fields: {
                    activity_type_id: { string: "Activity type", type: "many2one", relation: "mail.activity.type" },
                    create_uid: { string: "Assigned to", type: "many2one", relation: 'partner' },
                    create_user_id: { string: "Creator", type: "many2one", relation: 'partner' },
                    display_name: { string: "Display name", type: "char" },
                    date_deadline: { string: "Due Date", type: "date" },
                    user_id: { string: "Assigned to", type: "many2one", relation: 'partner' },
                    state: {
                        string: 'State',
                        type: 'selection',
                        selection: [['overdue', 'Overdue'], ['today', 'Today'], ['planned', 'Planned']],
                    },
                },
            },
            'mail.activity.type': {
                fields: {
                    name: { string: "Name", type: "char" },
                },
                records: [
                    { id: 1, name: "Type 1" },
                    { id: 2, name: "Type 2" },
                ],
            },
        };
    },
}, function () {
    QUnit.test('basic rendering', function (assert) {
        assert.expect(12);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // check view layout
        assert.strictEqual(kanban.$('> div').length, 3,
            "should have 3 columns");
        assert.strictEqual(kanban.$('> .o_documents_selector').length, 1,
            "should have a 'documents selector' column");
        assert.strictEqual(kanban.$('> .o_kanban_view').length, 1,
            "should have a 'classical kanban view' column");
        assert.ok(kanban.$('.o_kanban_view').hasClass('o_documents_kanban_view'),
            "should have classname 'o_documents_kanban_view'");
        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length, 5,
            "should have 5 records in the renderer");
        assert.strictEqual(kanban.$('.o_kanban_record:first .o_record_selector').length, 1,
            "should have a 'selected' button");
        assert.strictEqual(kanban.$('> .o_documents_inspector').length, 1,
            "should have a 'documents inspector' column");

        // check control panel buttons
        assert.strictEqual(kanban.$buttons.find('.btn-primary').length, 3,
            "should have three primary buttons");
        assert.strictEqual(kanban.$buttons.find('.btn-primary:first').text().trim(), 'Upload',
            "should have a primary 'Upload' button");
        assert.strictEqual(kanban.$buttons.find('button.o_documents_kanban_url').length, 1,
            "should allow to save a URL");
        assert.strictEqual(kanban.$buttons.find('button.o_documents_kanban_request').text().trim(), 'Request Document',
            "should have a primary 'request' button");
        assert.strictEqual(kanban.$buttons.find('button.btn-secondary').text().trim(), 'Share',
            "should have a secondary 'Share' button");

        kanban.destroy();
    });

    QUnit.test('can select records by clicking on the select icon', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        var $firstRecord = kanban.$('.o_kanban_record:first');
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should not be selected");
        $firstRecord.find('.o_record_selector').click();
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        var $thirdRecord = kanban.$('.o_kanban_record:nth(2)');
        assert.ok(!$thirdRecord.hasClass('o_record_selected'),
            "third record should not be selected");
        $thirdRecord.find('.o_record_selector').click();
        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should be selected");

        $firstRecord.find('.o_record_selector').click();
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should not be selected");
        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should be selected");

        kanban.destroy();
    });

    QUnit.test('can select records by clicking on them', function (assert) {
        assert.expect(5);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_record.o_record_selected').length, 0,
            "no record should be selected");

        var $firstRecord = kanban.$('.o_kanban_record:first');
        $firstRecord.click();
        assert.strictEqual(kanban.$('.o_kanban_record.o_record_selected').length, 1,
            "one record should be selected");
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        var $thirdRecord = kanban.$('.o_kanban_record:nth(2)');
        $thirdRecord.click();
        assert.strictEqual(kanban.$('.o_kanban_record.o_record_selected').length, 1,
            "one record should be selected");
        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should be selected");

        kanban.destroy();
    });

    QUnit.test('can unselect a record', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_record.o_record_selected').length, 0,
            "no record should be selected");

        var $firstRecord = kanban.$('.o_kanban_record:first');
        $firstRecord.click();
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        $firstRecord.click();
        assert.strictEqual(kanban.$('.o_kanban_record.o_record_selected').length, 0,
            "no more record should be selected");

        kanban.destroy();
    });

    QUnit.test('can select records with keyboard navigation', function (assert) {
        assert.expect(4);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<button name="some_method" type="object"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                execute_action: function () {
                    assert.ok(false, "should not trigger an 'execute_action' event");
                },
            },
        });

        var $firstRecord = kanban.$('.o_kanban_record:first');
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should not be selected");
        $firstRecord.focus().trigger($.Event('keydown', {
            keyCode: $.ui.keyCode.ENTER,
            which: $.ui.keyCode.ENTER,
        }));
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        var $thirdRecord = kanban.$('.o_kanban_record:nth(2)');
        $thirdRecord.focus().trigger($.Event('keydown', {
            keyCode: $.ui.keyCode.ENTER,
            which: $.ui.keyCode.ENTER,
        }));
        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should be selected");
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should no longer be selected");

        kanban.destroy();
    });

    QUnit.test('can multi select records with shift and ctrl', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<button name="some_method" type="object"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });
        var $firstRecord = kanban.$('.o_kanban_record:first');
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should not be selected");
        $firstRecord.focus().trigger($.Event('keydown', {
            keyCode: $.ui.keyCode.ENTER,
            which: $.ui.keyCode.ENTER,
        }));
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        var $thirdRecord = kanban.$('.o_kanban_record:nth(2)');
        $thirdRecord.focus().trigger($.Event('keydown', {
            keyCode: $.ui.keyCode.ENTER,
            which: $.ui.keyCode.ENTER,
            shiftKey: true,
        }));
        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should be selected (shift)");
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should still be selected (shift)");

        $firstRecord.focus().trigger($.Event('keydown', {
            keyCode: $.ui.keyCode.ENTER,
            which: $.ui.keyCode.ENTER,
            ctrlKey: true,
        }));

        assert.ok($thirdRecord.hasClass('o_record_selected'),
            "third record should still be selected (ctrl)");
        assert.ok(!$firstRecord.hasClass('o_record_selected'),
            "first record should no longer be selected (ctrl)");

        kanban.destroy();
    });

    QUnit.test('only visible selected records are kept after a reload', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<button name="some_method" type="object"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(yop) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(burp) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(blip) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 3,
            "should have 3 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 3,
            "should show 3 document previews in the DocumentsInspector");

        kanban.reload({domain: [['name', '=', 'burp']]});

        assert.strictEqual(kanban.$('.o_record_selected').length, 1,
            "should have 1 selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 1,
            "should show 1 document preview in the DocumentsInspector");

        kanban.reload({domain: []});

        assert.strictEqual(kanban.$('.o_record_selected').length, 1,
            "should have 1 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 1,
            "should show 1 document previews in the DocumentsInspector");

        kanban.destroy();
    });

    QUnit.test('selected records are kept when a button is clicked', function (assert) {
        assert.expect(7);

        var self = this;
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<button name="some_method" type="object"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'read' && args.model === 'ir.attachment') {
                    assert.deepEqual(args.args[0], [1],
                        "should read the clicked record");
                }
                return this._super.apply(this, arguments);
            },
            intercepts: {
                execute_action: function (ev) {
                    assert.strictEqual(ev.data.action_data.name, 'some_method',
                        "should call the correct method");
                    self.data['ir.attachment'].records[0].name = 'yop changed';
                    ev.data.on_closed();
                },
            },
        });

        kanban.$('.o_kanban_record:contains(yop) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(burp) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(blip) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 3,
            "should have 3 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 3,
            "should show 3 document previews in the DocumentsInspector");

        kanban.$('.o_kanban_record:contains(yop) button').click();

        assert.strictEqual(kanban.$('.o_record_selected:contains(yop changed)').length, 1,
            "should have re-rendered the updated record");
        assert.strictEqual(kanban.$('.o_record_selected').length, 3,
            "should still have 3 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 3,
            "should still show 3 document previews in the DocumentsInspector");

        kanban.destroy();
    });

    QUnit.test('can share current domain', function (assert) {
        assert.expect(2);

        var domain = [['owner_id', '=', 2]];
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            domain: domain,
            mockRPC: function (route, args) {
                if (args.method === 'create_share') {
                    assert.deepEqual(args.args, [{
                        domain: domain.concat([
                            ['folder_id', '=', 1], ['res_model', 'in', ['task']],
                        ]),
                        folder_id: 1,
                        tag_ids: [[6, 0, []]],
                        type: 'domain',
                    }]);
                }
                return this._super.apply(this, arguments);
            },
        });

        // filter on 'task' in the DocumentsSelector
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_record:not(.o_kanban_ghost)').length, 2,
            "should have 2 records in the renderer");

        kanban.$buttons.find('.o_documents_kanban_share').click();

        kanban.destroy();
    });

    QUnit.test('can upload from URL', function (assert) {
        assert.expect(1);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                do_action: function (ev) {
                    assert.deepEqual(ev.data.action, "documents.action_url_form", "should open the URL form");
                },
            },
        });

        kanban.$buttons.find('button.o_documents_kanban_url').click();

        kanban.destroy();
    });

    QUnit.test('can Request a file', function (assert) {
        assert.expect(1);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                do_action: function (ev) {
                    assert.deepEqual(ev.data.action, "documents.action_request_form", "should open the Request form");
                },
            },
        });

        kanban.$buttons.find('button.o_documents_kanban_request').click();

        kanban.destroy();
    });

    QUnit.test('can render without folder', function (assert) {
        assert.expect(1);

        this.data['documents.folder'].records = [];
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length, 1,
            "should have 1 record in the renderer (the one which is not in a folder)");

        kanban.destroy();
    });

    QUnit.module('DocumentsInspector');

    QUnit.test('documents inspector with no document selected', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });
        assert.strictEqual(kanban.$('.o_documents_inspector_preview').text().replace(/\s+/g, ''),
            '_F1-test-description_', "should display the current folder description");
        assert.strictEqual(kanban.$('.o_documents_inspector_info .o_inspector_value:first').text().trim(),
            '5', "should display the correct number of documents");
        assert.strictEqual(kanban.$('.o_documents_inspector_info .o_inspector_value:nth(1)').text().trim(),
            '0.12 MB', "should display the correct size");

        kanban.destroy();
    });

    QUnit.test('documents inspector with selected documents', function (assert) {
        assert.expect(5);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select a first document
        kanban.$('.o_kanban_record:first .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_documents_inspector_info .o_selection_size').length, 0,
            "should not display the number of selected documents (because only 1)");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 1,
            "should show a preview of the selected document");
        assert.ok(kanban.$('.o_documents_inspector_preview .o_document_preview').hasClass('o_documents_single_preview'),
            "should have the 'o_documents_single_preview' className");

        // select a second document
        kanban.$('.o_kanban_record:nth(2) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_selection_size').text().trim(),
            '2 documents selected', "should display the correct number of selected documents");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 2,
            "should show a preview of the selected documents");

        kanban.destroy();
    });

    QUnit.test('documents inspector limits preview to 4 documents', function (assert) {
        assert.expect(2);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select five documents
        kanban.$('.o_kanban_record:nth(0) .o_record_selector').click();
        kanban.$('.o_kanban_record:nth(1) .o_record_selector').click();
        kanban.$('.o_kanban_record:nth(2) .o_record_selector').click();
        kanban.$('.o_kanban_record:nth(3) .o_record_selector').click();
        kanban.$('.o_kanban_record:nth(4) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_selection_size').text().trim(),
            '5 documents selected', "should display the correct number of selected documents");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 4,
            "should only show a preview of 4 selected documents");

        kanban.destroy();
    });

    QUnit.test('documents inspector shows selected records of the current page', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban limit="2"><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 1,
            "should have 1 selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 1,
            "should show 1 document preview in the DocumentsInspector");

        kanban.pager.$('.o_pager_next').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 0,
            "should have no selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 0,
            "should show no document preview in the DocumentsInspector");

        kanban.pager.$('.o_pager_previous').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 0,
            "should have no selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 0,
            "should show no document preview in the DocumentsInspector");

        kanban.destroy();
    });

    QUnit.test('document inspector: document preview', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(yop)').click();

        assert.strictEqual(kanban.$('.o_document_preview img').length, 0,
            "should not have a clickable image");

        kanban.$('.o_kanban_record:contains(burp)').click();

        assert.strictEqual(kanban.$('.o_viewer_content').length, 0,
            "should not have a document preview");
        assert.strictEqual(kanban.$('.o_document_preview img').length, 1,
            "should have a clickable image");

        kanban.$('.o_document_preview img').click();

        assert.strictEqual(kanban.$('.o_viewer_content').length, 1,
            "should have a document preview");
        assert.strictEqual(kanban.$('.o_close_btn').length, 1,
            "should have a close button");

        kanban.$('.o_close_btn').click();

        assert.strictEqual(kanban.$('.o_viewer_content').length, 0,
            "should not have a document preview after pdf exit");

        kanban.destroy();
    });

    QUnit.test('document inspector: open preview while modifying document', function (assert) {
        assert.expect(2);

        var def = $.Deferred();

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    return def;
                }
                return this._super.apply(this, arguments);
            },
        });
        kanban.$('.o_kanban_record:contains(burp)').click();
        kanban.$('input[name=name]').val("foo").trigger('input');

        kanban.$('.o_document_preview img').click();
        assert.strictEqual(kanban.$('.o_viewer_content').length, 0,
            "should not have a document preview");

        def.resolve();
        assert.strictEqual(kanban.$('.o_viewer_content').length, 1,
            "should have a document preview");

        kanban.$('.o_close_btn').click();
        kanban.destroy();
    });

    QUnit.test('document inspector: can delete records', function (assert) {
        assert.expect(5);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            domain: [['active', '=', false]],
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'unlink') {
                    assert.deepEqual(args.args[0], [8, 9],
                        "should unlink the selected records");
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:contains(wip) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(zorro) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 2,
            "should have 2 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 2,
            "should show 2 document previews in the DocumentsInspector");

        kanban.$('.o_documents_inspector_info .o_inspector_delete').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 0,
            "should have no selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 0,
            "should show 0 document preview in the DocumentsInspector");

        kanban.destroy();
    });

    QUnit.test('document inspector: can archive records', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    assert.deepEqual(args.args, [[1, 4], {active: false}],
                        "should archive the selected records");
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:contains(yop) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(burp) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 2,
            "should have 2 selected records");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 2,
            "should show 2 document previews in the DocumentsInspector");

        kanban.$('.o_documents_inspector_info .o_inspector_archive').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 0,
            "should have no selected record");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview .o_document_preview').length, 0,
            "should show no document preview in the DocumentsInspector");

        kanban.reload({active: false});

        assert.strictEqual(kanban.$('.o_kanban_view .o_record_selected').length, 0,
            "should have no selected archived record");

        kanban.destroy();
    });

    QUnit.test('document inspector: can share records', function (assert) {
        assert.expect(2);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'create_share') {
                    assert.deepEqual(args.args, [{
                        attachment_ids: [[6, 0, [1, 2]]],
                        folder_id: 1,
                        type: 'ids',
                    }]);
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:contains(yop) .o_record_selector').click();
        kanban.$('.o_kanban_record:contains(blip) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 2,
            "should have 2 selected records");

        kanban.$('.o_documents_inspector_info .o_inspector_share').click();

        kanban.destroy();
    });

    QUnit.test('document inspector: locked records', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            session: {
                uid: 1,
            },
        });

        // select a record that is locked by ourself
        kanban.$('.o_kanban_record:contains(zip)').click();

        assert.ok(kanban.$('.o_inspector_lock').hasClass('o_locked'),
            "this attachment should be locked");
        assert.notOk(kanban.$('.o_inspector_lock').is(':disabled'),
            "lock button should not be disabled");
        assert.notOk(kanban.$('.o_inspector_replace').is(':disabled'),
            "replace button should not be disabled");

        // select a record that is locked by someone else
        kanban.$('.o_kanban_record:contains(gnap)').click();

        assert.ok(kanban.$('.o_inspector_lock').hasClass('o_locked'),
            "this attachment should be locked as well");
        assert.ok(kanban.$('.o_inspector_replace').is(':disabled'),
            "replace button should be disabled");
        assert.ok(kanban.$('.o_inspector_archive').is(':disabled'),
            "archive button should be disabled");

        kanban.destroy();
    });

    QUnit.test('document inspector: can (un)lock records', function (assert) {
        assert.expect(5);

        var self = this;
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            session: {
                uid: 1,
            },
            mockRPC: function (route, args) {
                if (args.method === 'toggle_lock') {
                    assert.deepEqual(args.args, [1], "should call method for the correct record");
                    var record = _.findWhere(self.data['ir.attachment'].records, {id: 1});
                    record.lock_uid = record.lock_uid ? false : 1;
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:contains(yop)').click();

        assert.notOk(kanban.$('.o_inspector_lock').hasClass('o_locked'),
            "this attachment should not be locked");

        // lock the record
        kanban.$('.o_inspector_lock').click();

        assert.ok(kanban.$('.o_inspector_lock').hasClass('o_locked'),
            "this attachment should be locked");


        // unlock the record
        kanban.$('.o_inspector_lock').click();

        assert.notOk(kanban.$('.o_inspector_lock').hasClass('o_locked'),
            "this attachment should not be locked anymore");

        kanban.destroy();
    });

    QUnit.test('document inspector: document info with one document selected', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(yop)').click();

        assert.strictEqual(kanban.$('.o_field_widget[name=name]').val(),
            'yop', "should correctly display the name");
        assert.strictEqual(kanban.$('.o_field_widget[name=owner_id] input').val(),
            'Hazard', "should correctly display the owner");
        assert.strictEqual(kanban.$('.o_field_widget[name=partner_id] input').val(),
            'Lukaku', "should correctly display the related partner");
        assert.strictEqual(kanban.$('.o_field_many2one .o_external_button:visible').length, 0,
            "should not display the external button in many2ones");
        assert.strictEqual(kanban.$('.o_inspector_model_name').text(),
            ' Task', "should correctly display the resource model");
        assert.strictEqual(kanban.$('.o_inspector_object_name').text(),
            'Write specs', "should correctly display the resource name");

        kanban.destroy();
    });

    QUnit.test('document inspector: update document info with one document selected', function (assert) {
        assert.expect(6);
        var done = assert.async();

        var M2O_DELAY = relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY;
        relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY = 0;

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<field name="owner_id"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    assert.deepEqual(args.args, [[1], {owner_id: 3}],
                        "should save the change directly");
                }
                return this._super.apply(this, arguments);
            },
        });

        var $firstRecord = kanban.$('.o_kanban_record:first');
        assert.strictEqual($firstRecord.text(), 'yopHazard',
            "should display the correct owner");

        $firstRecord.click();
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");

        // change m2o value
        var $ownerM2O = kanban.$('.o_field_many2one[name=owner_id] input');
        $ownerM2O.val('De Bruyne').trigger('keydown');
        concurrency.delay(0).then(function () {
            $ownerM2O.autocomplete('widget').find('a').first().click();

            $firstRecord = kanban.$('.o_kanban_record:first');
            assert.strictEqual($firstRecord.text(), 'yopDe Bruyne',
                "should have updated the owner");
            assert.ok($firstRecord.hasClass('o_record_selected'),
                "first record should still be selected");
            assert.strictEqual(kanban.$('.o_field_many2one[name=owner_id] input').val(), 'De Bruyne',
                "should display the new value in the many2one");

            relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY = M2O_DELAY;
            kanban.destroy();
            done();
        });
    });

    QUnit.test('document inspector: document info with several documents selected', function (assert) {
        assert.expect(7);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select two records with same m2o value
        var $blip = kanban.$('.o_kanban_record:contains(blip)');
        var $gnap = kanban.$('.o_kanban_record:contains(gnap)');
        $blip.click();
        $gnap.find('.o_record_selector').click();
        assert.ok($blip.hasClass('o_record_selected'),
            "blip record should be selected");
        assert.ok($gnap.hasClass('o_record_selected'),
            "gnap record should be selected");

        assert.strictEqual(kanban.$('.o_field_many2one[name=owner_id] input').val(),
            'Lukaku', "should display the correct m2o value");
        assert.strictEqual(kanban.$('.o_field_many2one .o_external_button:visible').length, 0,
            "should not display the external button in many2one");

        // select a third record with another m2o value
        var $yop = kanban.$('.o_kanban_record:contains(yop)');
        $yop.find('.o_record_selector').click();
        assert.ok($yop.hasClass('o_record_selected'),
            "yop record should be selected");

        assert.strictEqual(kanban.$('.o_field_many2one[name=owner_id] input').val(),
            'Multiple values', "should display 'Multiple values'");
        assert.strictEqual(kanban.$('.o_field_many2one .o_external_button:visible').length, 0,
            "should not display the external button in many2one");

        kanban.destroy();
    });

    QUnit.test('document inspector: update document info with several documents selected', function (assert) {
        assert.expect(10);
        var done = assert.async();

        var M2O_DELAY = relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY;
        relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY = 0;

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<field name="owner_id"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    assert.deepEqual(args.args, [[1, 2], {owner_id: 3}],
                        "should save the change directly");
                }
                return this._super.apply(this, arguments);
            },
        });

        var $firstRecord = kanban.$('.o_kanban_record:first');
        assert.strictEqual($firstRecord.text(), 'yopHazard',
            "should display the correct owner (record 1)");
        var $secondRecord = kanban.$('.o_kanban_record:nth(1)');
        assert.strictEqual($secondRecord.text(), 'blipLukaku',
            "should display the correct owner (record 2)");

        $firstRecord.click();
        $secondRecord.find('.o_record_selector').click();
        assert.ok($firstRecord.hasClass('o_record_selected'),
            "first record should be selected");
        assert.ok($secondRecord.hasClass('o_record_selected'),
            "second record should be selected");

        // change m2o value for both records
        var $ownerM2O = kanban.$('.o_field_many2one[name=owner_id] input');
        $ownerM2O.val('De Bruyne').trigger('keydown');
        concurrency.delay(0).then(function () {
            $ownerM2O.autocomplete('widget').find('a').first().click();

            $firstRecord = kanban.$('.o_kanban_record:first');
            assert.strictEqual($firstRecord.text(), 'yopDe Bruyne',
                "should have updated the owner of first record");
            $secondRecord = kanban.$('.o_kanban_record:nth(1)');
            assert.strictEqual($secondRecord.text(), 'blipDe Bruyne',
                "should have updated the owner of second record");
            assert.ok($firstRecord.hasClass('o_record_selected'),
                "first record should still be selected");
            assert.ok($secondRecord.hasClass('o_record_selected'),
                "second record should still be selected");
            assert.strictEqual(kanban.$('.o_field_many2one[name=owner_id] input').val(), 'De Bruyne',
                "should display the new value in the many2one");

            relationalFields.FieldMany2One.prototype.AUTOCOMPLETE_DELAY = M2O_DELAY;
            kanban.destroy();
            done();
        });
    });

    QUnit.test('document inspector: update info: handle concurrent updates', function (assert) {
        assert.expect(11);

        var def = $.Deferred();
        var nbWrite = 0;
        var value;
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                var result = this._super.apply(this, arguments);
                if (args.method === 'write') {
                    assert.step('write');
                    nbWrite++;
                    assert.deepEqual(args.args, [[1], {name: value}],
                        "should correctly save the changes");
                    if (nbWrite === 1) {
                        return def.then(_.constant(result));
                    }
                }
                return result;
            },
        });

        assert.strictEqual(kanban.$('.o_kanban_record:first').text(), 'yop',
            "should display the correct filename");
        kanban.$('.o_kanban_record:first').click();

        // change filename value of selected record (but block RPC)
        value = 'temp name';
        kanban.$('.o_field_char[name=name]').val(value).trigger('input');

        assert.strictEqual(kanban.$('.o_kanban_record:first').text(), 'yop',
            "should still display the old filename");

        // change filename value again (this RPC isn't blocked but must wait for
        // the first one to return)
        value = 'new name';
        kanban.$('.o_field_char[name=name]').val(value).trigger('input');

        assert.strictEqual(kanban.$('.o_kanban_record:first').text(), 'yop',
            "should still display the old filename");

        assert.step('resolve');
        def.resolve();

        assert.strictEqual(kanban.$('.o_kanban_record:first').text(), 'new name',
            "should still display the new filename in the record");
        assert.strictEqual(kanban.$('.o_field_char[name=name]').val(), 'new name',
            "should still display the new filename in the documents inspector");

        assert.verifySteps(['write', 'resolve', 'write']);

        kanban.destroy();
    });

    QUnit.test('document inspector: open resource', function (assert) {
        assert.expect(1);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                do_action: function (ev) {
                    assert.deepEqual(ev.data.action, {
                        res_id: 1,
                        res_model: 'task',
                        type: 'ir.actions.act_window',
                        views: [[false, 'form']],
                    }, "should open the resource in a form view");
                },
            },
        });

        kanban.$('.o_kanban_record:first').click();
        kanban.$('.o_documents_inspector .o_inspector_object_name').click();

        kanban.destroy();
    });

    QUnit.test('document inspector: display tags of selected documents', function (assert) {
        assert.expect(4);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 2,
            "should display the tags of the selected document");

        kanban.$('.o_kanban_record:nth(1) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 2,
            "should have 2 selected records");
        assert.strictEqual(kanban.$('.o_inspector_tag').length, 1,
            "should display the common tags between the two selected documents");
        assert.strictEqual(kanban.$('.o_inspector_tag').text().replace(/\s/g, ""), 'Status>Draft×',
            "should correctly display the content of the tag");

        kanban.destroy();
    });

    QUnit.test('document inspector: input to add tags is hidden if no tag to add', function (assert) {
        assert.expect(2);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(gnap)').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 3,
            "should have 3 tags");
        assert.strictEqual(kanban.$('.o_inspector_tags .o_inspector_tag_add').length, 0,
            "should not have an input to add tags");

        kanban.destroy();
    });

    QUnit.test('document inspector: remove tag', function (assert) {
        assert.expect(4);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    assert.deepEqual(args.args[0], [1, 3],
                        "should write on the selected records");
                    assert.deepEqual(args.args[1], {
                        tag_ids: [[3, 1]],
                    }, "should write the correct value");
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:first').click();
        kanban.$('.o_kanban_record:nth(2) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 2,
            "should display two tags");

        kanban.$('.o_inspector_tag:first .o_inspector_tag_remove').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 1,
            "should display one tag");

        kanban.destroy();
    });

    QUnit.test('document inspector: add a tag', function (assert) {
        assert.expect(5);
        var done = assert.async();

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'write') {
                    assert.deepEqual(args.args[0], [1, 2],
                        "should write on the selected records");
                    assert.deepEqual(args.args[1], {
                        tag_ids: [[4, 5]],
                    }, "should write the correct value");
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:first').click();
        kanban.$('.o_kanban_record:nth(1) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 1,
            "should display one tag");

        kanban.$('.o_inspector_tag_add').val('stress').trigger('keydown');
        concurrency.delay(0).then(function () {
            var $dropdown = kanban.$('.o_inspector_tag_add').autocomplete('widget');
            assert.strictEqual($dropdown.find('li').length, 1,
                "should have an entry in the autocomplete drodown");
            $dropdown.find('li > a').click();

            assert.strictEqual(kanban.$('.o_inspector_tag').length, 2,
                "should display two tags");

            kanban.destroy();
            done();
        });
    });

    QUnit.test('document inspector: do not suggest already linked tags', function (assert) {
        assert.expect(2);
        var done = assert.async();

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 2,
            "should display two tags");

        kanban.$('.o_inspector_tag_add').val('new').trigger('keydown');
        concurrency.delay(0).then(function () {
            var $dropdown = kanban.$('.o_inspector_tag_add').autocomplete('widget');
            assert.strictEqual($dropdown.find('li').length, 0,
                "should have no entry in the autocomplete drodown");

            kanban.destroy();
            done();
        });
    });

    QUnit.test('document inspector: tags: trigger a search on input clicked', function (assert) {
        assert.expect(1);
        var done = assert.async();

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        kanban.$('.o_inspector_tag_add').click();
        concurrency.delay(0).then(function () {
            var $dropdown = kanban.$('.o_inspector_tag_add').autocomplete('widget');
            assert.strictEqual($dropdown.find('li').length, 1,
                "should have an entry in the autocomplete drodown");

            kanban.destroy();
            done();
        });
    });

    QUnit.test('document inspector: unknown tags are hidden', function (assert) {
        assert.expect(1);

        this.data['ir.attachment'].records[0].tag_ids = [1, 2, 78];

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        assert.strictEqual(kanban.$('.o_inspector_tag').length, 2,
            "should not display the unknown tag");

        kanban.destroy();
    });

    QUnit.test('document inspector: display rules of selected documents', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:first').click();

        assert.strictEqual(kanban.$('.o_inspector_rule').length, 2,
            "should display the rules of the selected document");

        kanban.$('.o_kanban_record:nth(1) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_record_selected').length, 2,
            "should have 2 selected records");
        assert.strictEqual(kanban.$('.o_inspector_rule').length, 1,
            "should display the common rules between the two selected documents");
        assert.strictEqual(kanban.$('.o_inspector_rule .o_inspector_trigger_rule').length, 1,
            "should display the button for the common rule");
        assert.strictEqual(kanban.$('.o_inspector_rule').text().trim(), 'Convincing AI not to turn evil',
            "should correctly display the content of the rule");
        assert.strictEqual(kanban.$('.o_inspector_rule span').attr('title'), "Racing for AI Supremacy",
            "should correctly display the tooltip of the rule");

        kanban.destroy();
    });

    QUnit.test('document inspector: display rules of reloaded record', function (assert) {
        assert.expect(4);

        var self = this;
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                        '<button name="some_method" type="object"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                execute_action: function (ev) {
                    assert.strictEqual(ev.data.action_data.name, 'some_method',
                        "should call the correct method");
                    self.data['ir.attachment'].records[0].name = 'yop changed';
                    ev.data.on_closed();
                },
            },
        });

        kanban.$('.o_kanban_record:contains(yop)').click();

        assert.strictEqual(kanban.$('.o_inspector_rule span').text(),
            'Convincing AI not to turn evilFollow the white rabbit',
            "should correctly display the rules of the selected document");

        // click on the button to reload the record
        kanban.$('.o_kanban_record:contains(yop) button').click();

        assert.strictEqual(kanban.$('.o_record_selected:contains(yop changed)').length, 1,
            "should have reloaded the updated record");

        // unselect and re-select it (the record has been reloaded, so we want
        // to make sure its rules have been reloaded correctly as well)
        kanban.$('.o_kanban_record:contains(yop changed)').click();
        kanban.$('.o_kanban_record:contains(yop changed)').click();

        assert.strictEqual(kanban.$('.o_inspector_rule span').text(),
            'Convincing AI not to turn evilFollow the white rabbit',
            "should correctly display the rules of the selected document");

        kanban.destroy();
    });

    QUnit.test('document inspector: trigger rule actions on selected documents', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.model === 'documents.workflow.rule' && args.method === 'apply_actions') {
                    assert.deepEqual(args.args[0], [1],
                        "should execute actions on clicked rule");
                    assert.deepEqual(args.args[1], [1, 2],
                        "should execute actions on the selected records");
                    return $.when();
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:first').click();
        kanban.$('.o_kanban_record:nth(1) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_inspector_rule').length, 1,
            "should display the common rules between the two selected documents");
        kanban.$('.o_inspector_rule .o_inspector_trigger_rule').click();

        kanban.destroy();
    });

    QUnit.module('DocumentChatter');

    QUnit.test('document chatter: open and close chatter', function (assert) {
        assert.expect(7);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 0,
            "should not display any chatter");

        // select a record
        kanban.$('.o_kanban_record:contains(yop)').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 0,
            "should still not display any chatter");

        // open the chatter
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");
        assert.strictEqual(kanban.$('.o_documents_selector:visible').length, 1,
            "documents selector should still be visible");
        assert.strictEqual(kanban.$('.o_kanban_view:visible').length, 1,
            "kanban view should still be visible");
        assert.strictEqual(kanban.$('.o_documents_inspector:visible').length, 1,
            "documents inspector should still be visible");

        // close the chatter
        kanban.$('.o_document_close_chatter').click();
        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 0,
            "should no longer display the chatter");

        kanban.destroy();
    });

    QUnit.test('document chatter: fetch and display chatter messages', function (assert) {
        assert.expect(2);

        this.data['ir.attachment'].records[0].message_ids = [101, 102];
        this.data['mail.message'].records = [
            {body: "Message 1", id: 101, model: 'ir.attachment', res_id: 1},
            {body: "Message 2", id: 102, model: 'ir.attachment', res_id: 1},
        ];

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");
        assert.strictEqual(kanban.$('.o_document_chatter .o_thread_message').length, 2,
            "should display two messages in the chatter");

        kanban.destroy();
    });

    QUnit.test('document chatter: fetch and display followers', function (assert) {
        assert.expect(3);

        this.data['ir.attachment'].records[0].message_follower_ids = [301, 302];

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route) {
                if (route === '/mail/read_followers') {
                    return $.when({
                        followers: [
                            {id: 301, display_name: 'Follower 1'},
                            {id: 302, display_name: 'Follower 2'},
                        ],
                        subtypes: [],
                    });
                }
                return this._super.apply(this, arguments);
            },
        });

        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");
        assert.strictEqual(kanban.$('.o_document_chatter .o_followers').length, 1,
            "should display the follower widget");
        assert.strictEqual(kanban.$('.o_document_chatter .o_followers_count').text(), "2",
            "should have two followers");

        kanban.destroy();
    });

    QUnit.test('document chatter: render the activity button', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            intercepts: {
                do_action: function (ev) {
                    assert.deepEqual(ev.data.action, {
                        context: {
                            default_res_id: 1,
                            default_res_model: 'ir.attachment'
                        },
                        res_id: false,
                        res_model: 'mail.activity',
                        target: 'new',
                        type: 'ir.actions.act_window',
                        view_mode: 'form',
                        view_type: 'form',
                        views: [[false, 'form']]
                        },
                        "the activity button should trigger do_action with the correct args"
                    );
                },
            },
        });

        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        var $activityButton = kanban.$('.o_document_chatter .o_chatter_button_schedule_activity');
        assert.strictEqual($activityButton.length, 1,
            "should display the activity button");
        $activityButton.click();

        kanban.destroy();
    });

    QUnit.test('document chatter: render the activity button', function (assert) {
        assert.expect(8);

        this.data['mail.activity'].records = [{
            id: 1,
            display_name: "An activity",
            date_deadline: moment().format("YYYY-MM-DD"),
            state: "today",
            user_id: 2,
            create_user_id: 2,
            activity_type_id: 1,
        }];
        this.data.partner = {
            fields: {
                display_name: { string: "Displayed name", type: "char" },
                message_ids: {
                    string: "messages",
                    type: "one2many",
                    relation: 'mail.message',
                    relation_field: "res_id",
                },
                activity_ids: {
                    string: 'Activities',
                    type: 'one2many',
                    relation: 'mail.activity',
                    relation_field: 'res_id',
                },
            },
            records: [{
                id: 2,
                display_name: "first partner",
                message_ids: [],
                activity_ids: [],
            }]
        };
        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        assert.strictEqual(kanban.$('.o_mail_activity').length, 1,
            "should display the activity area");
        assert.strictEqual(kanban.$('#o_chatter_activity_info_1').length, 1,
            "should display an activity");
        assert.strictEqual(kanban.$('.o_activity_link:contains(Mark Done)').length, 1,
            "should display the activity mark done button");
        assert.strictEqual(kanban.$('.o_edit_activity').length, 1,
            "should display the activity Edit button");
        assert.strictEqual(kanban.$('.o_unlink_activity').length, 1,
            "should display the activity Cancel button");

        kanban.$('.o_kanban_record:contains(blip)').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        assert.strictEqual(kanban.$('#o_chatter_activity_info_1').length, 0,
            "should not display an activity");
        kanban.destroy();
    });

    QUnit.test('document chatter: can write messages in the chatter', function (assert) {
        assert.expect(7);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (args.method === 'message_get_suggested_recipients') {
                    return $.when({1: []});
                }
                if (args.method === 'message_post') {
                    assert.deepEqual(args.args, [1],
                        "should post message on correct record");
                    assert.strictEqual(args.kwargs.body, 'Some message',
                        "should post correct message");
                    return $.when(98);
                }
                if (args.method === 'message_format') {
                    assert.deepEqual(args.args, [[98]],
                        "should request message_format on correct message");
                    return $.when([{}]);
                }
                return this._super.apply(this, arguments);
            }
        });

        // select a record and open the chatter
        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");
        assert.strictEqual(kanban.$('.o_document_chatter .o_thread_composer').length, 0,
            "chatter composer should not be open");

        // open the composer
        kanban.$('.o_document_chatter .o_chatter_button_new_message').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_thread_composer').length, 1,
            "chatter composer should be open");

        // write and send a message
        kanban.$('.o_document_chatter .o_composer_text_field').val('Some message');
        kanban.$('.o_document_chatter .o_composer_button_send').click();

        assert.notOk(kanban.$('.o_chat_composer').hasClass('o_hidden'),
            "the composer should remain visible after a message is sent");

        kanban.destroy();
    });

    QUnit.test('document chatter: keep chatter open when switching between records', function (assert) {
        assert.expect(6);

        this.data['ir.attachment'].records[0].message_ids = [101, 102];
        this.data['mail.message'].records = [
            {body: "Message on 'yop'", id: 101, model: 'ir.attachment', res_id: 1},
            {body: "Message on 'blip'", id: 102, model: 'ir.attachment', res_id: 2},
        ];

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select a record and open the chatter
        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");
        assert.strictEqual(kanban.$('.o_document_chatter .o_thread_message').length, 1,
            "should display one message in the chatter");
        assert.strictEqual(kanban.$('.o_thread_message .o_thread_message_content').text().trim(),
            "Message on 'yop'", "should display the correct message");

        // select another record
        kanban.$('.o_kanban_record:contains(blip)').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should still display the chatter");
        assert.strictEqual(kanban.$('.o_document_chatter .o_thread_message').length, 1,
            "should display one message in the chatter");
        assert.strictEqual(kanban.$('.o_thread_message .o_thread_message_content').text().trim(),
            "Message on 'blip'", "should display the correct message");

        kanban.destroy();
    });

    QUnit.test('document chatter: keep chatter open after a reload', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select a record and open the chatter
        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        // reload with a domain
        kanban.reload({domain: [['id', '<', 4]]});

        assert.strictEqual(kanban.$('.o_record_selected').length, 1,
            "record should still be selected");
        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should still display the chatter");

        kanban.destroy();
    });

    QUnit.test('document chatter: close chatter when more than one record selected', function (assert) {
        assert.expect(2);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select a record and open the chatter
        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        // select another record alongside the first one
        kanban.$('.o_kanban_record:contains(blip) .o_record_selector').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 0,
            "should have closed the chatter");

        kanban.destroy();
    });

    QUnit.test('document chatter: close chatter when no more selected record', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            services: mailTestUtils.getMailServices(),
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // select a record and open the chatter
        kanban.$('.o_kanban_record:contains(yop)').click();
        kanban.$('.o_documents_inspector .o_inspector_open_chatter').click();

        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 1,
            "should display the chatter");

        // reload with a domain
        kanban.reload({domain: [['id', '>', 4]]});

        assert.strictEqual(kanban.$('.o_record_selected').length, 0,
            "no more record should be selected");
        assert.strictEqual(kanban.$('.o_document_chatter .o_chatter').length, 0,
            "should have closed the chatter");

        kanban.destroy();
    });

    QUnit.module('DocumentsSelector');

    QUnit.test('document selector: basic rendering', function (assert) {
        assert.expect(19);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_folders .o_documents_selector_header').text().trim(),
            'Folders', "should have a 'folders' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_folder').length, 3,
            "should have 3 folders");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_folder:visible').length, 2,
            "two of them should be visible");
        assert.strictEqual(kanban.$('.o_documents_inspector_preview').text().replace(/\s+/g, ''),
            '_F1-test-description_', "should display the first folder");

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_tags .o_documents_selector_header').text().trim(),
            'Tags', "should have a 'tags' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet').length, 2,
            "should have 2 facets");

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:first > header').text().trim(),
            'Priority', "the first facet should be 'Priority'");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:first > header').attr('title').trim(),
            'A priority tooltip', "the first facet have a tooltip");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last > header').text().trim(),
            'Status', "the last facet should be 'Status'");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last > header').attr('title').trim(),
            'A Status tooltip', "the last facet should be 'Status'");

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last .o_documents_selector_tag').length, 2,
            "should have 2 tags in the last facet");

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last .o_documents_selector_tag:first header').text().trim(),
            'Draft', "the first tag in the last facet should be 'Draft'");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last .o_documents_selector_tag:first header').attr('title').trim(),
            'A Status tooltip', "the first tag in the last facet have a tooltip");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last .o_documents_selector_tag:last header').text().trim(),
            'New', "the last tag in the last facet should be 'New'");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet:last .o_documents_selector_tag:last header').attr('title').trim(),
            'A Status tooltip', "the last tag in the last facet have a tooltip");

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_header').text().trim(),
            'Attached To', "should have an 'attached to' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_model').length, 3,
            "should have 3 types of models");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task]').text().replace(/\s/g, ""),
            'Task3', "should display the correct number of records");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_model:contains("No Source")').length, 1,
            "should at least have a no-model element");

        kanban.destroy();
    });

    QUnit.test('document selector: render without facets & tags', function (assert) {
        assert.expect(4);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            mockRPC: function (route, args) {
                if (args.method === 'group_by_documents') {
                    return $.when([]);
                }
                return this._super.apply(this, arguments);
            },
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_tags .o_documents_selector_header').text().trim(),
            'Tags', "should have a 'tags' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet').length, 0,
            "shouldn't have any facet");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_facet .o_documents_selector_tag').length, 0,
            "shouldn't have any tag");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_header').text().trim(),
            'Attached To', "should have an 'attached to' section");

        kanban.destroy();
    });

    QUnit.test('document selector: render without related models', function (assert) {
        assert.expect(3);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            domain: [['res_model', '=', false]],
        });

        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_tags .o_documents_selector_header').text().trim(),
            'Tags', "should have a 'tags' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_header').text().trim(),
            'Attached To', "should have an 'attached to' section");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_models .o_documents_selector_model:contains("No Source")').length, 1,
            "should at least have a no-model element");

        kanban.destroy();
    });

    QUnit.test('document selector: filter on related model', function (assert) {
        assert.expect(8);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            5, "should have 5 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should have 3 related models");

        // filter on 'Task'
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            3, "should have 3 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        // filter on 'Sale Order' (should be a disjunction)
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=order] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            4, "should have 6 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        // remove both filters
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=order] input:checkbox').click();
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            5, "should have 7 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        kanban.destroy();
    });

    QUnit.test('document selector: filter on attachments without related model', function (assert) {
        assert.expect(8);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            5, "should have 5 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should have 3 related models");

        // filter on 'No Source'
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=false] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            1, "should have 1 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        // filter on 'Task'
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            4, "should have 4 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        // remove both filters
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=false] input:checkbox').click();
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            5, "should have 5 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model').length,
            3, "should still have 3 related models");

        kanban.destroy();
    });

    QUnit.test('document selector: mix filter on related model and search filters', function (assert) {
        assert.expect(10);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            5, "should have 5 records in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task]').text().replace(/\s/g, ""),
            'Task3', "should display the correct number of records");

        // filter on 'Task'
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            3, "should have 3 records in the renderer");

        // reload with a domain
        kanban.reload({domain: [['public', '=', true]]});

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            1, "should have 1 record in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task]').text().replace(/\s/g, ""),
            'Task1', "should display the correct number of records");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=order]').text().replace(/\s/g, ""),
            'SaleOrder1', "should display the correct number of records");

        // filter on 'Sale Order'
        kanban.$('.o_documents_selector .o_documents_selector_model[data-id=order] input:checkbox').click();

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            2, "should have 2 records in the renderer");

        // reload without the domain
        kanban.reload({domain: []});

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            4, "should have 4 record in the renderer");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=task]').text().replace(/\s/g, ""),
            'Task3', "should display the correct number of records");
        assert.strictEqual(kanban.$('.o_documents_selector .o_documents_selector_model[data-id=order]').text().replace(/\s/g, ""),
            'SaleOrder1', "should display the correct number of records");

        kanban.destroy();
    });

    QUnit.test('document selector: selected tags are reset when switching between folders', function (assert) {
        assert.expect(6);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
            mockRPC: function (route, args) {
                if (route === '/web/dataset/search_read' && args.model === 'ir.attachment') {
                    assert.step(args.domain || []);
                }
                return this._super.apply(this, arguments);
            },
        });

        // filter on records having tag Draft
        kanban.$('.o_documents_selector_tag:contains(Draft) input').click();

        assert.ok(kanban.$('.o_documents_selector_tag:contains(Draft) input').is(':checked'),
            "tag selector should be checked");

        // switch to Folder2
        kanban.$('.o_documents_selector_folder:contains(Folder2) header').click();

        assert.notOk(kanban.$('.o_documents_selector_tag:contains(Draft) input').is(':checked'),
            "tag selector should not be checked anymore");

        assert.verifySteps([
            [["folder_id", "=", 1]],
            [["folder_id", "=", 1], ["tag_ids", "in", [2]]],
            [["folder_id", "=", 2]],
        ]);

        kanban.destroy();
    });

    QUnit.test('document selector: should keep its selection when adding a tag', function (assert) {
        assert.expect(5);
        var done = assert.async();

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // filter on records having tag Draft
        kanban.$('.o_documents_selector_tag:contains(Draft) input').click();

        assert.ok(kanban.$('.o_documents_selector_tag:contains(Draft) input').is(':checked'),
            "tag selector should be checked");

        assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            1, "should have records in the renderer");

        kanban.$('.o_kanban_record:first .o_record_selector').click();

        kanban.$('.o_inspector_tag_add').val('stress').trigger('keydown');
        concurrency.delay(0).then(function () {
            var $dropdown = kanban.$('.o_inspector_tag_add').autocomplete('widget');
            assert.strictEqual($dropdown.find('li').length, 1,
                "should have an entry in the autocomplete drodown");
            $dropdown.find('li > a').click();

            assert.ok(kanban.$('.o_documents_selector_tag:contains(Draft) input').is(':checked'),
                        "tag selector should still be checked");
            assert.strictEqual(kanban.$('.o_kanban_view .o_kanban_record:not(.o_kanban_ghost)').length,
            1, "should still have the same records in the renderer");

            kanban.destroy();
            done();
        });
    });

    QUnit.test('document selector: can (un)fold parent folders', function (assert) {
        assert.expect(7);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        assert.strictEqual(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').length, 1,
            "'Folder1' should be displayed as a parent folder");
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').hasClass('fa-caret-left'),
            "'Folder1' should be folded");
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_folded').length, 1,
            "'Folder1' should have className o_folded");

        // unfold Folder1
        kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').click();
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').hasClass('fa-caret-down'),
            "'Folder1' should be open");
        assert.notOk(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_folded').length, 1,
            "'Folder1' should not have className o_folded anymore");

        // fold Folder1
        kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').click();
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').hasClass('fa-caret-left'),
            "'Folder1' should be folded");
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_folded').length, 1,
            "'Folder1' should have className o_folded");

        kanban.destroy();
    });

    QUnit.test('document selector: fold status is kept at reload', function (assert) {
        assert.expect(4);

        var kanban = createView({
            View: DocumentsKanbanView,
            model: 'ir.attachment',
            data: this.data,
            arch: '<kanban><templates><t t-name="kanban-box">' +
                    '<div>' +
                        '<field name="name"/>' +
                    '</div>' +
                '</t></templates></kanban>',
        });

        // unfold Folder1
        kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').click();
        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').hasClass('fa-caret-down'),
            "'Folder1' should be open");
        assert.notOk(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_folded').length, 1,
            "'Folder1' should not have className o_folded");

        kanban.reload({});

        assert.ok(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_toggle_fold').hasClass('fa-caret-down'),
            "'Folder1' should still be open");
        assert.notOk(kanban.$('.o_documents_selector_folder:contains(Folder1) .o_folded').length, 1,
            "'Folder1' should still not have className o_folded");

        kanban.destroy();
    });
});

});
