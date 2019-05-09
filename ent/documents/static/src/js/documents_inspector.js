odoo.define('documents.DocumentsInspector', function (require) {
"use strict";

/**
 * This file defines the DocumentsInspector Widget, which is displayed next to
 * the KanbanRenderer in the DocumentsKanbanView.
 */

var DocumentViewer = require('mail.DocumentViewer');

var core = require('web.core');
var fieldRegistry = require('web.field_registry');
var session = require('web.session');
var Widget = require('web.Widget');

var _t = core._t;
var qweb = core.qweb;

var TAGS_SEARCH_LIMIT = 4;

var DocumentsInspector = Widget.extend({
    template: 'documents.DocumentsInspector',
    custom_events: {
        field_changed: '_onFieldChanged',
    },
    events: {
        'click .o_inspector_archive': '_onArchive',
        'click .o_inspector_delete': '_onDelete',
        'click .o_inspector_download': '_onDownload',
        'click .o_inspector_replace': '_onReplace',
        'click .o_inspector_lock': '_onLock',
        'click .o_inspector_share': '_onShare',
        'click .o_inspector_open_chatter': '_onOpenChatter',
        'click .o_inspector_tag_add': '_onTagInputClicked',
        'click .o_inspector_tag_remove': '_onRemoveTag',
        'click .o_inspector_trigger_rule': '_onTriggerRule',
        'click .o_inspector_object_name': '_onOpenResource',
        'click .o_preview_available': '_onOpenPreview',
        'click .o_document_pdf': '_onOpenPDF',
        'mouseover .o_inspector_trigger_hover': '_onMouseoverRule',
        'mouseout .o_inspector_trigger_hover': '_onMouseoutRule',
    },

    /**
     * @override
     * @param {Object} params
     * @param {Array} params.recordIDs list of document's resIDs
     * @param {Object} params.state
     */
    init: function (parent, params) {
        var self = this;
        this._super.apply(this, arguments);

        this.nbDocuments = params.state.count;
        this.size = params.state.size;
        this.currentFolder = _.findWhere(params.state.folders, {id: params.state.folderID});

        this.records = [];
        _.each(params.recordIDs, function (resID) {
            var record = _.findWhere(params.state.data, {res_id: resID});
            if (record) {
                self.records.push(_.extend(record, {
                    _isImage: new RegExp('image.*(gif|jpeg|jpg|png)').test(record.data.mimetype),
                }));
            }
        });

        this.tags = params.state.tags;
        var tagIDsByRecord = _.map(this.records, function (record) {
            return record.data.tag_ids.res_ids;
        });
        this.commonTagIDs = _.intersection.apply(_, tagIDsByRecord);

        var ruleIDsByRecord = _.map(this.records, function (record) {
            return record.data.available_rule_ids.res_ids;
        });
        var commonRuleIDs =_.intersection.apply(_, ruleIDsByRecord);
        var record = this.records[0];
        this.rules = _.map(commonRuleIDs, function (ruleID) {
            var rule = _.findWhere(record.data.available_rule_ids.data, {
                res_id: ruleID,
            });
            return rule.data;
        });

        // we have to lock some actions (like opening the record preview) when
        // there are pending 'multiSave' requests
        this.savingDef = null;
        this.pendingSavingRequests = 0;
    },
    /**
     * @override
     */
    start: function () {
        this._renderFields();
        this._renderTags();
        this._renderRules();
        this._renderModel();
        this._updateButtons();
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Return the internal state of the widget, which has to be restored after
     * an update (when this instance is destroyed, and another one is created).
     *
     * @returns {Object}
     */
    getLocalState: function () {
        return {
            scrollTop: this.el.scrollTop,
        };
    },
    /**
     * Restore the given state.
     *
     * @param {Object} state
     * @param {integer} state.scrollTop the scroll position to restore
     */
    setLocalState: function (state) {
        this.el.scrollTop = state.scrollTop;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Generate the record dataPoint to pass to the FieldMany2one when several
     * records a selected, and when those records have different values for the
     * many2one field to display.
     *
     * @private
     * @param {string} fieldName a many2one field
     */
    _generateCommonRecord: function (fieldName) {
        var record = _.extend({}, this.records[0], {
            id: null,
            res_id: null,
        });
        record.data = _.extend({}, record.data);
        record.data[fieldName] = {
            data: {
                display_name: _t('Multiple values'),
                id: null,
            },
        };
        return record;
    },
    /**
     * Render and append a field widget for the given field and the current
     * records.
     *
     * @private
     * @param {string} fieldName
     * @param {Object} [options] options to pass to the field
     * @param {string} [options.icon] optional icon to display
     * @param {string} [options.label] the label to display
     */
    _renderField: function (fieldName, options) {
        options = options || {};

        // generate the record to pass to the FieldWidget
        var values = _.uniq(_.map(this.records, function (record) {
            return record.data[fieldName] && record.data[fieldName].res_id;
        }));
        var record;
        if (values.length > 1) {
            record = this._generateCommonRecord(fieldName);
        } else {
            record = this.records[0];
        }

        var $row = $(qweb.render('documents.DocumentsInspector.infoRow'));

        // render the label
        var $label = $(qweb.render('documents.DocumentsInspector.fieldLabel', {
            icon: options.icon,
            label: options.label || record.fields[fieldName].string,
            name: fieldName,
        }));
        $label.appendTo($row.find('.o_inspector_label'));

        // render and append field
        var type = record.fields[fieldName].type;
        var FieldWidget = fieldRegistry.get(type);
        options = _.extend({}, options, {
            noOpen: true, // option for many2one fields
            viewType: 'kanban',
        });
        var fieldWidget = new FieldWidget(this, fieldName, record, options);
        fieldWidget.appendTo($row.find('.o_inspector_value'));
        fieldWidget.getFocusableElement().attr('id', fieldName);
        if (type === 'many2one' && values.length > 1) {
            fieldWidget.$el.addClass('o_multiple_values');
        }

        $row.insertBefore(this.$('.o_inspector_fields tbody tr.o_inspector_divider'));
    },
    /**
     * @private
     */
    _renderFields: function () {
        var options = {mode: 'edit'};
        if (this.records.length === 1) {
            this._renderField('name', options);
            if (this.records[0].data.type === 'url') {
                this._renderField('url', options);
            }
            this._renderField('partner_id', options);
        }
        if (this.records.length > 0) {
            this._renderField('owner_id', options);
            this._renderField('folder_id', {
                icon: 'fa fa-folder o_documents_folder_color',
                mode: 'edit',
            });
        }
    },
    /**
     * @private
     */
    _renderModel: function () {
        if (this.records.length === 1){
            var resModelName = this.records[0].data.res_model_name;
            if (!resModelName || this.records[0].data.res_model === 'ir.attachment') {
                return;
            }

            var $modelContainer = this.$('.o_model_container');
            var options = {
                res_model: resModelName,
                res_name: this.records[0].data.res_name,
            };
            $modelContainer.append(qweb.render('documents.DocumentsInspector.resModel', options));
        }
    },
    /**
     * @private
     */
    _renderRules: function () {
        var self = this;
        _.each(this.rules, function (rule) {
            var $rule = $(qweb.render('documents.DocumentsInspector.rule', rule));
            $rule.appendTo(self.$('.o_inspector_rules'));
        });
    },
    /**
     * @private
     */
    _renderTags: function () {
        var self = this;
        var $tags = this.$('.o_inspector_tags');

        // render common tags
        _.each(this.commonTagIDs, function (tagID) {
            var tag = _.findWhere(self.tags, {tag_id: tagID});
            if (tag) {
                // hide unknown tags (this may happen if a document with tags
                // is moved to another folder, but we keep those tags in case
                // the document is moved back to its original folder)
                var $tag = $(qweb.render('documents.DocumentsInspector.tag', tag));
                $tag.appendTo(self.$('.o_inspector_tags'));
            }
        });

        // render autocomplete input (if there are still tags to add)
        if (this.tags.length > this.commonTagIDs.length) {
            this.$tagInput = $('<input>', {
                class: 'o_input o_inspector_tag_add',
                type: 'text',
            }).attr('placeholder', _t("+ Add a tag "));

            this.$tagInput.autocomplete({
                delay: 0,
                minLength: 0,
                select: function (event, ui) {
                    self._saveMulti({
                        tag_ids: {
                            operation: 'ADD_M2M',
                            resIDs: [ui.item.id],
                        },
                    });
                },
                source: function (req, resp) {
                    resp(self._search(req.term));
                },
            });

            var disabled = this.records.length === 1 && !this.records[0].data.active;
            $tags.closest('.o_inspector_custom_field').toggleClass('o_disabled', disabled);

            this.$tagInput.appendTo($tags);
        }
    },
    /**
     * Trigger a 'save_multi' event to save changes on the selected records.
     *
     * @private
     * @param {Object} changes
     */
    _saveMulti: function (changes) {
        var self = this;
        this.savingDef = this.savingDef || $.Deferred();
        this.pendingSavingRequests++;
        this.trigger_up('save_multi', {
            changes: changes,
            dataPointIDs: _.pluck(this.records, 'id'),
            callback: function () {
                self.pendingSavingRequests--;
                if (self.pendingSavingRequests === 0) {
                    self.savingDef.resolve();
                }
            },
        });
    },
    /**
     * Search for tags matching the given value. The result is given to jQuery
     * UI autocomplete.
     *
     * @private
     * @param {string} value
     * @returns {Object[]}
     */
    _search: function (value) {
        var self = this;
        var options = {
            extract: function (el) {
                return el.label;
            }
        };
        var tags = [];
        _.each(this.tags, function (tag) {
            // don't search amongst already linked tags
            if (!_.contains(self.commonTagIDs, tag.tag_id)) {
                tags.push({
                    id: tag.tag_id,
                    label: tag.facet_name + ' > ' + tag.tag_name,
                });
            }
        });
        var searchResults = fuzzy.filter(value, tags, options).slice(0, TAGS_SEARCH_LIMIT);
        return _.map(searchResults, function (result) {
            return tags[result.index];
        });
    },
    /**
     * Disable buttons if at least one of the selected records is locked by
     * someone else
     *
     * @private
     */
    _updateButtons: function () {
        var disabled = _.some(this.records, function (record) {
            return record.data.lock_uid && record.data.lock_uid.res_id !== session.uid;
        });
        var binary = _.some(this.records, function (record) {
            return record.data.type === 'binary';
        });
        if (disabled) {
            this.$('.o_inspector_replace').prop('disabled', true);
            this.$('.o_inspector_delete').prop('disabled', true);
            this.$('.o_inspector_archive').prop('disabled', true);
        }
        if (!binary && (this.records.length > 1 || (this.records.length && this.records[0].data.type === 'empty'))) {
            this.$('.o_inspector_download').prop('disabled', true);
        }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onArchive: function () {
        this.trigger_up('archive_records', {
            records: this.records,
        });
    },
    /**
     * @private
     */
    _onDelete: function () {
        this.trigger_up('delete_records', {
            records: this.records,
        });
    },
    /**
     * Download the selected documents (zipped if there are several documents).
     *
     * @private
     */
    _onDownload: function () {
        this.trigger_up('download', {
            resIDs: _.pluck(this.records, 'res_id'),
        });
    },
    /**
     * Intercept 'field_changed' events as they may concern several records, and
     * not one as the events suggest. Trigger a 'save_multi' event instead,
     * which will be handled by the DocumentsKanbanController.
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onFieldChanged: function (ev) {
        ev.stopPropagation();
        this._saveMulti(ev.data.changes);
    },
    /**
     * Lock the current attachment for the current user. This assumes that there
     * is only one selected attachment (the lock button is hidden when several
     * records are selected).
     *
     * @private
     */
    _onLock: function () {
        this.trigger_up('lock_attachment', {
            resID: this.records[0].res_id,
        });
    },
    /**
     * Apply a style-class to a sidebar action when its button is hover
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onMouseoverRule: function (ev) {
        $(ev.currentTarget).closest('.o_inspector_trigger_hover_target').addClass('o_inspector_hover');
    },
    /**
     * Remove the style-class when the sidebar action button is not hover
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onMouseoutRule: function (ev) {
        $(ev.currentTarget).closest('.o_inspector_trigger_hover_target').removeClass('o_inspector_hover');
    },
    /**
     * @private
     */
    _onOpenChatter: function () {
        this.trigger_up('open_chatter', {
            id: this.records[0].id,
        });
    },
    /**
     * Open the document previewer, a fullscreen preview of the image with
     * download and print options.
     *
     * @private
     */
    _onOpenPreview: function (ev) {
        ev.stopPropagation();
        var self = this;
        var activeID = $(ev.currentTarget).data('id');
        if (activeID) {
            $.when(this.savingDef).then(function () {
                var records = _.pluck(self.records, 'data');
                var documentViewer = new DocumentViewer(self, records, activeID);
                documentViewer.appendTo($('.o_documents_kanban_view'));
            });
        }
    },
    /**
     * Open the business object linked to the selected record in a form view.
     *
     * @private
     */
    _onOpenResource: function () {
        var record = this.records[0];
        this.trigger_up('open_record', {
            resID: record.data.res_id,
            resModel: record.data.res_model,
        });
    },
    /**
     * Remove the clicked tag from the selected records.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onRemoveTag: function (ev) {
        ev.stopPropagation();
        var tagID = $(ev.currentTarget).closest('.o_inspector_tag').data('id');
        var changes = {
            tag_ids: {
                operation: 'FORGET',
                resIDs: [tagID],
            },
        };
        this._saveMulti(changes);
    },
    /**
     * TODO tests
     *
     * @private
     */
    _onReplace: function () {
        this.trigger_up('replace_file', {
            id: this.records[0].data.id,
        });
    },
    /**
     * Share the selected documents
     *
     * @private
     */
    _onShare: function () {
        this.trigger_up('share', {
            resIDs: _.pluck(this.records, 'res_id'),
        });
    },
    /**
     * Trigger a search or close the dropdown if it is already open when the
     * input is clicked.
     *
     * @private
     */
    _onTagInputClicked: function () {
        if (this.$tagInput.autocomplete("widget").is(":visible")) {
            this.$tagInput.autocomplete("close");
        } else {
            this.$tagInput.autocomplete('search');
        }
    },
    /**
     * Trigger a Workflow Rule's action on the selected records
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onTriggerRule: function (ev) {
        var $btn = $(ev.currentTarget);
        var ruleID = $btn.closest('.o_inspector_rule').data('id');
        $btn.prop('disabled', true);
        this.trigger_up('trigger_rule', {
            records: this.records,
            ruleID: ruleID
        });
    },
});

return DocumentsInspector;

});
