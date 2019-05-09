odoo.define('web_studio.ActionEditorAction', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Dialog = require('web.Dialog');
var dom = require('web.dom');
var form_common = require('web.view_dialogs');
var session = require('web.session');

var ActionEditor = require('web_studio.ActionEditor');
var bus = require('web_studio.bus');
var NewViewDialog = require('web_studio.NewViewDialog');
var ViewEditorManager = require('web_studio.ViewEditorManager');

var _t = core._t;
var _lt = core._lt;

var ActionEditorAction = AbstractAction.extend({
    className: 'o_web_studio_client_action',
    custom_events: {
        'studio_default_view': '_onSetDefaultView',
        'studio_disable_view': '_onDisableView',
        'studio_edit_view': '_onEditView',
        'studio_new_view': '_onNewView',
        'studio_set_another_view': '_onSetAnotherView',
        'studio_edit_action': '_onEditAction',
    },
    /**
     * @constructor
     * @param {Object} options
     * @param {Object} options.action - action description
     * @param {Boolean} options.chatter_allowed
     * @param {boolean} [options.noEdit] - do not edit a view
     * @param {string} [options.viewType]
     * @param {Object} [options.x2mEditorPath]
     */
    init: function (parent, context, options) {
        this._super.apply(this, arguments);
        this.options = options;
        this.action = options.action;
        this.viewType = options.viewType;
        // We set the x2mEditorPath since when we click on the studio breadcrumb
        // a new view_editor_manager is instantiated and then the previous
        // x2mEditorPath is needed to reload the previous view_editor_manager
        // state.
        this.x2mEditorPath = options.x2mEditorPath;
    },
    /**
     * @override
     */
    willStart: function () {
        if (!this.action) {
            return $.Deferred().reject();
        }
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        var def;
        this.set('title', _t('Studio'));
        if (this.options.noEdit) {
            // click on "Views" in menu
            this.action_editor = new ActionEditor(this, this.action);
            def = this.action_editor.appendTo(this.$el);
        } else {
            // directly edit the view instead of displaying all views
            def = this._editView(this.viewType);
        }
        return $.when(def, this._super.apply(this, arguments)).then(function () {
            self._pushState();
            bus.trigger('studio_main', self.action);
            if (!self.options.noEdit) {
                // TODO: try to put it in editView
                bus.trigger('edition_mode_entered', self.viewType);
            }
        });
    },
    /**
     * @override
     */
    on_attach_callback: function () {
        this._super.apply(this, arguments);
        this.isInDOM = true;
        if (this.view_editor) {
            this.view_editor.on_attach_callback();
        }
    },
    /**
     * @override
     */
    on_detach_callback: function () {
        this._super.apply(this, arguments);
        this.isInDOM = false;
        if (this.view_editor) {
            this.view_editor.on_detach_callback();
        }
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Object} action
     * @param {String} view_type
     * @param {Object} args
     * @returns {Deferred}
     */
    _addViewType: function (action, view_type, args) {
        var self = this;
        var def = $.Deferred();
        core.bus.trigger('clear_cache');
        this._rpc({
            route: '/web_studio/add_view_type',
            params: {
                action_type: action.type,
                action_id: action.id,
                res_model: action.res_model,
                view_type: view_type,
                args: args,
                context: session.user_context,
            },
        }).then(function (result) {
            if (result !== true) {
                var params = {
                    action: action,
                    callback: function () {
                        self._editAction(action, args).then(function (result) {
                            def.resolve(result);
                        });
                    },
                };
                if (view_type === 'gantt' || view_type === 'calendar') {
                    params.view_type = view_type;
                    new NewViewDialog(self, params).open();
                } else if (view_type === 'cohort') {
                    params.view_type = view_type;
                    params.mandatory_stop_date = true;
                    new NewViewDialog(self, params).open();
                } else {
                    var message = result;
                    if (!message) {
                        message = _lt("Creating this type of view is not currently supported in Studio.");
                    }
                    Dialog.alert(self, message);
                    def.reject();
                }
            } else {
                return self._reloadAction(action.id)
                    .then(def.resolve.bind(def))
                    .fail(def.reject.bind(def));
            }
        });
        return def;
    },
    /**
     * @private
     * @param {Object} action
     * @param {Object} args
     * @returns {Deferred}
     */
    _editAction: function (action, args) {
        var self = this;
        core.bus.trigger('clear_cache');
        return this._rpc({
            route: '/web_studio/edit_action',
            params: {
                action_type: action.type,
                action_id: action.id,
                args: args,
                context: session.user_context,
            },
        }).then(function (result) {
            if (result !== true) {
                Dialog.alert(self, result);
            } else {
                return self._reloadAction(action.id);
            }
        });
    },
    /**
     * @private
     * @param {String} view_type
     */
    _editView: function (view_type) {
        var self = this;
        var options = {};

        var views = this.action._views || this.action.views;
        views = views.slice();
        // search is not in action.view
        options.load_filters = true;
        var searchview_id = this.action.search_view_id && this.action.search_view_id[0];
        views.push([searchview_id || false, 'search']);

        var view = _.find(views, function (el) {
            return el[1] === view_type;
        });
        if (!view) {
            // see action manager
            view = views[0];
        }
        var view_id = view[0];
        this.viewType = view[1];

        // the default view needs to be created before `loadViews` or the
        // renderer will not be aware that a new view exists
        var defs = [this._getStudioViewArch(this.action.res_model, this.viewType, view_id)];
        if (this.viewType === 'form') {
            defs.push(this._isChatterAllowed());
        }
        return $.when.apply($, defs).then(function () {
            // add studio in loadViews context to retrieve groups server-side
            var context = _.extend({}, self.action.context, {studio: true});
            var loadViewDef = self.loadViews(self.action.res_model, context, views, options);
            return loadViewDef.then(function (fields_views) {
                var viewEnv = _.defaults({}, self.action.env, {
                    currentId: self.action.env.ids && self.action.env.ids[0],
                });
                var params = {
                    fields_view: fields_views[self.viewType],
                    viewType: self.viewType,
                    env: viewEnv,
                    chatter_allowed: self.chatter_allowed,
                    studio_view_id: self.studioView.studio_view_id,
                    studio_view_arch: self.studioView.studio_view_arch,
                    x2mEditorPath: self.x2mEditorPath,
                };
                self.view_editor = new ViewEditorManager(self, params);

                var fragment = document.createDocumentFragment();
                return self.view_editor.appendTo(fragment).then(function () {
                    if (self.action_editor) {
                        dom.detach([{widget: self.action_editor}]);
                    }
                    dom.append(self.$el, [fragment], {
                        in_DOM: self.isInDOM,
                        callbacks: [{widget: self.view_editor}],
                    });
                });
            });
        });
    },
    /**
     * @private
     * @param {String} model
     * @param {String} view_type
     * @param {Integer} view_id
     * @returns {Deferred}
     */
    _getStudioViewArch: function (model, view_type, view_id) {
        var self = this;
        core.bus.trigger('clear_cache');
        return this._rpc({
            route: '/web_studio/get_studio_view_arch',
            params: {
                model: model,
                view_type: view_type,
                view_id: view_id,
                context: session.user_context,
            },
        }).then(function (studioView) {
            self.studioView = studioView;
        });
    },
    /**
     * @private
     * Determines whether the model
     * that will be edited supports mail_thread
     * @returns {Deferred}
     */
    _isChatterAllowed: function () {
        var self = this;
        var res_model = this.action.res_model;
        return this._rpc({
            route: '/web_studio/chatter_allowed',
            params: {
                model: res_model,
            }
        }).then(function (isChatterAllowed) {
            self.chatter_allowed = isChatterAllowed;
        });
    },

    /**
     * @private
     */
    _pushState: function () {
        // as there is no controller, we need to update the state manually
        var state = {
            action: this.action.id,
            model: this.action.res_model,
            view_type: this.viewType,
        };
        // TODO: necessary?
        if (this.action.context) {
            var active_id = this.action.context.active_id;
            if (active_id) {
                state.active_id = active_id;
            }
            var active_ids = this.action.context.active_ids;
            // we don't push active_ids if it's a single element array containing the active_id
            // to make the url shorter in most cases
            if (active_ids && !(active_ids.length === 1 && active_ids[0] === active_id)) {
                state.active_ids = this.action.context.active_ids.join(',');
            }
        }
        this.trigger_up('push_state', {
            state: state,
            studioPushState: true,  // see action_manager @_onPushState
        });
    },
    /**
     * @private
     * @param {Integer} actionID
     * @returns {Deferred}
     */
    _reloadAction: function (actionID) {
        var def = $.Deferred();
        this.trigger_up('reload_action', {actionID: actionID, def: def});
        return def;
    },
    /**
     * @private
     * @param {String} view_mode
     * @param {Integer} view_id
     * @returns {Deferred}
     */
    _setAnotherView: function (view_mode, view_id) {
        var self = this;
        var def = this._setAnotherViewRPC(this.action.id, view_mode, view_id);
        return def.then(function (result) {
            return self.do_action('action_web_studio_action_editor', {
                action: result,
                noEdit: true,
            });
        });
    },
    /**
     * @private
     * @param {Integer} action_id
     * @param {String} view_mode
     * @param {Integer} view_id
     * @returns {Deferred}
     */
    _setAnotherViewRPC: function (action_id, view_mode, view_id) {
        var self = this;
        core.bus.trigger('clear_cache');
        return this._rpc({
            route: '/web_studio/set_another_view',
            params: {
                action_id: action_id,
                view_mode: view_mode,
                view_id: view_id,
                context: session.user_context,
            },
        }).then(function () {
            return self._reloadAction(action_id);
        });
    },
    /**
     * @private
     * @param {String} view_mode
     * @returns {Deferred}
     */
    _writeViewMode: function (view_mode, initial_view_mode) {
        var self = this;
        var def = this._editAction(this.action, {view_mode: view_mode});
        return def.then(function (result) {
            if (initial_view_mode) {
                result.initial_view_types = initial_view_mode.split(',');
            }
            return self.do_action('action_web_studio_action_editor', {
                action: result,
                noEdit: true,
            });
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {OdooEvent} event
     */
    _onDisableView: function (event) {
        var view_type = event.data.view_type;
        var view_mode = _.without(this.action.view_mode.split(','), view_type);

        this._writeViewMode(view_mode.toString());
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onEditAction: function (event) {
        var self = this;

        var args = event.data.args;
        if (!args) { return; }

        this._editAction(this.action, args).then(function (result) {
            self.action = result;
        });
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onEditView: function (event) {
        var view_type = event.data.view_type;
        this._editView(view_type).then(function () {
            bus.trigger('edition_mode_entered', view_type);
        });
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onNewView: function (event) {
        var self = this;
        var view_type = event.data.view_type;
        var view_mode = this.action.view_mode + ',' + view_type;
        var def = this._addViewType(this.action, view_type, {
            view_mode: view_mode,
        });
        def.then(function (result) {
            self.do_action('action_web_studio_action_editor', {
                action: result,
                viewType: view_type,
            });
        });
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onSetAnotherView: function (event) {
        var self = this;
        var view_type = event.data.view_type;

        new form_common.SelectCreateDialog(this, {
            res_model: 'ir.ui.view',
            title: _t('Select a view'),
            disable_multiple_selection: true,
            no_create: true,
            domain: [
                ['type', '=', view_type],
                ['mode', '=', 'primary'],
                ['model', '=', this.action.res_model],
            ],
            on_selected: function (records) {
                self._setAnotherView(view_type, records[0].id);
            }
        }).open();
    },
    /**
     * @private
     * @param {OdooEvent} event
     */
    _onSetDefaultView: function (event) {
        var view_type = event.data.view_type;
        var view_mode = _.without(this.action.view_mode.split(','), view_type);
        view_mode.unshift(view_type);
        view_mode = view_mode.toString();

        this._writeViewMode(view_mode, this.action.view_mode);
    },
});

core.action_registry.add('action_web_studio_action_editor', ActionEditorAction);

});
