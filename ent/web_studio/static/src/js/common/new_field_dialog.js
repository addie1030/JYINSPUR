odoo.define('web_studio.NewFieldDialog', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var relational_fields = require('web.relational_fields');
var ModelFieldSelector = require('web.ModelFieldSelector');
var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');

var _t = core._t;
var qweb = core.qweb;
var Many2one = relational_fields.FieldMany2One;

// TODO: refactor this file

var NewFieldDialog = Dialog.extend(StandaloneFieldManagerMixin, {
    template: 'web_studio.NewFieldDialog',
    events: {
        'click .o_web_studio_selection_new_value button': '_onAddSelectionValue',
        'keyup .o_web_studio_selection_new_value > input': '_onAddSelectionValue',
        'click .o_web_studio_edit_selection_value': '_onEditSelectionValue',
        'click .o_web_studio_remove_selection_value': '_onRemoveSelectionValue',
    },
    /**
     * @constructor
     * @param {String} model_name
     * @param {Object} field
     * @param {Object} fields
     */
    init: function (parent, model_name, field, fields) {
        this.model_name = model_name;
        this.type = field.type;
        this.field = field;
        this.order = field.order;
        this.followRelations = field.followRelations || function (field) {return true;};
        this.filter = field.filter || function (field) {return true;};
        this.filters = field.filters;

        if (this.type === 'selection') {
            this.selection = this.field.selection && this.field.selection.slice() || [];
        }

        this.fields = fields;
        var options = _.extend({
            title: _t('Field Properties'),
            size: 'small',
            buttons: [{
                text: _t("Confirm"),
                classes: 'btn-primary',
                click: this._onSave.bind(this),
            }, {
                text: _t("Cancel"),
                close: true,
            }],
        }, options);
        this._super(parent, options);
        StandaloneFieldManagerMixin.init.call(this);
    },
    /**
     * @override
     */
    renderElement: function () {
        this._super.apply(this, arguments);

        if (this.type === 'selection') {
           this.$('.o_web_studio_selection_editor').sortable({
                axis: 'y',
                containment: '.o_web_studio_field_dialog_form',
                items: '> li',
                helper: 'clone',
                handle: '.input-group',
                opacity: 0.6,
                stop: this._resequenceSelection.bind(this),
           });
       }
    },
    /**
     * @override
     */
    start: function() {
        var self = this;
        var defs = [];
        var record;
        var options = {
            mode: 'edit',
        };

        this.$modal.addClass('o_web_studio_field_modal');

        if (this.type === 'one2many') {
            defs.push(this.model.makeRecord('ir.model.fields', [{
                name: 'field',
                relation: 'ir.model.fields',
                type: 'many2one',
                domain: [['relation', '=', this.model_name], ['ttype', '=', 'many2one']],
            }], {
                'field': {
                    can_create: false,
                }
            }).then(function (recordID) {
                record = self.model.get(recordID);
                self.many2one_field = new Many2one(self, 'field', record, options);
                self._registerWidget(recordID, 'field', self.many2one_field);
                self.many2one_field.nodeOptions.no_create_edit = !config.debug;
                self.many2one_field.appendTo(self.$('.o_many2one_field'));
            }));
        } else if (_.contains(['many2many', 'many2one'], this.type)) {
            defs.push(this.model.makeRecord('ir.model', [{
                name: 'model',
                relation: 'ir.model',
                type: 'many2one',
                domain: [['transient', '=', false], ['abstract', '=', false]]
            }]).then(function (recordID) {
                record = self.model.get(recordID);
                self.many2one_model = new Many2one(self, 'model', record, options);
                self._registerWidget(recordID, 'model', self.many2one_model);
                self.many2one_model.nodeOptions.no_create_edit = !config.debug;
                self.many2one_model.appendTo(self.$('.o_many2one_model'));
            }));
        } else if (this.type === 'related') {
            // This restores default modal height (bootstrap) and allows field selector to overflow
            this.$el.css("overflow", "visible").closest(".modal-dialog").css("height", "auto");
            var field_options = {
                order: this.order,
                filter: this.filter,
                followRelations: this.followRelations,
                fields: this.fields, //_.filter(this.fields, this.filter),
                readonly: false,
                filters: this.filters,
            };
            this.fieldSelector = new ModelFieldSelector(this, this.model_name, [], field_options);
            defs.push(this.fieldSelector.appendTo(this.$('.o_many2one_field')));
        }

        defs.push(this._super.apply(this, arguments));
        return $.when.apply($, defs);
    },

    /**
     * @private
     * @param {Event} e
     */
    _resequenceSelection: function () {
        var self = this;
        var newSelection = [];
        this.$('.o_web_studio_selection_editor li').each(function (index, u) {
            var value = u.dataset.value;
            var string = _.find(self.selection, function(el) {
                return el[0] === value;
            })[1];
            newSelection.push([value, string]);
        });
        this.selection = newSelection;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} e
     */
    _onAddSelectionValue: function (e) {
        if (e.type === "keyup" && e.which !== $.ui.keyCode.ENTER) { return; }

        var $input = this.$(".o_web_studio_selection_new_value input");
        var string = $input.val().trim();

        if (string && !_.find(this.selection, function(el) {return el[1] === string; })) {
            // add a new element
            this.selection.push([string, string]);
        }
        this.renderElement();
        this.$('input').focus();
    },
    /**
     * @private
     * @param {Event} e
     */
    _onEditSelectionValue: function (e) {
        var self = this;
        var val = this.$(e.currentTarget).closest('li')[0].dataset.value;
        var element = _.find(this.selection, function(el) {return el[0] === val; });
        new Dialog(this, {
            title: _t('Edit Value'),
            size: 'small',
            $content: $(qweb.render('web_studio.SelectionValues.edit', {
                debug: config.debug,
                element: element,
            })),
            buttons: [
                {text: _t('Confirm'), classes: 'btn-primary', close: true, click: function () {
                    // the value edition is only available in debug mode
                    var newValue = config.debug && this.$('input#o_selection_value').val() || val;
                    var newString = this.$('input#o_selection_label').val();
                    var index = self.selection.indexOf(element);
                    if (index >= 0) {
                        self.selection.splice(index, 1);
                        self.selection.splice(index, 0, [newValue, newString]);
                        self.renderElement();
                    }
                }},
                {text: _t('Close'), close: true},
            ],
        }).open();
    },
    /**
     * @private
     * @param {Event} e
     */
    _onRemoveSelectionValue: function (e) {
        var self = this;
        var msg = _t(
            "Do you really want to remove this value? " +
            "All the records with this value will be updated accordingly."
        );
        Dialog.confirm(self, msg, {
            title: _t("Warning"),
            confirm_callback: function () {
                var val = $(e.target).closest('li')[0].dataset.value;
                var element = _.find(self.selection, function(el) {return el[0] === val; });
                var index = self.selection.indexOf(element);
                if (index >= 0) {
                    self.selection.splice(index, 1);
                }
                self.renderElement();
            },
        });
    },
    /**
     * @private
     */
    _onSave: function () {
        var values = {};
        if (this.type === 'one2many') {
            if (!this.many2one_field.value) {
                this.trigger_up('warning', {title: _t('You must select a related field')});
                return;
            }
            values.relation_field_id = this.many2one_field.value.res_id;
        } else if (_.contains(['many2many', 'many2one'], this.type)) {
            if (!this.many2one_model.value) {
                this.trigger_up('warning', {title: _t('You must select a relation')});
                return;
            }
            values.relation_id = this.many2one_model.value.res_id;
            values.field_description = this.many2one_model.m2o_value;
        } else if (this.type === 'selection') {
            values.selection = JSON.stringify(this.selection);
        } else if (this.type === 'related') {
            var selectedField = this.fieldSelector.getSelectedField();
            if (!selectedField) {
                this.trigger_up('warning', {title: _t('You must select a related field')});
                return;
            }
            values.string = selectedField.string;
            values.model = selectedField.model;
            values.related = this.fieldSelector.chain.join('.');
            values.type = selectedField.type;
            if (_.contains(['many2one', 'many2many'], selectedField.type)) {
                values.relation = selectedField.relation;
            } else if (selectedField.type === 'one2many') {
                values.relational_model = selectedField.model;
            } else if (selectedField.type === 'selection') {
                values.selection = selectedField.selection;
            } else if (selectedField.type === 'monetary') {
                // find the associated currency field on the related model in
                // case there is no currency field on the current model
                var currencyField = _.find(_.last(this.fieldSelector.pages), function (el) {
                    return el.name === 'currency_id' || el.name === 'x_currency_id';
                });
                if (currencyField) {
                    var chain = this.fieldSelector.chain.slice();
                    chain.splice(chain.length - 1, 1, currencyField.name);
                    values._currency = chain.join('.');
                }
            }
        }
        this.trigger('field_default_values_saved', values);
    },
});

return NewFieldDialog;

});
