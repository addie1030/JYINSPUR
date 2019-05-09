odoo.define('documents.DocumentsKanbanController', function (require) {
"use strict";

/**
 * This file defines the Controller for the Documents Kanban view, which is an
 * override of the KanbanController.
 */

var DocumentsInspector = require('documents.DocumentsInspector');
var DocumentViewer = require('mail.DocumentViewer');

var Chatter = require('mail.Chatter');

var core = require('web.core');
var KanbanController = require('web.KanbanController');
var session = require('web.session');

var qweb = core.qweb;
var _t = core._t;

var DocumentsKanbanController = KanbanController.extend({
    events: _.extend({}, KanbanController.prototype.events, {
        'click .o_document_close_chatter': '_onCloseChatter',
        'change .o_documents_selector_model input': '_onCheckSelectorModel',
        'change .o_documents_selector_tag input': '_onCheckSelectorTag',
        'change .o_documents_selector_facet > header input': '_onCheckSelectorFacet',
        'click .o_foldable .o_toggle_fold': '_onToggleFold',
        'click .o_documents_selector_folder header': '_onSelectFolder',
        'drop .o_documents_kanban_view': '_onDrop',
        'dragover .o_documents_kanban_view': '_onHoverDrop',
        'dragleave .o_documents_kanban_view': '_onHoverLeave',
    }),
    custom_events: _.extend({}, KanbanController.prototype.custom_events, {
        archive_records: '_onArchiveRecords',
        delete_records: '_onDeleteRecords',
        document_viewer_attachment_changed: '_onDocumentViewerAttachmentChanged',
        download: '_onDownload',
        kanban_image_clicked: '_onKanbanPreview',
        lock_attachment: '_onLock',
        open_chatter: '_onOpenChatter',
        open_record: '_onOpenRecord',
        replace_file: '_onReplaceFile',
        save_multi: '_onSaveMulti',
        select_record: '_onRecordSelected',
        selection_changed: '_onSelectionChanged',
        share: '_onShareIDs',
        trigger_rule: '_onTriggerRule',
    }),

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.selectedRecordIDs = [];
        this.selectedFilterModelIDs = [];
        this.selectedFilterTagIDs = {};
        this.chatter = null;
        this.documentsInspector = null;
        this.anchorID = null; // used to select records with ctrl/shift keys
        this.fileUploadID = _.uniqueId('documents_file_upload');

        var state = this.model.get(this.handle);
        this.selectedFolderID = state.folderID;

        // store in memory the folded state of folders and facets, to keep it
        // at each reload
        this.openedFolders = {};
        this.foldedFacets = {};
    },
    /**
     * @override
     */
    start: function () {
        this.$el.addClass('o_documents_kanban d-flex');
        $(window).on(this.fileUploadID, this._onFileUploaded.bind(this));
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @param {jQueryElement} $node
     */
    renderButtons: function ($node) {
        this.$buttons = $(qweb.render('DocumentsKanbanView.buttons'));
        this.$buttons.appendTo($node);
        this.$buttons.on('click', '.o_documents_kanban_share', this._onShareDomain.bind(this));
        this.$buttons.on('click', '.o_documents_kanban_upload', this._onUpload.bind(this));
        this.$buttons.on('click', '.o_documents_kanban_url', this._onUploadFromUrl.bind(this));
        this.$buttons.on('click', '.o_documents_kanban_request', this._onRequestFile.bind(this));
    },
    /**
     * @override
     * @param {object} params
     * @param {object} options
     */
    update: function (params, options) {
        params = params || {};
        params.folderID = this.selectedFolderID;
        params.selectorDomain = this._buildSelectorDomain();
        return this._super(params, options);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Generic method to add a filter from selector panel
     *
     * @private
     * @param {String} selectionProp - instance property's name used to store filter
     * @param {Integer} id
     */
    _addSelectorFilter: function (selectionProp, id) {
        this[selectionProp] = _.uniq(this[selectionProp].concat(id));
    },
    /**
     * Add a Tag filter from selector panel
     *
     * @private
     * @param {Integer} facetID
     * @param {Integer} tagID
     */
    _addSelectorTagFilter: function (facetID, tagID) {
        this.selectedFilterTagIDs[facetID] = this.selectedFilterTagIDs[facetID] || [];
        this.selectedFilterTagIDs[facetID] = _.uniq(this.selectedFilterTagIDs[facetID].concat(tagID));
    },
    /**
     * Reload the controller and reset pagination offset
     * Typically used when updating a selector's filter
     *
     * @private
     * @returns {Deferred}
     */
    _applySelectors: function () {
        return this.reload({offset: 0});
    },
    /**
     * Construct the extra domain based on selector's filters
     *
     * @private
     * @returns {Array[]}
     */
    _buildSelectorDomain: function () {
        var domain = [];
        if (this.selectedFolderID) {
            domain.push(['folder_id', '=', this.selectedFolderID]);
        }
        _.each(this.selectedFilterTagIDs, function (facetTagIDs) {
            if (facetTagIDs.length) {
                domain.push(['tag_ids', 'in', facetTagIDs]);
            }
        });
        if (this.selectedFilterModelIDs.length) {
            domain.push(['res_model', 'in', this.selectedFilterModelIDs]);
        }
        return domain;
    },
    /**
     * @private
     */
    _closeChatter: function () {
        this.$el.removeClass('o_chatter_open');
        this.$('.o_document_chatter').remove();
        if (this.chatter) {
            this.chatter.destroy();
            this.chatter = null;
        }
    },
    /**
     * Group tags by facets.
     *
     * @private
     * @param {Object[]} tags - raw list of tags
     * @returns {Object[]}
     */
    _groupTagsByFacets: function (tags) {
        var groupedFacets = _.reduce(tags, function (memo, tag) {
            var facetKey = tag.facet_sequence + '-' + tag.facet_name;
            if (!_.has(memo, facetKey)) {
                memo[facetKey] = {
                    id: tag.facet_id,
                    name: tag.facet_name,
                    tooltip: tag.facet_tooltip,
                    tags: [],
                };
            }
            memo[facetKey].tags.push({
                id: tag.tag_id,
                name: tag.tag_name,
                __count: tag.__count
            });
            return memo;
        }, {});
        return _.values(groupedFacets);
    },
    /**
     * Set indeterminate state for partially selected facets' checkboxes
     * Note: cannot be done through HTML attributes
     *
     * @private
     */
    _markPartiallySelectedFacet: function () {
        this.$('.o_documents_selector_facet').each(function (idx, el) {
            var $el = $(el);
            var $input = $el.find('> header input');
            if (!$input.get(0)) {
                return;
            }
            var $allTags = $el.find('.o_documents_selector_tag input');
            var $selectedTags = $allTags.filter(':checked');
            var nbSelectedTags = $selectedTags.length;
            $input.get(0).indeterminate = nbSelectedTags > 0 && nbSelectedTags < $allTags.length;
        });
    },
    /**
     * Opens the chatter of the given record.
     *
     * @private
     * @param {Object} record
     * @returns {Deferred}
     */
    _openChatter: function (record) {
        var self = this;
        return this.model.fetchActivities(record.id).then(function () {
            record = self.model.get(record.id);
            var $chatterContainer = $('<div>').addClass('o_document_chatter p-relative bg-white');
            var options = {
                display_log_button: true,
                isEditable: true,
            };
            var mailFields = {mail_thread: 'message_ids',
                          mail_followers: 'message_follower_ids',
                          mail_activity: 'activity_ids'};

            self._closeChatter();
            self.chatter = new Chatter(self, record, mailFields, options);
            return self.chatter.appendTo($chatterContainer).then(function () {
                $chatterContainer.append($('<span>').addClass('o_document_close_chatter text-center').html('&#215;'));
                self.$el.addClass('o_chatter_open');
                self.$el.append($chatterContainer);
            });
        });
    },
    /**
     * Prepares and upload files.
     *
     * @private
     * @param {Object[]} files
     * @returns {Deferred}
     */
    _processFiles: function (files) {
        var self = this;
        var $formContainer = this.$('.o_content').find('.o_documents_hidden_input_file_container');
        if (!$formContainer.length) {
            $formContainer = $(qweb.render('documents.HiddenInputFile', {
                widget: this,
                csrf_token: core.csrf_token,
            }));
            $formContainer.appendTo(this.$('.o_content'));
        }
        var data = new FormData($formContainer.find('.o_form_binary_form')[0]);

        data.delete('ufile');
        _.each(files, function (file) {
            data.append('ufile', file);
        });
        var def = $.Deferred();
        $.ajax({
            url: '/web/binary/upload_attachment',
            processData: false,
            contentType: false,
            type: "POST",
            enctype: 'multipart/form-data',
            data: data,
            success: function (result) {
                def.resolve();
                var $el = $(result);
                $.globalEval($el.contents().text());
            },
            error: function (error) {
                self.do_notify(_t("Error"), _t("An error occurred during the upload"));
                return $.when();
            },
        });
        return def;
    },
    /**
     * Generic method to remove a filter from selector panel
     *
     * @private
     * @param {string} selectionProp the name of the class attribute which contains the selection
     * @param {string} id the filter element's identifier
     */
    _removeSelectorFilter: function (selectionProp, id) {
        this[selectionProp] = _.without(this[selectionProp], id);
    },
    /**
     * Remove a Tag filter from selector panel
     *
     * @private
     * @param {integer} facetID
     * @param {integer} tagID
     */
    _removeSelectorTagFilter: function (facetID, tagID) {
        this.selectedFilterTagIDs[facetID] = _.without(this.selectedFilterTagIDs[facetID], tagID);
    },
    /**
     * Renders and appends the documents inspector sidebar.
     *
     * @private
     * @param {Object} state
     */
    _renderDocumentsInspector: function (state) {
        var localState;
        if (this.documentsInspector) {
            localState = this.documentsInspector.getLocalState();
            this.documentsInspector.destroy();
        }
        var params = {
            recordIDs: this.selectedRecordIDs,
            state: state,
        };
        this.documentsInspector = new DocumentsInspector(this, params);
        this.documentsInspector.insertAfter(this.$('.o_kanban_view'));
        if (localState) {
            this.documentsInspector.setLocalState(localState);
        }
    },
    /**
     * Render and append the documents selector sidebar.
     *
     * @private
     * @param {Object} state
     */
    _renderDocumentsSelector: function (state) {
        var self = this;
        var scrollTop = this.$('.o_documents_selector').scrollTop();
        this.$('.o_documents_selector').remove();

        var relatedTagsByFacet = this._groupTagsByFacets(state.tags);
        var params = {
            facets: _.map(relatedTagsByFacet, function (facet) {
                facet.tags = _.map(facet.tags, function (tag) {
                    tag.selected = _.contains(self.selectedFilterTagIDs[facet.id], tag.id);
                    return tag;
                });
                var selectedTags = _.filter(facet.tags, function (tag) {
                    return tag.selected;
                });
                facet.selected = selectedTags.length === facet.tags.length;
                return facet;
            }),
            relatedModels: _.map(state.relatedModels, function (model) {
                model.selected = _.contains(self.selectedFilterModelIDs, model.res_model);
                return model;
            }),
        };
        var $documentSelector = $(qweb.render('documents.DocumentsSelector', params));
        var $folders = $documentSelector.find('.o_documents_selector_folders_container');
        $folders.append(this._renderFolders(state.folders));

        this.$el.prepend($documentSelector);
        this._markPartiallySelectedFacet();
        this._updateFoldableElements();

        this.$('.o_documents_selector').scrollTop(scrollTop || 0);
    },
    /**
     * Render a folder tree, recursively
     *
     * @private
     * @param {Object[]} folders - the subtree of folders to render
     * @returns {jQuery}
     */
    _renderFolders: function (folders) {
        var self = this;
        var $folders = $('<ul>', {class: 'list-group d-block'});
        _.each(folders, function (folder) {
            var $folder = $(qweb.render('documents.DocumentsSelectorFolder', {
                activeFolderID: self.selectedFolderID,
                folder: folder,
            }));
            if (folder.children.length) {
                var $children =  self._renderFolders(folder.children);
                $children.appendTo($folder);
            }
            $folder.appendTo($folders);
        });
        return $folders;
    },
    /**
     * Open the share wizard with the given context, containing either the
     * 'attachment_ids' or the 'active_domain'.
     *
     * @private
     * @param {Object} vals
     * @param {Array[]} [vals.attachment_ids] M2M commandsF
     * @param {Array[]} [vals.domain] the domain to share
     * @param {integer} vals.folderID
     * @param {Array[]} [vals.tags] M2M commands
     * @param {string} vals.type the type of share (either 'ids' or 'domain')
     * @returns {Deferred}
     */
    _share: function (vals) {
        var self = this;
        this._rpc({
            model: 'documents.share',
            method: 'create_share',
            args: [vals],
        }).then(function (result) {
            self.do_action(result);
        });
    },
    /**
     * Toggle the selected attached model
     *
     * @private
     * @param {any} model
     */
    _toggleSelectorModel: function (model) {
        if (_.contains(this.selectedFilterModelIDs, model)) {
            this._removeSelectorFilter('selectedFilterModelIDs', model);
        } else {
            this._addSelectorFilter('selectedFilterModelIDs', model);
        }
    },
    /**
     * Toggle the selected facet/tag
     *
     * @private
     * @param {string|integer} facet
     * @param {string|integer} tag
     */
    _toggleSelectorTag: function (facet, tag) {
        var facetID = parseInt(facet, 10);
        var tagID = parseInt(tag, 10);
        if (_.isNaN(tagID) && _.isNaN(facetID)) {
            return;
        }
        if (_.contains(this.selectedFilterTagIDs[facetID], tagID)) {
            this._removeSelectorTagFilter(facetID, tagID);
        } else {
            this._addSelectorTagFilter(facetID, tagID);
        }
    },
    /*
     * Apply rule's actions for the specified attachments.
     *
     * @private
     * @param {string[]} recordIDs
     * @param {string} ruleID
     * @returns {Deferred} either returns true or an action to open
     *   a form view on the created business object (if available)
     */
    _triggerRule: function (recordIDs, ruleID) {
        var self = this;
        return this._rpc({
            model: 'documents.workflow.rule',
            method: 'apply_actions',
            args: [[ruleID], recordIDs],
        }).then(function (result) {
            if (_.isObject(result)) {
                return self.do_action(result);
            } else {
                return self.reload();
            }
        });
    },
    /**
     * Override to render the documents selector and inspector sidebars.
     * Also update the selection.
     *
     * @override
     * @private
     */
    _update: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var state = self.model.get(self.handle);
            var recordIDs = _.pluck(state.data, 'res_id');
            self.selectedRecordIDs = _.intersection(self.selectedRecordIDs, recordIDs);
            return self._updateChatter(state).then(function () {
                self._renderDocumentsInspector(state);
                self._renderDocumentsSelector(state);
                self.anchorID = null;
                self.renderer.updateSelection(self.selectedRecordIDs);
            });
        });
    },
    /**
     * If a chatter is currently open, close it and re-open it with the
     * currently selected record (if exactly one is selected).
     *
     * @private
     * @param {Object} state
     * @returns {Deferred}
     */
    _updateChatter: function (state) {
        if (this.chatter) {
            // re-open the chatter if the new selection still contains 1 record
            if (this.selectedRecordIDs.length === 1) {
                var record = _.findWhere(state.data, {res_id: this.selectedRecordIDs[0]});
                if (record) {
                    return this._openChatter(record);
                }
            }
            this._closeChatter();
        }
        return $.when();
    },
    /**
     * Iterate of o_foldable elements (folders and facets) in this.$el, and set
     * their fold status (in the UI) according to the internal state
     *
     * @private
     */
    _updateFoldableElements: function () {
        var self = this;
        this.$('.o_foldable').each(function (index, item) {
            var $item = $(item);
            var id = $item.data('id');
            var folded;
            if ($item.hasClass('o_documents_selector_folder')) {
                folded = !self.openedFolders[id];
            } else if ($item.hasClass('o_documents_selector_facet')) {
                folded = !!self.foldedFacets[id];
            }
            var $caret = $item.find('.o_toggle_fold');
            $caret.toggleClass('fa-caret-down', !folded);
            $caret.toggleClass('fa-caret-left', folded);
            $item.find('.list-group:first').toggleClass('o_folded', folded);
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * FIXME: build a more complete archive system:
     * TODO tests
     * currently, it checks the archive state of the first record of the selection and supposes that
     * all the selected records have the same active state (since archived attachments should always be viewed
     * separately. The current system could technically cause unexpected results if the selection contains
     * records of both states.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {Object[]} ev.data.records objects with keys 'id' (the localID)
     *   and 'res_id'
     */
    _onArchiveRecords: function (ev) {
        ev.stopPropagation();
        var self = this;
        var active = !ev.data.records[0].data.active;
        var recordIDs = _.pluck(ev.data.records, 'id');
        this.model.toggleActive(recordIDs, active, this.handle).then(function () {
            self.update({}, {reload: false}); // the reload is done by toggleActive
        });
    },
    /**
     * React to facets selector to toggle child-tags filters.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onCheckSelectorFacet: function (ev) {
        ev.preventDefault();
        var $facet = $(ev.target).closest('.o_documents_selector_facet');
        var facetID = $facet.data().id;
        var $tags = $facet.find('.o_documents_selector_tag');
        var tagIDs = _.compact(_.map($tags, function (tag) {
            return parseInt($(tag).data().id, 10);
        }));
        if (tagIDs.length) {
            if (ev.target.checked) {
                _.each(tagIDs, _.partial(this._addSelectorTagFilter, facetID).bind(this));
            } else {
                _.each(tagIDs, _.partial(this._removeSelectorTagFilter, facetID).bind(this));
            }
            this._applySelectors();
        }
    },
    /**
     * React to attached model selector to filter the records.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onCheckSelectorModel: function (ev) {
        ev.preventDefault();
        var $item = $(ev.target).closest('.o_documents_selector_model');
        var data = $item.data();
        if (_.has(data, 'id')) {
            this._toggleSelectorModel(data.id);
            this._applySelectors();
        }
    },
    /**
     * React to tags selector to filter the records.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onCheckSelectorTag: function (ev) {
        ev.preventDefault();
        var $tag = $(ev.target).closest('.o_documents_selector_tag');
        var $facet = $tag.closest('.o_documents_selector_facet');
        var data = $tag.data();
        if (_.has(data, 'id')) {
            this._toggleSelectorTag($facet.data().id, data.id);
            this._markPartiallySelectedFacet();
            this._applySelectors();
        }
    },
    /**
     * @private
     */
    _onCloseChatter: function () {
        this._closeChatter();
    },
    /**
     * @private
     * @param {OdooEvent} ev
     * @param {Object[]} ev.data.records objects with keys 'id' (the localID)
     *   and 'res_id'
     */
    _onDeleteRecords: function (ev) {
        ev.stopPropagation();
        var self = this;
        var recordIDs = _.pluck(ev.data.records, 'id');
        this.model.deleteRecords(recordIDs, this.modelName).then(function () {
            var resIDs = _.pluck(ev.data.records, 'res_id');
            self.selectedRecordIDs = _.difference(self.selectedRecordIDs, resIDs);
            self.reload();
        });
    },
    /**
     * Update the controller when the DocumentViewer has modified an attachment
     *
     * @private
     */
    _onDocumentViewerAttachmentChanged: function () {
        this.update();
    },
    /**
     * @private
     * @param {OdooEvent} ev
     * @param {integer[]} ev.data.resIDs
     */
    _onDownload: function (ev) {
        ev.stopPropagation();
        var resIDs = ev.data.resIDs;
        if (resIDs.length === 1) {
            window.location = '/web/content/' + resIDs[0] + '?download=true';
        } else {
            var timestamp = moment().format('YYYY-MM-DD');
            session.get_file({
                url: '/document/zip',
                data: {
                    file_ids: resIDs,
                    zip_name: 'documents-' + timestamp + '.zip',
                },
            });
        }
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onDrop: function (ev) {
        ev.preventDefault();
        var self = this;
        this._processFiles(ev.originalEvent.dataTransfer.files).always(function () {
            self.$('.o_documents_kanban_view').removeClass('o_drop_over');
            self.$('.o_upload_text').remove();
            self.reload();
        });
    },
    /**
     * creates new documents when attachments are uploaded.
     * arguments are each uploaded files, a slice is called on arguments to extract those values.
     *
     * @private
     */
    _onFileUploaded: function () {
        var self = this;
        var tagIDs = _.flatten(_.values(this.selectedFilterTagIDs));
        var attachments = Array.prototype.slice.call(arguments, 1);
        var attachmentIds = _.pluck(attachments, 'id');
        var writeDict = {
            folder_id: this.selectedFolderID,
            res_model: false,
            res_id: false,
        }
        if (tagIDs) {
            writeDict.tag_ids = [[6, 0, tagIDs]];
        }
        if (!attachmentIds.length) {
            return;
        }
        this._rpc({
            model: 'ir.attachment',
            method: 'write',
            args: [attachmentIds, writeDict],
        }).then(function () {
            self.reload();
        });
    },
    /**
     * @private
     * @param {OdooEvent} ev
     * @param {Object} recordData ev.data.record
     */
    _onKanbanPreview: function (ev) {
        ev.stopPropagation();
        var self = this;
        var documentViewer = new DocumentViewer(this, [ev.data.record], ev.data.record.id);
        documentViewer.appendTo(this.$('.o_documents_kanban_view'));
    },
    /**
     * @private
     * @param {OdooEvent} ev
     * @param {integer} ev.data.resID
     */
    _onLock: function (ev) {
        ev.stopPropagation();
        var self = this;
        this._rpc({
            model: 'ir.attachment',
            method: 'toggle_lock',
            args: [ev.data.resID],
        }).always(function () {
            self.reload();
        });
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onHoverDrop: function (ev) {
        ev.preventDefault();
        this.renderer.$el.addClass('o_drop_over');
        if (this.$('.o_upload_text').length === 0) {
            var $upload_text = $('<div>').addClass("o_upload_text text-center text-white");
            $upload_text.append('<i class="d-block fa fa-upload fa-9x mb-4"/>');
            $upload_text.append('<span>' + _t('Drop files here to upload') + '</span>');
            this.$el.append($upload_text);
        }
        $(document).on('dragover:kanbanView', this._onHoverLeave.bind(this));
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onHoverLeave: function (ev) {
        if ($.contains(this.renderer.$el[0], ev.target)) {
            return;
        }

        // hack to prevent flickering when leaving kanban cards (in a 1px perimeter)
        var target = document.elementFromPoint(ev.originalEvent.clientX, ev.originalEvent.clientY);
        if ($.contains(this.renderer.$el[0], target)) {
            return;
        }

        $(document).off('dragover:kanbanView');
        this.renderer.$el.removeClass('o_drop_over');
        this.$('.o_upload_text').remove();
    },
    /**
     * Open the chatter of the given document.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {string} ev.data.id localID of the document
     */
    _onOpenChatter: function (ev) {
        ev.stopPropagation();
        var state = this.model.get(this.handle);
        var record = _.findWhere(state.data, {id: ev.data.id});
        this._openChatter(record);
    },
    /**
     * Open a record in form view given a model and an id.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {integer} [ev.data.resID] opens the form view in create mode if
     *   not given
     * @param {string} ev.data.resModel
     */
    _onOpenRecord: function (ev) {
        ev.stopPropagation();
        var self = this;
        this._rpc({
            model: ev.data.resModel,
            method: 'get_formview_id',
            args: [ev.data.resID],
        }).always(function (result) {
            self.do_action({
                res_id: ev.data.resID,
                res_model: ev.data.resModel,
                type: 'ir.actions.act_window',
                views: [[result, 'form']],
            });
        });
    },
    /**
     * React to records selection changes to update the DocumentInspector with
     * the current selected records.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {boolean} ev.data.clear if true, unselect other records
     * @param {MouseEvent} ev.data.originalEvent the event catched by the child
     *   element triggering up the OdooEvent
     * @param {string} ev.data.resID the resID of the record updating its status
     * @param {boolean} ev.data.selected whether the record is selected or not
     */
    _onRecordSelected: function (ev) {
        ev.stopPropagation();

        // update the list of selected records (support typical behavior of
        // ctrl/shift/command muti-selection)
        var shift = ev.data.originalEvent.shiftKey;
        var ctrl = ev.data.originalEvent.ctrlKey || ev.data.originalEvent.metaKey;
        var state = this.model.get(this.handle);
        if (ev.data.clear || shift || ctrl) {
            if (this.selectedRecordIDs.length === 1 && this.selectedRecordIDs[0] === ev.data.resID) {
                // unselect the record if it is currently the only selected one
                this.selectedRecordIDs = [];
            } else if (shift && this.selectedRecordIDs.length) {
                var recordIDs = _.pluck(state.data, 'res_id');
                var anchorIndex = recordIDs.indexOf(this.anchorID);
                var selectedRecordIndex = recordIDs.indexOf(ev.data.resID);
                var lowerIndex = Math.min(anchorIndex, selectedRecordIndex);
                var upperIndex = Math.max(anchorIndex, selectedRecordIndex);
                var shiftSelection = recordIDs.slice(lowerIndex, upperIndex + 1);
                if (ctrl) {
                    this.selectedRecordIDs = _.uniq(this.selectedRecordIDs.concat(shiftSelection));
                } else {
                    this.selectedRecordIDs = shiftSelection;
                }
            } else if (ctrl && this.selectedRecordIDs.length) {
                var oldIds = this.selectedRecordIDs.slice();
                this.selectedRecordIDs = _.without(this.selectedRecordIDs, ev.data.resID);
                if (this.selectedRecordIDs.length === oldIds.length) {
                    this.selectedRecordIDs.push(ev.data.resID);
                    this.anchorID = ev.data.resID;
                }
            } else {
                this.selectedRecordIDs = [ev.data.resID];
                this.anchorID = ev.data.resID;
            }
        } else if (ev.data.selected) {
            this.selectedRecordIDs.push(ev.data.resID);
            this.selectedRecordIDs = _.uniq(this.selectedRecordIDs);
            this.anchorID = ev.data.resID;
        } else {
            this.selectedRecordIDs = _.without(this.selectedRecordIDs, ev.data.resID);
        }

        // notify the controller of the selection changes
        this.trigger_up('selection_changed', {
            selection: this.selectedRecordIDs,
        });

        this.renderer.updateSelection(this.selectedRecordIDs);
    },
    /**
     * Replace a file of the document by prompting an input file.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {integer} ev.data.id
     */
    _onReplaceFile: function (ev) {
        var self = this;
        var $upload_input = $('<input type="file" name="files[]"/>');
        $upload_input.on('change', function (e) {
            var f = e.target.files[0];
            var state = self.model.get(self.handle);
            var reader = new FileReader();

            reader.onload = function (e) {
                 // convert data from "data:application/zip;base64,R0lGODdhAQBADs=" to "R0lGODdhAQBADs="
                var dataString = e.target.result;
                var data = dataString.split(',',2)[1];
                var mimetype = dataString.substring(
                                        dataString.indexOf(":") + 1,
                                        dataString.indexOf(";")
                                        );
                self._rpc({
                    model: 'ir.attachment',
                    method: 'write',
                    args: [[ev.data.id], {datas: data, mimetype: mimetype, datas_fname: f.name}],
                }).always(function () {
                    $upload_input.removeAttr('disabled');
                    $upload_input.val("");
                }).then(function () {
                    self.reload();
                });
            };
            try {
                reader.readAsDataURL(f);
            } catch (e) {
                console.warn(e);
            }
        });
        $upload_input.click();
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onRequestFile: function (ev) {
        ev.preventDefault();
        var self = this;
        var tagIDs = _.flatten(_.values(this.selectedFilterTagIDs));
        this.do_action('documents.action_request_form', {
            additional_context: {
                default_folder_id: this.selectedFolderID,
                default_tag_ids: [[6, 0, tagIDs]],
            },
            on_close: function () {
                self.reload();
            },
        });
    },
    /**
     * Save the changes done in the DocumentsInspector and re-render the view.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {string[]} ev.data.dataPointsIDs
     * @param {Object} ev.data.changes
     * @param {function} [ev.data.callback]
     */
    _onSaveMulti: function (ev) {
        ev.stopPropagation();
        this.model
            .saveMulti(ev.data.dataPointIDs, ev.data.changes, this.handle)
            .then(this.update.bind(this, {}, {}))
            .always(ev.data.callback || function () {});
    },
    /**
     * React to folder selector to filter the records.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onSelectFolder: function (ev) {
        ev.preventDefault();
        var $item = $(ev.currentTarget).closest('.o_documents_selector_folder');
        var data = $item.data();
        if ('id' in data && data.id !== this.selectedFolderID) {
            this.selectedFilterTagIDs = {}; // reset the tags as they depend on the current folder
            this.selectedFolderID = data.id;
            this._applySelectors();
        }
    },
    /**
     * React to records selection changes to update the DocumentInspector with
     * the current selected records.
     *
     * @private
     * @param {OdooEvent} ev
     * @param {integer[]} ev.data.selection the new list of selected record IDs
     */
    _onSelectionChanged: function (ev) {
        ev.stopPropagation();
        var self = this;
        this.selectedRecordIDs = ev.data.selection;
        var state = this.model.get(this.handle);
        this._updateChatter(state).then(function () {
            self._renderDocumentsInspector(state);
        });
    },
    /**
     * Share the current domain.
     *
     * @private
     */
    _onShareDomain: function () {
        var state = this.model.get(this.handle, {raw: true});
        var tagIDs = _.flatten(_.values(this.selectedFilterTagIDs));
        this._share({
            domain: state.domain,
            folder_id: this.selectedFolderID,
            tag_ids: [[6, 0, tagIDs]],
            type: 'domain',
        });
    },
    /**
     * Share the given records.
     *
     * @param {OdooEvent} ev
     * @param {integer[]} ev.data.resIDs
     */
    _onShareIDs: function (ev) {
        ev.stopPropagation();
        this._share({
            attachment_ids: [[6, 0, ev.data.resIDs]],
            folder_id: this.selectedFolderID,
            type: 'ids',
        });
    },
    /**
     * @private
     */
    _onToggleFavorite: function (ev) {
        ev.stopPropagation();
        var self = this;
        self._rpc({
            model: 'ir.attachment',
            method: 'toggle_favorited',
            args: [ev.data.resID],
        })
        .then(function () {
            self.reload();
        });
    },
    /**
     * Toggle subtree's visibility
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onToggleFold: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $target = $(ev.currentTarget);
        if (!$target.hasClass('o_foldable')) {
            $target = $target.closest('.o_foldable');
        }
        var folded = !$target.find('.list-group:first').hasClass('o_folded');
        var id = $target.data('id');
        if ($target.hasClass('o_documents_selector_folder')) {
            this.openedFolders[id] = !folded;
        } else if ($target.hasClass('o_documents_selector_facet')) {
            this.foldedFacets[id] = folded;
        }
        this._updateFoldableElements();
    },
    /**
     * Apply rule's actions for the given records in a mutex, and reload
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onTriggerRule: function (ev) {
        ev.stopPropagation();
        var recordIDs = _.pluck(ev.data.records, 'res_id');
        return this._triggerRule(recordIDs, ev.data.ruleID, this.handle);
    },
    /**
     * @private
     */
    _onUpload: function () {
        var self = this;
        var $uploadInput = $('<input>', {type: 'file', name: 'files[]', multiple: 'multiple'});
        $uploadInput.on('change', function (ev) {
            self._processFiles(ev.target.files).always(function () {
                $uploadInput.remove();
            });
        });
        $uploadInput.click();
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onUploadFromUrl: function (ev) {
        ev.preventDefault();
        var self = this;
        var tagIDs = _.flatten(_.values(this.selectedFilterTagIDs));
        this.do_action('documents.action_url_form', {
            additional_context: {
                default_folder_id: this.selectedFolderID,
                default_tag_ids: [[6, 0, tagIDs]],
            },
            on_close: function () {
                self.reload();
            },
        });
    },
});

return DocumentsKanbanController;

});
