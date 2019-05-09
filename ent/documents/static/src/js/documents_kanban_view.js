odoo.define('documents.DocumentsKanbanView', function (require) {
"use strict";

var DocumentsKanbanController = require('documents.DocumentsKanbanController');
var DocumentsKanbanModel = require('documents.DocumentsKanbanModel');
var DocumentsKanbanRenderer = require('documents.DocumentsKanbanRenderer');

var config = require('web.config');
var core = require('web.core');
var KanbanView = require('web.KanbanView');
var view_registry = require('web.view_registry');

var _lt = core._lt;

if (config.device.isMobile) {
    // use the classical KanbanView in mobile
    view_registry.add('documents_kanban', KanbanView);
    return;
}

var DocumentsKanbanView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: DocumentsKanbanController,
        Model: DocumentsKanbanModel,
        Renderer: DocumentsKanbanRenderer,
    }),
    display_name: _lt('Attachments Kanban'),
    groupable: false,

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);

        // add the fields used in the DocumentsInspector to the list of fields to fetch
        var inspectorFields = [
            'active',
            'available_rule_ids',
            'checksum',
            'datas_fname',
            'display_name', // necessary for the mail tracking system to work correctly
            'folder_id',
            'lock_uid',
            'message_follower_ids',
            'message_ids',
            'activity_ids',
            'mimetype',
            'name',
            'owner_id',
            'partner_id',
            'res_id',
            'res_model',
            'res_model_name',
            'res_name',
            'share_ids',
            'tag_ids',
            'type',
            'url',
        ];
        _.defaults(this.fieldsInfo[this.viewType], _.pick(this.fields, inspectorFields));

        // force fetch of relational data (display_name and tooltip) for related
        // rules to display in the DocumentsInspector
        this.fieldsInfo[this.viewType].available_rule_ids = _.extend({}, {
            fieldsInfo: {
                default: {
                    display_name: {},
                    note: {},
                },
            },
            relatedFields: {
                display_name: {type: 'string'},
                note: {type: 'string'},
            },
            viewType: 'default',
        }, this.fieldsInfo[this.viewType].available_rule_ids);
    },
});

view_registry.add('documents_kanban', DocumentsKanbanView);

return DocumentsKanbanView;

});
