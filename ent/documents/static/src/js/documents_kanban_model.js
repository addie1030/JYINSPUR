odoo.define('documents.DocumentsKanbanModel', function (require) {
"use strict";

/**
 * This file defines the Model for the Documents Kanban view, which is an
 * override of the KanbanModel.
 */

var KanbanModel = require('web.KanbanModel');
var core = require('web.core');

var _t = core._t;

var DocumentsKanbanModel = KanbanModel.extend({
    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @param {Integer} recordID
     * @returns {Deferred}
     */
    fetchActivities: function (recordID) {
        var record = this.localData[recordID];
        return this._fetchSpecialActivity(record, 'activity_ids').then(function (data) {
            record.specialData.activity_ids = data;
        });
    },
    /**
     * @override
     */
    get: function (dataPointID) {
        var result = this._super.apply(this, arguments);
        if (result && result.type === 'list') {
            var dataPoint = this.localData[dataPointID];
            _.extend(result, _.pick(dataPoint, 'folderID', 'folders', 'relatedModels', 'size', 'tags'));
        }
        return result;
    },
    /**
     * Override to explicitely specify the 'searchDomain', which is the domain
     * coming from the search view. This domain is used to load the related
     * models, whereas a combination of this domain and the domain of the
     * DocumentsSelector is used for the classical search_read.
     *
     * Also fetch the folders here, so that it is done only once, as it doesn't
     * depend on the domain. Moreover, the folders are necessary to fetch the
     * tags, as we first fetch tags of the default folder.
     *
     * @override
     */
    load: function (params) {
        var self = this;
        var _super = this._super.bind(this);
        return this._fetchFolders(params.context).then(function (folders) {
            var defaultFolderID = folders.length ? folders[0].id : false;
            params = _.extend({}, params, {
                folderID: defaultFolderID,
                folders: folders,
            });

            params.domain = params.domain || [];
            params.searchDomain = params.domain;
            params.domain = self._addFolderToDomain(params.domain, params.folderID);

            var def = _super(params);
            return self._fetchAdditionalData(def, params).then(function (dataPointID) {
                var dataPoint = self.localData[dataPointID];
                dataPoint.folderID = params.folderID;
                dataPoint.folders = params.folders;
                dataPoint.isRootDataPoint = true;
                dataPoint.searchDomain = params.searchDomain;
                return dataPointID;
            });
        });
    },
    /**
     * Override to handle the 'selectorDomain' coming from the
     * DocumentsInspector, and to explicitely specify the 'searchDomain', which
     * is the domain coming from the search view. This domain is used to load
     * the related models, whereas a combination of the 'searchDomain' and the
     * 'selectorDomain' is used for the classical search_read.
     *
     * @override
     * @param {Array[]} [options.selectorDomain] the domain coming from the
     *   DocumentsInspector
     */
    reload: function (id, options) {
        options = options || {};
        var element = this.localData[id];

        if (element.isRootDataPoint) {
            // we are reloading the whole view
            element.folderID = options.folderID || element.folderID;
            options.folderID = element.folderID;

            var searchDomain = options.domain || element.searchDomain;
            element.searchDomain = options.searchDomain = searchDomain;
            options.domain = this._addFolderToDomain(searchDomain, options.folderID);
            if (options.selectorDomain !== undefined) {
                options.domain = searchDomain.concat(options.selectorDomain);
            }
        }

        var def = this._super.apply(this, arguments);
        if (element.isRootDataPoint) {
            return this._fetchAdditionalData(def, options);
        } else {
            return def;
        }
    },
    /**
     * Save changes on several records in a mutex, and reload.
     *
     * @param {string[]} recordIDs
     * @param {Object} values
     * @param {string} parentID
     * @returns {Deferred<string>} resolves with the parentID
     */
    saveMulti: function (recordIDs, values, parentID) {
        return this.mutex.exec(this._saveMulti.bind(this, recordIDs, values, parentID));
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Return an extended version of the given domain containing a part that
     * filters out records that do not belong to the given folder.
     *
     * @param {Array[]} domain
     * @param {integer} folderID
     * @returns {Array[]}
     */
    _addFolderToDomain: function (domain, folderID) {
        return domain.concat([['folder_id', '=', folderID]]);
    },
    /**
     * Build folders' tree based on flat array returned from server
     *
     * @private
     * @param {Array<Object>} folders
     * @param {Integer} parent_id
     * @returns {Array<Object>}
     */
    _buildFoldersTree: function (folders, parent_id) {
        var self = this;
        if (folders.length === 0) {
            return [];
        }
        var rootFolders = _.filter(folders, function (folder) {
            return folder.parent_folder_id === parent_id ||
                   (_.isArray(folder.parent_folder_id) && folder.parent_folder_id[0] === parent_id);
        });
        var subFolders = _.filter(folders, function (folder) {
            return folder.parent_folder_id !== parent_id ||
                   (_.isArray(folder.parent_folder_id) && folder.parent_folder_id[0] !== parent_id);
        });
        return _.map(rootFolders, function (folder) {
            return {
                id: folder.id,
                name: folder.name,
                description: folder.description,
                children: self._buildFoldersTree(subFolders, folder.id)
            };
        });
    },
    /**
     * Fetch additional data required by the DocumentsKanban view.
     *
     * @param {Deferred<string>} def resolves with the id of the dataPoint
     *   created by the load/reload call
     * @param {Object} params parameters/options passed to the load/reload function
     * @returns {Deferred<string>} resolves with the dataPointID
     */
    _fetchAdditionalData: function (def, params) {
        var self = this;
        var defs = [def];
        defs.push(this._fetchRelatedModels(params));
        defs.push(this._fetchSize(params));
        defs.push(this._fetchTags(params));
        return $.when.apply($, defs).then(function (dataPointID, models, size, tags) {
            var dataPoint = self.localData[dataPointID];
            dataPoint.relatedModels = models;
            dataPoint.tags = tags;
            dataPoint.size = size;
            return dataPointID;
        });
    },
    /**
     * Fetch all folders, and convert them into a tree structure
     * @param {Object} context
     *
     * @private
     * @returns {Deferred<array>}
     */
    _fetchFolders: function (context) {
        var self = this;
        return this._rpc({
            model: 'documents.folder',
            method: 'search_read',
            fields: ['parent_folder_id', 'name', 'id', 'description'],
            context: context,
        }).then(function (folders) {
            return self._buildFoldersTree(folders, false);
        });
    },
    /**
     * Fetch all related models.
     *
     * @private
     * @param {Object} params parameters/options passed to the load/reload function
     * @param {array} params.domain domain used during the load/reload call
     * @returns {Deferred<array>}
     */
    _fetchRelatedModels: function (params) {
        params = params || {};
        return this._rpc({
            model: 'ir.attachment',
            method: 'read_group',
            domain: this._addFolderToDomain(params.searchDomain, params.folderID),
            fields: ['res_model', 'res_model_name'],
            groupBy: ['res_model', 'res_model_name'],
            lazy: false,
        }).then(function (models) {
            return _.map(models, function (model) {
                if (!model.res_model_name) {
                    model.res_model_name = _t('No Source');
                }
                return model;
            });
        });
    },
    /**
     * Fetch the sum of the size of the documents matching the current domain.
     *
     * @private
     * @param {Object} params
     * @returns {Deferred<integer>} the size, in MB
     */
    _fetchSize: function (params) {
        params = params || {};
        return this._rpc({
            model: 'ir.attachment',
            method: 'read_group',
            domain: params.domain || [],
            fields: ['file_size'],
            groupBy: [],
        }).then(function (result) {
            var size = result[0].file_size / (1000*1000); // in MB
            return Math.round(size * 100) / 100;
        });
    },
    /**
     * Fetch all tags. A tag as a 'tag_id', a 'tag_name', a 'facet_id', a
     * 'facet_name', a 'facet_tooltip' and a 'count' (the number of records linked to this tag).
     *
     * @private
     * @param {Object} params parameters/options passed to the load/reload function
     * @param {array} params.domain domain used during the load/reload call
     * @returns {Deferred<array>}
     */
    _fetchTags: function (params) {
        params = params || {};
        return this._rpc({
            model: 'documents.tag',
            method: 'group_by_documents',
            kwargs: {
                folder_id: params.folderID,
                domain: this._addFolderToDomain(params.domain, params.folderID),
            },
        });
    },
    /**
     * Save changes on several records. Be careful that this function doesn't
     * handle all field types: only primitive types, many2ones and many2manys
     * (forget and link_to commands) are covered.
     *
     * @private
     * @param {string[]} recordIDs
     * @param {Object} values
     * @param {string} parentID
     * @returns {Deferred<string>} resolves with the parentID
     */
    _saveMulti: function (recordIDs, values, parentID) {
        var self = this;
        var parent = this.localData[parentID];
        var resIDs = _.map(recordIDs, function (recordID) {
            return self.localData[recordID].res_id;
        });
        var changes = _.mapObject(values, function (value, fieldName) {
            var field = parent.fields[fieldName];
            if (field.type === 'many2one') {
                value = value.id;
            } else if (field.type === 'many2many') {
                var command = value.operation === 'FORGET' ? 3 : 4;
                value = _.map(value.resIDs, function (resID) {
                    return [command, resID];
                });
            }
            return value;
        });

        return this._rpc({
            model: parent.model,
            method: 'write',
            args: [resIDs, changes],
        });
    },
});

return DocumentsKanbanModel;

});
