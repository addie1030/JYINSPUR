odoo.define('web_studio.ViewEditorSidebar', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var Dialog = require('web.Dialog');
var DomainSelectorDialog = require("web.DomainSelectorDialog");
var Domain = require("web.Domain");
var field_registry = require('web.field_registry');
var relational_fields = require('web.relational_fields');
var session = require("web.session");
var Widget = require('web.Widget');
var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');
var view_components = require('web_studio.view_components');
var pyUtils = require('web.py_utils');

var form_component_widget_registry = view_components.registry;
var _t = core._t;
var Many2ManyTags = relational_fields.FieldMany2ManyTags;

return Widget.extend(StandaloneFieldManagerMixin, {
    template: 'web_studio.ViewEditorSidebar',
    events: {
        'click .o_web_studio_new:not(.inactive)':            '_onTab',
        'click .o_web_studio_view':                          '_onTab',
        'click .o_web_studio_xml_editor':                    '_onXMLEditor',
        'click .o_display_view .o_web_studio_parameters':    '_onViewParameters',
        'click .o_display_field .o_web_studio_parameters':   '_onFieldParameters',
        'click .o_display_view .o_web_studio_defaults':      '_onDefaultValues',
        'change #show_invisible':                            '_onShowInvisibleToggled',
        'click .o_web_studio_remove':                        '_onElementRemoved',
        'change .o_display_view input':                      '_onViewChanged',
        'change .o_display_view select':                     '_onViewChanged',
        'click .o_web_studio_edit_selection_values':         '_onSelectionValues',
        'change .o_display_field input[data-type="attributes"]': '_onElementChanged',
        'change .o_display_field select':                    '_onElementChanged',
        'change .o_display_field input[data-type="field_name"]': '_onFieldNameChanged',
        'focus .o_display_field input[data-type="attributes"][name="domain"]': '_onDomainEditor',
        'change .o_display_field [data-type="default_value"]': '_onDefaultValueChanged',
        'change .o_display_page input':                      '_onElementChanged',
        'change .o_display_label input':                     '_onElementChanged',
        'change .o_display_group input':                     '_onElementChanged',
        'change .o_display_button input':                    '_onElementChanged',
        'change .o_display_button select':                   '_onElementChanged',
        'click .o_display_button .o_img_upload':             '_onUploadRainbowImage',
        'click .o_display_button .o_img_reset':              '_onRainbowImageReset',
        'change .o_display_filter input':                    '_onElementChanged',
        'change .o_display_chatter input[data-type="email_alias"]': '_onEmailAliasChanged',
        'click .o_web_studio_attrs':                         '_onDomainAttrs',
        'focus .o_display_filter input#domain':              '_onDomainEditor',
    },
    /**
     * @constructor
     * @param {Widget} parent
     * @param {Object} params
     * @param {Object} params.state
     * @param {Object} params.view_type
     * @param {Object} params.model_name
     * @param {Object} params.fields
     * @param {Object} params.fields_in_view
     * @param {Object} params.fields_not_in_view
     * @param {boolean} params.isEditingX2m
     * @param {Array} params.renamingAllowedFields
     */
    init: function (parent, params) {
        this._super.apply(this, arguments);
        StandaloneFieldManagerMixin.init.call(this);
        this.debug = config.debug;

        this.view_type = params.view_type;
        this.model_name = params.model_name;
        this.isEditingX2m = params.isEditingX2m;
        this.editorData = params.editorData;
        this.renamingAllowedFields = params.renamingAllowedFields;

        this.fields = params.fields;
        this.orderered_fields = _.sortBy(this.fields, function (field) {
            return field.string.toLowerCase();
        });
        this.fields_in_view = params.fields_in_view;
        this.fields_not_in_view = params.fields_not_in_view;

        this.GROUPABLE_TYPES = ['many2one', 'char', 'boolean', 'selection', 'date', 'datetime'];
        // FIXME: At the moment, it's not possible to set default value for these types
        this.NON_DEFAULT_TYPES = ['many2one', 'many2many', 'one2many', 'binary'];
        this.MODIFIERS_IN_NODE_AND_ATTRS = ['readonly', 'invisible', 'required'];

        this.state = params.state || {};

        if (this.state.node && (this.state.node.tag === 'field' || this.state.node.tag === 'filter')) {
            // deep copy of field because the object is modified
            // in this widget and this shouldn't impact it
            var field = jQuery.extend(true, {}, this.fields[this.state.attrs.name]);

            // field_registry contains all widgets
            // We want to filter these widgets based on field types
            field.field_widgets = _.chain(field_registry.map)
                .pairs()
                .filter(function (arr) {
                    return _.contains(arr[1].prototype.supportedFieldTypes, field.type) && arr[0].indexOf('.') < 0;
                })
                .map(function (array) {
                    return array[0];
                })
                .sortBy()
                .value();

            this.state.field = field;

            // only for list & tree view
            this.state.modifiers = this.state.attrs.modifiers || {};
            this._computeFieldAttrs();

            // get infos from the widget:
            // - the possibilty to set a placeholder for this widget
            // For example: it's not possible to set it on a boolean field.
            var Widget = this.state.attrs.Widget;
            this.has_placeholder = Widget && Widget.prototype.has_placeholder || false;
        }
        // Upload image related stuff
        if (this.state.node && this.state.node.tag === 'button') {
            this.is_stat_btn = this.state.node.attrs.class === 'oe_stat_button';
            if (!this.is_stat_btn) {
                this.state.node.widget = "image";
                this.user_id = session.uid;
                this.fileupload_id = _.uniqueId('o_fileupload');
                $(window).on(this.fileupload_id, this._onUploadRainbowImageDone.bind(this));
            }
        }
    },
    /**
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments).then(this._render.bind(this));
    },
    /**
     * @override
     */
    destroy: function () {
        $(window).off(this.fileupload_id);
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Transform an array domain into its string representation.
     *
     * @param {Array} domain
     * @returns {String}
     */
    domainToStr: function (domain) {
        return Domain.prototype.arrayToString(domain);
    },
    /**
     * @param {string} fieldName
     * @returns {boolean} if the field can be renamed
     */
    isRenamingAllowed: function (fieldName) {
        return _.contains(this.renamingAllowedFields, fieldName);
    },
    /**
     * @param {String} value
     * @returns {Boolean}
     */
    isTrue: function (value) {
        return value !== 'false' && value !== 'False';
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _changeFieldGroup: function () {
        var record = this.model.get(this.groupsHandle);
        var new_attrs = {};
        new_attrs.groups = record.data.groups.res_ids;
        this.trigger_up('view_change', {
            type: 'attributes',
            structure: 'edit_attributes',
            node: this.state.node,
            new_attrs: new_attrs,
        });
    },
    /**
     * @private
     */
    _computeFieldAttrs: function () {
        /* Compute field attributes.
         * These attributes are either taken from modifiers or attrs
         * so attrs store their combinaison.
         */
        this.state.attrs.invisible = this.state.modifiers.invisible || this.state.modifiers.column_invisible;
        this.state.attrs.readonly = this.state.modifiers.readonly;
        this.state.attrs.string = this.state.attrs.string || this.state.field.string;
        this.state.attrs.help = this.state.attrs.help || this.state.field.help;
        this.state.attrs.placeholder = this.state.attrs.placeholder || this.state.field.placeholder;
        this.state.attrs.required = this.state.field.required || this.state.modifiers.required;
        this.state.attrs.domain = this.state.attrs.domain || this.state.field.domain;
        this.state.attrs.context = this.state.attrs.context || this.state.field.context;
        this.state.attrs.related = this.state.field.related ? this.state.field.related.join('.'): false;
    },
    /**
     * @private
     * @param {Object} modifiers
     * @returns {Object}
     */
    _getNewAttrsFromModifiers: function (modifiers) {
        var self = this;
        var newAttributes = {};
        var attrs = [];
        var originNodeAttr = this.state.modifiers;
        var originSubAttrs =  pyUtils.py_eval(this.state.attrs.attrs || '{}', this.editorData);
        _.each(modifiers, function (value, key) {
                var keyInNodeAndAttrs = _.contains(self.MODIFIERS_IN_NODE_AND_ATTRS, key);
                var keyFromView = key in originSubAttrs;
                var trueValue = value === true || _.isEqual(value, []);
                var isOriginNodeAttr = key in originNodeAttr;

                if (keyInNodeAndAttrs && !isOriginNodeAttr && trueValue) { // modifier always applied, use modifier attribute
                    newAttributes[key] = "1";
                } else if (keyFromView || !trueValue) { // modifier not applied or under certain condition, remove modifier attribute and use attrs if any
                    newAttributes[key] = "";
                    if (value !== false) {
                        attrs.push(_.str.sprintf("\"%s\": %s", key, Domain.prototype.arrayToString(value)));
                    }
                }
        });
        newAttributes.attrs = _.str.sprintf("{%s}", attrs.join(", "));
        return newAttributes;
    },
    /**
     * Render additional sections according to the sidebar mode
     * i.e. the new & existing field if 'new', etc.
     *
     * @private
     */
    _render: function () {
        var self = this;
        if (this.state.mode === 'new') {
            this._renderNewSections();
            this.$('.o_web_studio_component').on("drag", _.throttle(function (event, ui) {
                self.trigger_up('drag_component', {position: {pageX: event.pageX, pageY: event.pageY}, $helper: ui.helper});
            }, 200));
        } else if (this.state.mode === 'properties') {
            return this._renderWidgetsM2MGroups();
        }
    },
    /**
     * @private
     */
    _renderNewSections: function () {
        var self = this;
        var widget_classes;
        var form_widgets;
        var $section;
        var $sectionTitle;
        var $sidebar_content = this.$('.o_web_studio_sidebar_content');

        // Components
        if (_.contains(['form', 'search'], this.view_type)) {
            widget_classes = form_component_widget_registry.get(this.view_type + '_components');
            form_widgets = widget_classes.map(function (FormComponent) {
                return new FormComponent(self);
            });
            $sectionTitle = $('<h3>', {
                html: _t('Components'),
            });
            $section = this._renderSection(form_widgets);
            $section.addClass('o_web_studio_new_components');
            $sidebar_content.append($sectionTitle, $section);
        }
        // New Fields
        if (_.contains(['list', 'form'], this.view_type)) {
            widget_classes = form_component_widget_registry.get('new_field');
            form_widgets = widget_classes.map(function (FormComponent) {
                return new FormComponent(self);
            });
            $sectionTitle = $('<h3>', {
                html: _t('New Fields'),
            });
            $section = this._renderSection(form_widgets);
            $section.addClass('o_web_studio_new_fields');
            $sidebar_content.append($sectionTitle, $section);
        }

        // Existing Fields
        var FormComponent = form_component_widget_registry.get('existing_field');
        if (this.view_type === 'search') {
            form_widgets = _.map(this.fields, function (field) {
                return new FormComponent(self, field.name, field.string, field.type, field.store);
            });
        } else {
            var fields = _.sortBy(this.fields_not_in_view, function (field) {
                return field.string.toLowerCase();
            });
            form_widgets = _.map(fields, function (field) {
                return new FormComponent(self, field.name, field.string, field.type);
            });
        }
        $sectionTitle = $('<h3>', {
            html: _t('Existing Fields'),
        });
        $section = this._renderSection(form_widgets);
        $section.addClass('o_web_studio_existing_fields');
        $sidebar_content.append($sectionTitle, $section);
    },
    /**
     * @private
     * @param {Object} form_widgets
     * @returns {JQuery}
     */
    _renderSection: function (form_widgets) {
        var $components_container = $('<div>').addClass('o_web_studio_field_type_container');
        form_widgets.forEach(function (form_component) {
            form_component.appendTo($components_container);
        });
        return $components_container;
    },
    /**
     * @private
     */
    _renderWidgetsM2MGroups: function () {
        var self = this;
        var studio_groups = this.state.attrs.studio_groups && JSON.parse(this.state.attrs.studio_groups);
        return this.model.makeRecord('ir.model.fields', [{
            name: 'groups',
            fields: [{
                name: 'id',
                type: 'integer',
            }, {
                name: 'display_name',
                type: 'char',
            }],
            relation: 'res.groups',
            type: 'many2many',
            value: studio_groups,
        }]).then(function (recordID) {
            self.groupsHandle = recordID;
            var record = self.model.get(self.groupsHandle);
            var options = {
                idForLabel: 'groups',
                mode: 'edit',
                no_quick_create: true,
            };
            var many2many = new Many2ManyTags(self, 'groups', record, options);
            self._registerWidget(self.groupsHandle, 'groups', many2many);
            return many2many.appendTo(self.$('.o_groups'));
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onDefaultValues: function () {
        this.trigger_up('open_defaults');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onDefaultValueChanged: function (ev) {
        var self = this;
        var $input = $(ev.currentTarget);
        var value = $input.val();
        if (value !== this.state.default_value) {
            this.trigger_up('default_value_change', {
                field_name: this.state.attrs.name,
                value: value,
                on_fail: function () {
                    $input.val(self.default_value);
                }
            });
        }
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onDomainAttrs: function (ev) {
        ev.preventDefault();
        var modifier = ev.currentTarget.dataset.type;

        // Add id to the list of usable fields
        var fields = this.fields_in_view;
        if (!fields.id) {
            fields = _.extend({
                id: {
                    searchable: true,
                    string: "ID",
                    type: "integer",
                },
            }, fields);
        }

        var dialog = new DomainSelectorDialog(this, this.model_name, _.isArray(this.state.modifiers[modifier]) ? this.state.modifiers[modifier] : [], {
            readonly: false,
            fields: fields,
            size: 'medium',
            operators: ["=", "!=", "<", ">", "<=", ">=", "in", "not in", "set", "not set"],
            followRelations: false,
            debugMode: session.debug,
            $content: $(_.str.sprintf(
                _t("<div><p>The <strong>%s</strong> property is only applied to records matching this filter.</p></div>"),
                modifier
            )),
        }).open();
        dialog.on("domain_selected", this, function (e) {
            var newModifiers = _.extend({}, this.state.modifiers);
            newModifiers[modifier] = e.data.domain;
            var new_attrs = this._getNewAttrsFromModifiers(newModifiers);
            this.trigger_up('view_change', {
                type: 'attributes',
                structure: 'edit_attributes',
                node: this.state.node,
                new_attrs: new_attrs,
            });
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onDomainEditor: function (ev) {
        ev.preventDefault();
        var $input = $(ev.currentTarget);

        // If we want to edit a filter domain, we don't have a specific
        // field to work on but we want a domain on the current model.
        var model = this.state.node.tag === 'filter' ? this.model_name : this.state.field.relation;
        var dialog = new DomainSelectorDialog(this, model, $input.val(), {
            readonly: false,
            debugMode: session.debug,
        }).open();
        dialog.on("domain_selected", this, function (e) {
            $input.val(Domain.prototype.arrayToString(e.data.domain)).change();
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onElementChanged: function (ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (attribute && $input.attr('type') !== 'file') {
            var new_attrs = {};
            // rainbow attribute on button needs JSON value, so on change of any rainbow related
            // attributes, re-form rainbow attribute in required format, excluding falsy/empty
            // values
            if (attribute.match('^rainbow')) {
                if (this.$('input#rainbow').is(':checked')) {
                    new_attrs.effect = JSON.stringify(_.pick({
                            message: this.$('input#rainbow_message').val(),
                            img_url: this.$('input#rainbow_img_url').val(),
                            fadeout: this.$('select#rainbow_fadeout').val(),
                        }, _.identity)
                    );
                } else {
                    new_attrs.effect = 'False';
                }
            } else if (attribute === 'img_size') {
                var newOptions = _.extend({}, this.state.attrs.options);
                var size = parseInt($input.val());
                newOptions.size = [size, size];
                new_attrs.options = JSON.stringify(newOptions);
            } else if (attribute === 'widget') {
                // reset widget options
                var widget = $input.val();
                new_attrs = {
                    widget: widget,
                    options: '',
                };
                if (widget === 'image') {
                    // add small as a default size for image widget
                    new_attrs.options = JSON.stringify({size: [90, 90]});
                }
            } else if ($input.attr('type') === 'checkbox') {
                if (!_.contains(this.MODIFIERS_IN_NODE_AND_ATTRS, attribute)) {
                    if ($input.is(':checked')) {
                        new_attrs[attribute] = $input.data('leave-empty') === 'checked' ? '': 'True';
                    } else {
                        new_attrs[attribute] = $input.data('leave-empty') === 'unchecked' ? '': 'False';
                    }
                } else {
                    var newModifiers = _.extend({}, this.state.modifiers);
                    newModifiers[attribute] = $input.is(':checked');
                    new_attrs = this._getNewAttrsFromModifiers(newModifiers);
                }
            } else {
                new_attrs[attribute] = $input.val();
            }
            this.trigger_up('view_change', {
                type: 'attributes',
                structure: 'edit_attributes',
                node: this.state.node,
                new_attrs: new_attrs,
            });
        }
    },
    /**
     * @private
     */
    _onElementRemoved: function () {
        var self = this;
        var elementName = this.state.node.tag;
        if (elementName === 'div' && this.state.node.attrs.class === 'oe_chatter') {
            elementName = 'chatter';
        }
        var message = _.str.sprintf(_t('Are you sure you want to remove this %s from the view?'), elementName);

        Dialog.confirm(this, message, {
            confirm_callback: function () {
                self.trigger_up('view_change', {
                    type: 'remove',
                    structure: 'remove',
                    node: self.state.node,
                });
            }
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onEmailAliasChanged: function (ev) {
        var $input = $(ev.currentTarget);
        var value = $input.val();
        if (value !== this.state.email_alias) {
            this.trigger_up('email_alias_change', {
                value: value,
            });
        }
    },
    /**
     * @private
     */
    _onFieldChanged: function () {
        StandaloneFieldManagerMixin._onFieldChanged.apply(this, arguments);
        this._changeFieldGroup();
    },
    /**
     * Renames the field after confirmation from user.
     *
     * @private
     * @param {Event} ev
     */
    _onFieldNameChanged: function (ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (!attribute) {
            return;
        }
        var newName = 'x_studio_' + $input.val();
        var message;
        if (newName.match(/[^a-z0-9_]/g) || newName.length >= 54) {
            message = _.str.sprintf(_t('The new name can contain only a to z lower letters, numbers and _, with ' +
                'a maximum of 53 characters.'));
            Dialog.alert(this, message);
            return;
        }
        if (newName in this.fields) {
            message = _.str.sprintf(_t('A field with the same name already exists.'));
            Dialog.alert(this, message);
            return;
        }
        this.trigger_up('field_renamed', {
            oldName: this.state.node.attrs.name,
            newName: newName,
        });
    },
    /**
     * @private
     */
    _onFieldParameters: function () {
        this.trigger_up('open_field_form', {field_name: this.state.attrs.name});
    },
    /**
     * @private
     */
    _onRainbowImageReset: function () {
        this.$('input#rainbow_img_url').val('');
        this.$('input#rainbow_img_url').trigger('change');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onSelectionValues: function (ev) {
        ev.preventDefault();
        this.trigger_up('field_edition', {
            node: this.state.node,
        });
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onShowInvisibleToggled: function (ev) {
        this.state.show_invisible = !!$(ev.currentTarget).is(":checked");
        this.trigger_up('toggle_form_invisible', {show_invisible : this.state.show_invisible});
    },
    /**
     * @private
     */
    _onTab: function (ev) {
        var mode = $(ev.currentTarget).attr('name');
        this.trigger_up('sidebar_tab_changed', {
            mode: mode,
        });
    },
    /**
     * @private
     */
    _onUploadRainbowImage: function () {
        var self = this;
        this.$('input.o_input_file').on('change', function () {
            self.$('form.o_form_binary_form').submit();
        });
        this.$('input.o_input_file').click();
    },
    /**
     * @private
     * @param {Event} event
     * @param {Object} result
     */
    _onUploadRainbowImageDone: function (event, result) {
        this.$('input#rainbow_img_url').val(_.str.sprintf('/web/content/%s', result.id));
        this.$('input#rainbow_img_url').trigger('change');
    },
    /**
     * @private
     * @param {Event} ev
     */
    _onViewChanged: function (ev) {
        var $input = $(ev.currentTarget);
        var attribute = $input.attr('name');
        if (attribute === 'enable_stage') {
            if ($input.is(':checked')) {
                this.trigger_up('view_change', {
                    structure: 'enable_stage',
                });
            } else {
                this.trigger_up('view_change', {
                    type: 'attributes',
                    structure: 'view_attribute',
                    new_attrs: {
                        default_group_by: '',
                    },
                });
            }
        } else if (attribute) {
            var new_attrs = {};
            if ($input.attr('type') === 'checkbox') {
                if (($input.is(':checked') && !$input.data('inverse')) || (!$input.is(':checked') && $input.data('inverse'))) {
                    new_attrs[attribute] = $input.data('leave-empty') === 'checked' ? '': 'true';
                } else {
                    new_attrs[attribute] = $input.data('leave-empty') === 'unchecked' ? '': 'false';
                }
            } else {
                new_attrs[attribute] = $input.val();
            }
            this.trigger_up('view_change', {
                type: 'attributes',
                structure: 'view_attribute',
                new_attrs: new_attrs,
            });
        }
    },
    /**
     * @private
     */
    _onViewParameters: function () {
        this.trigger_up('open_record_form_view');
    },
    /**
     * @private
     */
    _onXMLEditor: function () {
        this.trigger_up('open_xml_editor');
    },
});

});
