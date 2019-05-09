odoo.define('web_studio.AbstractViewEditor', function (require) {
"use strict";

var ajax = require('web.ajax');
var AbstractView = require('web.AbstractView');

AbstractView.include({

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @param {Widget} parent
     * @param {Widget} Editor
     * @param {Object} options
     * @returns {Widget}
     */
    createStudioEditor: function (parent, Editor, options) {
        return this._createStudioRenderer(parent, Editor, options);
    },
    /**
     * @param {Widget} parent
     * @param {Widget} Editor
     * @param {Object} options
     * @returns {Widget}
     */
    createStudioRenderer: function (parent, options) {
        var Renderer = this.config.Renderer;
        return this._createStudioRenderer(parent, Renderer, options);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @param {Widget} parent
     * @param {Widget} Renderer
     * @param {Object} options
     * @returns {Widget}
     */
    _createStudioRenderer: function (parent, Renderer, options) {
        var self = this;
        var def = this._loadSubviews ? this._loadSubviews(parent) : $.when();
        return def.then(function () {
            return $.when(
                self._loadData(parent),
                ajax.loadLibs(self)
            ).then(function (handle) {
                var model = self.getModel();
                var state = model.get(handle);
                var params = _.extend({}, self.rendererParams, options);
                var editor = new Renderer(parent, state, params);
                // the editor needs to have a reference to its BasicModel
                // instance to reuse it in x2m edition
                editor.model = model;
                model.setParent(editor);
                return editor;
            });
        });
    },
    /**
     * This override is a hack because when we load the data for a subview in
     * studio we don't want to display all the record of the list view but only
     * the one set in the parent record.
     *
     * @private
     * @override
     */
    _loadData: function (parent) {
        if (parent.x2mField) {
            this.loadParams.static = true;
        }
        var result = this._super.apply(this, arguments);
        if (parent.x2mField) {
            this.loadParams.static = false;
        }
        return result;
    },
});

});
