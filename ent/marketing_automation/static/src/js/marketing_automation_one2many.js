odoo.define('marketing_automation.hierarchy_kanban', function (require) {
"use strict";

var core = require('web.core');
var Domain = require('web.Domain');
var DomainSelector = require('web.DomainSelector');
var Dialog = require('web.Dialog');
var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
var KanbanRenderer = require('web.KanbanRenderer');
var KanbanRecord = require('web.KanbanRecord');
var registry = require('web.field_registry');

var _t = core._t;

var HierarchyKanban = FieldOne2Many.extend({
    custom_events: _.extend({}, FieldOne2Many.prototype.custom_events, {
        'add_child_act': '_onAddChild',
    }),

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------


    /**
     * @private
     * @override
     * @returns {Deferred}
     */
    _render: function () {
        var self = this;
        this._setHierarchyData();
        if (!this.renderer) {
            this.renderer = new HierarchyKanbanRenderer(this, this.value, {
                arch: this.view.arch,
                viewType: 'kanban',
                record_options: {
                    editable: false,
                    deletable: false,
                    read_only_mode: this.isReadonly,
                },
            });
            this.renderer.appendTo(this.$el);
        }
        return this._super.apply(this, arguments).then(function () {
            // Move control_panel at bottom
            if (self.control_panel) {
                return self.control_panel.$el.appendTo(self.$el);
            }
        });
    },
    /**
     * Transforms the widget value into parent and child relationship.
     *
     * @private
     */
    _setHierarchyData: function () {
        var data = this.value.data;
        this.allData = data;
        var parentMap = {};
        this.value.data = _.filter(data, function (record) {
            parentMap[record.res_id] = record;
            record.children = [];
            return record.data.parent_id === false;
        });
        _.each(data, function (record) {
            if (record.data.parent_id && parentMap[record.data.parent_id.res_id]) {
                parentMap[record.data.parent_id.res_id].children.push(record);
            }
        });
    },
    /**
     * The implicit contract on this.value.data has been broken by _setHierarchyData
     * so we need to make sure that we generated the right command by checking
     * if the record id is in all_data (which is what this.value.data should be)
     *
     * @override
     * @private
     */
    _setValue: function (value, options) {
        if (value.operation === 'ADD' && _.some(this.allData, {id: value.id})) {
            value.operation = 'UPDATE';
        }
        return this._super(value, options);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Opens the record with custom context and adds the child activity on saved.
     *
     * @private
     */
    _onAddChild: function (params) {
        var self = this;
        var context = _.extend(this.record.getContext(this.recordParams), params.data);
        this.trigger_up('open_one2many_record', {
            domain: this.record.getDomain(this.recordParams),
            context: context,
            field: this.field,
            fields_view: this.attrs.views && this.attrs.views.form,
            parentID: this.value.id,
            viewInfo: this.view,
            on_saved: function (record) {
                self._setValue({operation: 'ADD', id: record.id});
            },
        });
    },
});

var HierarchyKanbanRenderer = KanbanRenderer.extend({
    /**
     * Renders kanban records with its children.
     *
     * @private
     * @override
     */
    _renderUngrouped: function (fragment, records) {
        var self = this;
        _.each(records || this.state.data, function (record) {
            var kanbanRecord = new HierarchyKanbanRecord(self, record, self.recordOptions);
            self.widgets.push(kanbanRecord);
            kanbanRecord.appendTo(fragment);
            if (record.children.length) {
                var newFragment = kanbanRecord.$('.o_hierarchy_children');
                self._renderUngrouped(newFragment, record.children);
            }
        });
    }
});

var HierarchyKanbanRecord = KanbanRecord.extend({
    events: _.extend({}, KanbanRecord.prototype.events, {
        'click .o_ma_switch span': '_onClickSwitch',
        'click .o_add_child': '_onKanbanActionClicked',
    }),

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Renders DomainSelector.
     *
     * @private
     * @returns {Deferred}
     */
    _renderDomainSelector: function () {
        if (!this.domainSelector) {
            var domainModel = this.state.data.model_name;
            var domain = Domain.prototype.stringToArray(this.state.data.domain);
            this.domainSelector = new DomainSelector(this, domainModel, domain, {
                readonly: true,
                filters: {},
            });
            return this.domainSelector.prependTo(this.$('.o_ma_card:first > .o_pane_filter'));
        }
        return $.when();
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Displays dialog if user try to delete record having children.
     * Triggers custom actions related to add child activities.
     *
     * @private
     * @override
     * @param {Event} event
     */
    _onKanbanActionClicked: function (event) {
        event.stopPropagation();
        event.preventDefault();
        var type = $(event.currentTarget).data('type') || 'button';
        if (type === 'delete' && this.state.children.length) {
            new Dialog(this, {
                title: _t('Delete Activity'),
                buttons: [{
                    text: _t('Delete All'),
                    classes: 'btn-primary',
                    close: true,
                    click: this._super.bind(this, event)
                }, {
                    text: _t('Discard'),
                    close: true
                }],
                $content: $('<div>', {
                    html: _t("This Activity has a dependant child activity. 'DELETE ALL' will delete all child activities."),
                }),
            }).open();
        } else if (_.indexOf(['act', 'mail_open', 'mail_not_open', 'mail_reply', 'mail_not_reply', 'mail_click', 'mail_not_click', 'mail_bounce'], type) !== -1) {
            // If we are in edit mode and we create a new kanban record,
            // we cannot add a child activity for this record before saving.
            if (this.id) {
                this.trigger_up('add_child_act', {
                    'default_parent_id': this.id,
                    'default_trigger_type': type
                });
            } else {
                this.do_warn(_t('Please save the campaign to add a child activity'));
            }
        } else {
            this._super.apply(this, arguments);
        }
    },

    /**
     * Handles toggling of kanban pane.
     *
     * @private
     * @param {Event} event
     */
    _onClickSwitch: function (event) {
        event.stopPropagation();
        var self = this;
        $(event.currentTarget).siblings().removeClass('active');
        $(event.currentTarget).addClass('active');
        var mode = $(event.currentTarget).data('mode');
        this._renderDomainSelector().then(function () {
            self.$('.o_ma_card:first > [class*="o_pane_"]').addClass('d-none');
            self.$('.o_ma_card:first > .o_pane_' + mode).removeClass('d-none');
        });
    }
});

registry.add('hierarchy_kanban', HierarchyKanban);

return {
    HierarchyKanbanRecord: HierarchyKanbanRecord,
    HierarchyKanbanRenderer: HierarchyKanbanRenderer,
    HierarchyKanban: HierarchyKanban,
};

});
