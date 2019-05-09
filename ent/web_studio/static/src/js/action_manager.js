odoo.define('web_studio.ActionManager', function (require) {
"use strict";

var ActionManager = require('web.ActionManager');

var bus = require('web_studio.bus');

/**
 * Logic of the Studio action manager: the Studio client action (i.e.
 * "action_web_studio_action_editor") will always be pushed on top of another
 * controller, which corresponds to the edited action by Studio.
 */

ActionManager.include({
    custom_events: _.extend({}, ActionManager.prototype.custom_events, {
        'reload_action': '_onReloadAction',
    }),

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.studioControllerIndex = undefined;
        bus.on('edition_mode_entered', this, this._onEditionModeEntered);
        bus.on('studio_toggled', this, this._onStudioToggled);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    clearUncommittedChanges: function () {
        var currentController = this.getCurrentController();
        if (currentController && !currentController.widget) {
            // navigate with Studio will push a "fake" controller without widget
            // (see @_executeWindowAction) before doAction on the Studio action
            // but @_executeAction will call this function so no need to do
            // anything in this case
            return $.when();
        }
        return this._super.apply(this, arguments);
    },
    /**
     * Returns the action of the Studio controller in the controllerStack, i.e.
     * the action currently edited in Studio.
     *
     * @returns {Object|null}
     */
    getCurrentStudioAction: function () {
        var controllerID = this.controllerStack[this.studioControllerIndex];
        var controller = this.controllers[controllerID];
        return controller ? this.actions[controller.actionID] : null;
    },
    /**
     * Restores the action currently edited by Studio.
     *
     * @returns {Deferred}
     */
    restoreStudioAction: function () {
        var self = this;
        var studioControllerIndex = this.studioControllerIndex;
        var controllerID = this.controllerStack[studioControllerIndex];
        var controller = this.controllers[controllerID];
        var action = this.actions[controller.actionID];

        // find the index in the controller stack of the first controller
        // associated to the action to restore
        var index = _.findIndex(this.controllerStack, function(controllerID) {
            var controller = self.controllers[controllerID];
            return controller.actionID === action.jsID;
        });

        // reset to correctly update the breadcrumbs
        this.studioControllerIndex = undefined;

        var options = {
            additional_context: action.context,
            index: index,
            viewType: this.studioViewType,
        };
        if (this.studioViewType === 'form') {
            options.resID = action.env.currentId;
        }
        return this.doAction(action.id, options);
    },
    /**
     * Restores the first controller after Studio controller.
     */
    studioHistoryBack: function () {
        var controller = this.controllerStack[this.studioControllerIndex + 1];
        this._restoreController(controller);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Controllers pushed in the controller stack for actions flagged with
     * 'studioNavigation' don't have an instantiated widget, so in this case,
     * there is nothing to detach from the DOM (see @_executeWindowAction).
     *
     * @override
     * @private
     */
    _detachCurrentController: function () {
        var currentAction = this.getCurrentAction();
        if (currentAction && !currentAction.studioNavigation) {
            this._super.apply(this, arguments);
        }
    },
    /**
     * Overrides to deal with actions tagged for the Studio navigation by the
     * WebClient.
     *
     * @override
     * @private
     */
    _executeWindowAction: function (action, options) {
        if (action.studioNavigation) {
            // We don't call _pushController or super here to avoid destroying
            // the previous actions ; they will be destroyed afterwards (see
            // override of @_pushController). We just create a new controller
            // and push it in the controller stack.
            this._processStudioAction(action, options);
            this.actions[action.jsID] = action;
            var controller = {
                actionID: action.jsID,
                jsID: _.uniqueId('controller_'),
            };
            this.controllers[controller.jsID] = controller;
            this.controllerStack.push(controller.jsID);

            // as we are navigating through Studio (with a menu), reset the
            // breadcrumb index
            this.studioControllerIndex = 0;

            return $.when(action);

        }
        return this._super.apply(this, arguments);
    },
    /*
     * @override
     * @private
     */
    _getBreadcrumbs: function () {
        if (this.studioControllerIndex !== undefined) {
            // do not display the breadcrumbs from the action edited by Studio
            var stack = this.controllerStack;
            this.controllerStack = stack.slice(this.studioControllerIndex + 1);
            var result = this._super.apply(this, arguments);
            this.controllerStack = stack;
            return result;
        }
        return this._super.apply(this, arguments);
    },
    /**
     * @override
     * @private
     */
    _pushController: function (controller, options) {
        var length = this.controllerStack.length - 1;
        var toDestroy;
        if (options && options.studio_clear_breadcrumbs) {
            // we actually don't want to destroy the whole controller stack
            // but we want to keep the last controller, which is the one
            // associated to the action edited by Studio
            toDestroy = this.controllerStack.splice(0, length);
            this._removeControllers(toDestroy);
        } else if (options && options.studio_clear_studio_breadcrumbs) {
            toDestroy = this.controllerStack.splice(this.studioControllerIndex + 1);
            this._removeControllers(toDestroy);
        }
        return this._super.apply(this, arguments);
    },
    /**
     * @_executeWindowAction is overridden when navigating in Studio but some
     * processing in said function still needs to be done.
     *
     * @private
     * @param {Object} action
     * @param {Object} options
     */
    _processStudioAction: function (action, options) {
        // needed by ViewEditorManager when instanciating the ViewEditor
        action.env = this._generateActionEnv(action, options);

        // needed in _createViewController
        action.controllers = {};

        // similar to what is done in @_generateActionViews), but without
        // _loadViews - needed in Submenu and ActionEditor to have the same
        // structure than if the action was opened after being executed
        var views = _.map(action.views, function (view) {
            return {
                type: view[1],
                viewID: view[0],
            };
        });
        action._views = action.views;  // save the initial attribute
        action.views = views;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /*
     * @private
     * @param {string} viewType
     */
    _onEditionModeEntered: function (viewType) {
        if (viewType !== 'search') {
            this.studioViewType = viewType;
        }
    },
    /**
     * Overrides to let the event bubble if the push_state comes from Studio.
     *
     * @override
     * @private
     */
    _onPushState: function (ev) {
        if (!ev.data.studioPushState) {
            this._super.apply(this, arguments);
        }
    },
    /**
     * @private
     * @param {OdooEvent} ev
     * @param {string} ev.data.actionID
     */
    _onReloadAction: function (ev) {
        var self = this;
        var action = _.findWhere(this.actions, {id: ev.data.actionID});
        this._loadAction(action.id).then(function (result) {
            self._preprocessAction(result, {additional_context: action.context});
            self._processStudioAction(result, {});
            bus.trigger('action_changed', result);
            if (ev.data.def) {
                ev.data.def.resolve(result);
            }
        });
    },
    /**
     * @private
     * @param {string} mode
     */
    _onStudioToggled: function (mode) {
        if (mode === 'main') {
            // Studio has directly been opened on the action so the action to
            // restore is not the last one (which is Studio) but the one before
            this.studioControllerIndex = this.controllerStack.length - 2;
        }
    },
});

});
