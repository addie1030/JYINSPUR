odoo.define('web_grid.GridModel', function (require) {
"use strict";

var AbstractModel = require('web.AbstractModel');
var concurrency = require('web.concurrency');

return AbstractModel.extend({
    /**
     * GridModel
     *
     * All data will be loaded in the _gridData object and can be retrieved with
     * the `get` method.
     */

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this._gridData = null;
        this._fetchMutex = new concurrency.Mutex();
        this._pendingFetch = null;
        this._waitingDef = $.Deferred();
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     * @returns {Object}
     */
    get: function () {
        return this._gridData;
    },
    /**
     * @override
     * @param {Object} context
     * @returns {Object}
     */
    getContext: function (context) {
        var c = _.extend({}, this.context, context);
        return c;
    },
    /**
     * The data from the grid view basically come from a read_group so we don't
     * have any res_ids. A big domain is thus computed with the domain of all
     * cells and this big domain is used to search for res_ids.
     *
     * @returns {Deferred<integer[]>} the list of ids used in the grid
     */
    getIds: function () {
        var data = this._gridData;
        if (!_.isArray(data)) {
            data = [data];
        }

        var domain = [];
        // count number of non-empty cells and only add those to the search
        // domain, on sparse grids this makes domains way smaller
        var cells = 0;

        for (var i = 0; i < data.length; i++) {
            var grid = data[i].grid;

            for (var j = 0; j < grid.length; j++) {
                var row = grid[j];
                for (var k = 0; k < row.length; k++) {
                    var cell = row[k];
                    if (cell.size !== 0) {
                        cells++;
                        domain.push.apply(domain, cell.domain);
                    }
                }
            }
        }

        // if there are no elements in the grid we'll get an empty domain
        // which will select all records of the model... that is *not* what
        // we want
        if (cells === 0) {
            return $.when([]);
        }

        while (--cells > 0) {
            domain.unshift('|');
        }

        return this._rpc({
            model: this.modelName,
            method: 'search',
            args: [domain],
            context: this.getContext(),
        });
    },
    /**
     * @override
     * @param {Object} params
     * @returns {Deferred}
     */
    load: function (params) {
        this.modelName = params.modelName;
        this.rowFields = params.rowFields;
        this.sectionField = params.sectionField;
        this.colField = params.colField;
        this.cellField = params.cellField;
        this.ranges = params.ranges;
        this.currentRange = params.currentRange;
        this.domain = params.domain;
        this.context = params.context;
        var groupedBy = (params.groupedBy && params.groupedBy.length) ?
            params.groupedBy : this.rowFields;
        this.groupedBy = Array.isArray(groupedBy) ? groupedBy : [groupedBy];
        return this._fetch(this.groupedBy);
    },
    /**
     * @override
     * @param {any} handle this parameter is ignored
     * @param {Object} params
     * @returns {Deferred}
     */
    reload: function (handle, params) {
        params = params || {};
        if ('context' in params) {
            // keep the grid anchor, when reloading view (e.i.: removing a filter in search view)
            var old_context = this.context;
            this.context = params.context;
            if (old_context.grid_anchor !== undefined || params.context.grid_anchor !== undefined) {
                this.context.grid_anchor = old_context.grid_anchor || params.context.grid_anchor;
            }
        }
        if ('domain' in params) {
            this.domain = params.domain;
        }
        if ('pagination' in params) {
            _.extend(this.context, params.pagination);
        }
        if ('range' in params) {
            this.currentRange = _.findWhere(this.ranges, {name: params.range});
        }
        if ('groupBy' in params) {
            if (params.groupBy.length) {
                this.groupedBy = Array.isArray(params.groupBy) ?
                    params.groupBy : [params.groupBy];
            } else {
                this.groupedBy = this.rowFields;
            }
        }
        return this._fetch(this.groupedBy);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * We only want a single fetch being performed at any time (because
     * there's really no point in performing 5 fetches concurrently just
     * because the user has just edited 5 records), utils.Mutex does that
     * fine, *however* we don't actually care about all the fetches, if
     * we're enqueuing fetch n while fetch n-1 is waiting, we can just
     * drop the older one, it's only going to delay the currently
     * useful and interesting job.
     *
     * So when requesting a fetch
     * * if there's no request waiting on the mutex (for a fetch to come
     *   back) set the new request waiting and queue up a fetch on the
     *   mutex
     * * if there is already a request waiting (and thus an enqueued fetch
     *   on the mutex) just replace the old request, so it'll get taken up
     *   by the enqueued fetch eventually
     *
     * @private
     * @param {Function} fn the handler function to enqueue. Note that this
     *                      handler can be dropped if there was a n-1 (so n
     *                      is waiting) and a n+1 arrives before n-1 is done.
     * @returns {Deferred}
     */
    _enqueue: function (fn) {
        var self = this;
        this._waitingDef = $.Deferred();
        if (this._pendingFetch) {
            // if there's already a query waiting for a slot, drop it and replace
            // it by the new updated query
            this._pendingFetch = fn;
        } else {
            // if there's no query waiting for a slot, add the current one and
            // enqueue a fetch job
            this._pendingFetch = fn;
            this._fetchMutex.exec(function () {

                var def = self._waitingDef;
                var fn = self._pendingFetch;
                self._pendingFetch = null;

                return fn().then(def.resolve.bind(def));
            });
        }
        return this._waitingDef;
    },
    /**
     * @private
     * @param {string[]} groupBy
     * @returns {Deferred}
     */
    _fetch: function (groupBy) {
        var self = this;

        if (!this.currentRange) {
            return $.when();
        }

        return this._enqueue(function () {
            if (self.sectionField && self.sectionField === groupBy[0]) {
                return self._fetchGroupedData(groupBy);
            } else {
                return self._fetchUngroupedData(groupBy);
            }
        });
    },
    /**
     * @private
     * @param {string[]} groupBy
     * @returns {Deferred}
     */
    _fetchGroupedData: function (groupBy) {
        var self = this;
        return this._rpc({
            model: self.modelName,
            method: 'read_grid_domain',
            kwargs: {
                field: self.colField,
                range: self.currentRange,
            },
            context: self.getContext(),
        }).then(function (d) {
            return self._rpc({
                model: self.modelName,
                method: 'read_group',
                kwargs: {
                    domain: d.concat(self.domain || []),
                    fields: [self.sectionField],
                    groupby: [self.sectionField],
                },
                context: self.getContext()
            });
        }).then(function (groups) {
            if (!groups.length) {
                // if there are no groups in the output we still need
                // to fetch an empty grid so we can render the table's
                // decoration (pagination and columns &etc) otherwise
                // we get a completely empty grid
                return self._fetchSectionGrid(groupBy, {
                    __domain: self.domain || [],
                });
            }
            return $.when.apply(null, _(groups).map(function (group) {
                return self._fetchSectionGrid(groupBy, group);
            }));
        }).then(function () {
            var results = [].slice.apply(arguments);
            self._gridData = results;
            self._gridData.groupBy = groupBy;
            self._gridData.colField = self.colField;
            self._gridData.cellField = self.cellField;
            self._gridData.range = self.currentRange.name;
            self._gridData.context = self.context;

            // set the prev & next in the state for grouped
            var r0 = results[0];
            self._gridData.prev = r0 && r0.prev;
            self._gridData.next = r0 && r0.next;
        });
    },
    /**
     * @private
     * @param {string[]} groupBy
     * @param {Object} sectionGroup
     * @param {Object} [additionalContext]
     * @returns {Deferred}
     */
    _fetchSectionGrid: function (groupBy, sectionGroup, additionalContext) {
        var self = this;
        return this._rpc({
            model: this.modelName,
            method: 'read_grid',
            kwargs: {
                row_fields: groupBy.slice(1),
                col_field: this.colField,
                cell_field: this.cellField,
                range: this.currentRange,
                domain: sectionGroup.__domain,
            },
            context: this.getContext(additionalContext),
        }).done(function (grid) {
            grid.__label = sectionGroup[self.sectionField];
        });
    },
    /**
     * @private
     * @param {string[]} groupBy
     * @returns {Deferred}
     */
    _fetchUngroupedData: function (groupBy) {
        var self = this;
        return this._rpc({
            model: self.modelName,
            method: 'read_grid',
            kwargs: {
                row_fields: groupBy,
                col_field: self.colField,
                cell_field: self.cellField,
                domain: self.domain,
                range: self.currentRange,
            },
            context: self.getContext(),
        })
        .then(function (result) {
            self._gridData = result;
            self._gridData.groupBy = groupBy;
            self._gridData.colField = self.colField;
            self._gridData.cellField = self.cellField;
            self._gridData.range = self.currentRange.name;
            self._gridData.context = self.context;
        });
    },
});

});
