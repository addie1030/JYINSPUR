odoo.define('sign.views_custo', function(require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var KanbanController = require("web.KanbanController");
    var KanbanColumn = require("web.KanbanColumn");
    var KanbanRecord = require("web.KanbanRecord");
    var ListController = require("web.ListController");

    var _t = core._t;

    KanbanController.include(_make_custo("button.o-kanban-button-new"));
    ListController.include(_make_custo(".o_list_button_add"));

    KanbanColumn.include({
        /**
         * @override
         */
        init: function () {
            this._super.apply(this, arguments);
            if (this.modelName === "sign.request") {
                this.draggable = false;
            }
        },
    });

    KanbanRecord.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * On click of kanban open send signature wizard
         * @override
         * @private
         */
        _openRecord: function () {
            var self = this;
            if (this.modelName === 'sign.template') {
                this.do_action("sign.action_sign_send_request", {
                    additional_context: {active_id: self.recordData.id}
                });
            } else if (this.modelName === 'sign.request') {
                this._rpc({
                    model: 'sign.request',
                    method: 'go_to_document',
                    args: [self.recordData.id],
                }).then(function(action) {
                    self.do_action(action);
                });
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

    function _make_custo(selector_button) {
        return {
            renderButtons: function () {
                this._super.apply(this, arguments);
                if (this.modelName === "sign.template") {
                    this._sign_upload_file_button();
                    this.$buttons.find('button.o_button_import').hide();
                } else if (this.modelName === "sign.request") {
                    this._sign_create_request_button();
                    this.$buttons.find('button.o_button_import').hide();
                }
            },

            _sign_upload_file_button: function () {
                var self = this;
                this.$buttons.find(selector_button).text(_t("Send a Request")).off("click").on("click", function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    _sign_upload_file.call(self, true);
                });
                this.$buttons.find(selector_button).after(
                    $('<button class="btn btn-link o-kanban-button-new ml8" type="button">'+ _t('UPLOAD A PDF TEMPLATE') +'</button>')
                    .off('click')
                    .on('click', function (e) {
                        e.preventDefault();
                        e.stopImmediatePropagation();
                        _sign_upload_file.call(self);
                }));
            },

            _sign_create_request_button: function () {
                var self = this;
                this.$buttons.find(selector_button).text(_t("Request a Signature")).off("click").on("click", function (e) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    _sign_create_request.call(self);
                });
            },
        };
    }

    function _sign_upload_file(inactive) {
        var self = this;
        var $upload_input = $('<input type="file" name="files[]"/>');
        $upload_input.on('change', function (e) {
            var f = e.target.files[0];
            var reader = new FileReader();

            reader.onload = function(e) {
                var args;
                if (inactive) {
                    args = [f.name, e.target.result, false];
                } else {
                    args = [f.name, e.target.result];
                }
                self._rpc({
                        model: 'sign.template',
                        method: 'upload_template',
                        args: args,
                    })
                    .then(function(data) {
                        self.do_action({
                            type: "ir.actions.client",
                            tag: 'sign.Template',
                            name: _t("New Template"),
                            context: {
                                id: data.template,
                            },
                        });
                    })
                    .always(function() {
                        $upload_input.removeAttr('disabled');
                        $upload_input.val("");
                    });
            };
            try {
                reader.readAsDataURL(f);
            } catch (e) {
                console.warn(e);
            }
        });

        $upload_input.click();
    }

    function _sign_create_request() {
        this.do_action("sign.sign_template_action");
    }
});

odoo.define('sign.template', function(require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var config = require('web.config');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var PDFIframe = require('sign.PDFIframe');
    var sign_utils = require('sign.utils');

    var _t = core._t;

    var SignItemCustomPopover = Widget.extend({
        template: 'sign.sign_item_custom_popover',
        events: {
            'click .o_sign_delete_field_button': function(e) {
                this.$currentTarget.popover("hide");
                this.$currentTarget.trigger('itemDelete');
            },
            'click .o_sign_validate_field_button': function (e) {
                this.hide();
            }
        },

        init: function(parent, parties, options) {
            options = options || {};

            this.title = options.title || _t("Customize Field");
            this._super(parent, options);
            //TODO: Add buttons for save, discard and remove.
            this.parties = parties;
            this.debug = config.debug;
        },

        start: function() {
            this.$responsibleSelect = this.$('.o_sign_responsible_select');
            sign_utils.resetResponsibleSelectConfiguration();

            var self = this;
            return this._super().then(function() {
                sign_utils.setAsResponsibleSelect(self.$responsibleSelect.find('select'), self.$currentTarget.data('responsible'), self.parties);
                self.$('input[type="checkbox"]').prop('checked', self.$currentTarget.data('required'));

                self.$('#o_sign_name').val(self.$currentTarget.data('name') );
                self.title = self.title + ' <span class="fa fa-long-arrow-right"/> ' + self.$currentTarget.prop('field-type') + ' Field';
            });

        },

        create: function($targetEl) {
            var self = this;
            this.$currentTarget = $targetEl;
            this.$elPopover = $("<div class='o_sign_item_popover'/>");
            this.appendTo(this.$elPopover).then(function() {
                var options = {
                    title: self.title,
                    content: function () {
                        return self.$el;
                    },
                    html: true,
                    placement: 'right',
                    trigger:'focus',
                };
                self.$currentTarget.popover(options).one('inserted.bs.popover', function (e) {
                    $('.popover').addClass('o_popover_offset');
                });
                self.$currentTarget.popover("toggle");

            });
        },
        hide: function() {
            this.$currentTarget.popover("hide");
            var resp = parseInt(this.$responsibleSelect.find('select').val());
            var required = this.$('input[type="checkbox"]').prop('checked');
            var name = this.$('#o_sign_name').val();
            this.getParent().currentRole = resp;
            this.$currentTarget.data({responsible: resp, required: required, name: name}).trigger('itemChange');
        }
    });

    var InitialAllPagesDialog = Dialog.extend({
        template: 'sign.initial_all_pages_dialog',

        init: function(parent, parties, options) {
            options = options || {};

            options.title = options.title || _t("Add Initials");
            options.size = options.size || "medium";

            if(!options.buttons) {
                options.buttons = [];
                options.buttons.push({text: _t('Add once'), classes: 'btn-primary', close: true, click: function(e) {
                    this.updateTargetResponsible();
                    this.$currentTarget.trigger('itemChange');
                }});
                options.buttons.push({text: _t('Add on all pages'), classes: 'btn-secondary', close: true, click: function(e) {
                    this.updateTargetResponsible();
                    this.$currentTarget.draggable('destroy').resizable('destroy');
                    this.$currentTarget.trigger('itemClone');
                }});
            }

            this._super(parent, options);

            this.parties = parties;
        },

        start: function() {
            this.$responsibleSelect = this.$('.o_sign_responsible_select_initials');

            var self = this;
            return this._super.apply(this, arguments).then(function() {
                sign_utils.setAsResponsibleSelect(self.$responsibleSelect.find('select'), self.getParent().currentRole, self.parties);
            });
        },

        open: function($signatureItem) {
            this.$currentTarget = $signatureItem;
            this._super.apply(this, arguments);
        },

        updateTargetResponsible: function() {
            var resp = parseInt(this.$responsibleSelect.find('select').val());
            this.getParent().currentRole = resp;
            this.$currentTarget.data('responsible', resp);
        },
    });

    var EditablePDFIframe = PDFIframe.extend({
        init: function() {
            this._super.apply(this, arguments);

            this.customPopovers = {};
            this.events = _.extend(this.events || {}, {
                'itemChange .o_sign_sign_item': function(e) {
                    this.updateSignItem($(e.target));
                    this.$iframe.trigger('templateChange');
                },

                'itemDelete .o_sign_sign_item': function(e) {
                    this.deleteSignItem($(e.target));
                    this.$iframe.trigger('templateChange');
                },

                'itemClone .o_sign_sign_item': function(e) {
                    var $target = $(e.target);
                    this.updateSignItem($target);

                    page_loop:
                    for(var i = 1 ; i <= this.nbPages ; i++) {
                        for(var j = 0 ; j < this.configuration[i].length ; j++) {
                            if(this.types[this.configuration[i][j].data('type')].type === 'signature') {
                                continue page_loop;
                            }
                        }

                        var $newElem = $target.clone(true);
                        this.enableCustom($newElem);
                        this.configuration[i].push($newElem);
                    }

                    this.deleteSignItem($target);
                    this.refreshSignItems();
                    this.$iframe.trigger('templateChange');
                },
            });
        },

        doPDFPostLoad: function() {
            var self = this;
            this.fullyLoaded.then(function() {
                if(self.editMode) {
                    if(self.$iframe.prop('disabled')) {
                        self.$('#viewer').fadeTo('slow', 0.75);
                        var $div = $('<div/>').css({
                            position: "absolute",
                            top: 0,
                            left: 0,
                            width: "100%",
                            height: "100%",
                            'z-index': 110,
                            opacity: 0.75
                        });
                        self.$('#viewer').css('position', 'relative').prepend($div);
                        $div.on('click mousedown mouseup mouveover mouseout', function(e) {
                            return false;
                        });
                    } else {
                        self.$hBarTop = $('<div/>');
                        self.$hBarBottom = $('<div/>');
                        self.$hBarTop.add(self.$hBarBottom).css({
                            position: 'absolute',
                            "border-top": "1px dashed orange",
                            width: "100%",
                            height: 0,
                            "z-index": 103,
                            left: 0
                        });
                        self.$vBarLeft = $('<div/>');
                        self.$vBarRight = $('<div/>');
                        self.$vBarLeft.add(self.$vBarRight).css({
                            position: 'absolute',
                            "border-left": "1px dashed orange",
                            width: 0,
                            height: "10000px",
                            "z-index": 103,
                            top: 0
                        });

                        var typesArr = _.toArray(self.types);
                        var $fieldTypeButtons = $(core.qweb.render('sign.type_buttons', {sign_item_types: typesArr}));
                        self.$fieldTypeToolbar = $('<div/>').addClass('o_sign_field_type_toolbar');
                        self.$fieldTypeToolbar.prependTo(self.$('#viewerContainer'));
                        $fieldTypeButtons.appendTo(self.$fieldTypeToolbar).draggable({
                            cancel: false,
                            helper: function(e) {
                                var type = self.types[$(this).data('item-type-id')];
                                var $signatureItem = self.createSignItem(type, true, self.currentRole, 0, 0, type.default_width, type.default_height, '');

                                if(!e.ctrlKey) {
                                    self.$('.o_sign_sign_item').removeClass('ui-selected');
                                }
                                $signatureItem.addClass('o_sign_sign_item_to_add ui-selected');

                                self.$('.page').first().append($signatureItem);
                                self.updateSignItem($signatureItem);
                                $signatureItem.css('width', $signatureItem.css('width')).css('height', $signatureItem.css('height')); // Convert % to px
                                $signatureItem.detach();

                                return $signatureItem;
                            }
                        });
                        $fieldTypeButtons.each(function(i, el) {
                            self.enableCustomBar($(el));
                        });

                        self.$('.page').droppable({
                            accept: '*',
                            tolerance: 'touch',
                            drop: function(e, ui) {
                                if(!ui.helper.hasClass('o_sign_sign_item_to_add')) {
                                    return true;
                                }

                                var $parent = $(e.target);
                                var pageNo = parseInt($parent.prop('id').substr('pageContainer'.length));

                                ui.helper.removeClass('o_sign_sign_item_to_add');
                                var $signatureItem = ui.helper.clone(true).removeClass().addClass('o_sign_sign_item o_sign_sign_item_required');

                                var posX = (ui.offset.left - $parent.find('.textLayer').offset().left) / $parent.innerWidth();
                                var posY = (ui.offset.top - $parent.find('.textLayer').offset().top) / $parent.innerHeight();
                                $signatureItem.data({posx: posX, posy: posY});

                                self.configuration[pageNo].push($signatureItem);
                                self.refreshSignItems();
                                self.updateSignItem($signatureItem);
                                self.enableCustom($signatureItem);

                                self.$iframe.trigger('templateChange');

                                if(self.types[$signatureItem.data('type')].type === 'initial') {
                                    (new InitialAllPagesDialog(self, self.parties)).open($signatureItem);
                                }

                                return false;
                            }
                        });

                        self.$('#viewer').selectable({
                            appendTo: self.$('body'),
                            filter: '.o_sign_sign_item',
                        });

                        $(document).add(self.$el).on('keyup', function(e) {
                            if(e.which !== 46) {
                                return true;
                            }

                            self.$('.ui-selected').each(function(i, el) {
                                self.deleteSignItem($(el));
                            });
                            self.$iframe.trigger('templateChange');
                        });
                    }

                    self.$('.o_sign_sign_item').each(function(i, el) {
                        self.enableCustom($(el));
                    });
                }
            });

            this._super.apply(this, arguments);
        },

        enableCustom: function($signatureItem) {
            var self = this;

            $signatureItem.prop('field-type', this.types[$signatureItem.data('type')].name);
            var itemId = $signatureItem.data('itemId');

            var $configArea = $signatureItem.find('.o_sign_config_area');

            $configArea.find('.o_sign_responsible_display').off('mousedown').on('mousedown', function(e) {
                e.stopPropagation();
                self.$('.ui-selected').removeClass('ui-selected');
                $signatureItem.addClass('ui-selected');

                _.each(_.keys(self.customPopovers), function(keyId) {
                    if (keyId != itemId && self.customPopovers[keyId] && ((keyId && itemId) || (keyId != 'undefined' && !itemId))) {
                        self.customPopovers[keyId].$currentTarget.popover('hide');
                        self.customPopovers[keyId] = false;
                    }
                });
                if (self.customPopovers[itemId]) {
                    self.customPopovers[itemId].$currentTarget.popover('hide');
                    self.customPopovers[itemId] = false;
                } else {
                    self.customPopovers[itemId] = new SignItemCustomPopover(self, self.parties, {'field_type': $signatureItem[0]['field-type']});
                    self.customPopovers[itemId].create($signatureItem);
                }
            });

            $configArea.find('.fa.fa-arrows').off('mouseup').on('mouseup', function(e) {
                if(!e.ctrlKey) {
                    self.$('.o_sign_sign_item').filter(function(i) {
                        return (this !== $signatureItem[0]);
                    }).removeClass('ui-selected');
                }
                $signatureItem.toggleClass('ui-selected');
            });

            $signatureItem.draggable({containment: "parent", handle: ".fa-arrows"}).resizable({containment: "parent"}).css('position', 'absolute');

            $signatureItem.off('dragstart resizestart').on('dragstart resizestart', function(e, ui) {
                if(!e.ctrlKey) {
                    self.$('.o_sign_sign_item').removeClass('ui-selected');
                }
                $signatureItem.addClass('ui-selected');
            });

            $signatureItem.off('dragstop').on('dragstop', function(e, ui) {
                $signatureItem.data({
                    posx: Math.round((ui.position.left / $signatureItem.parent().innerWidth())*1000)/1000,
                    posy: Math.round((ui.position.top / $signatureItem.parent().innerHeight())*1000)/1000,
                });
            });

            $signatureItem.off('resizestop').on('resizestop', function(e, ui) {
                $signatureItem.data({
                    width: Math.round(ui.size.width/$signatureItem.parent().innerWidth()*1000)/1000,
                    height: Math.round(ui.size.height/$signatureItem.parent().innerHeight()*1000)/1000,
                });
            });

            $signatureItem.on('dragstop resizestop', function(e, ui) {
                self.updateSignItem($signatureItem);
                self.$iframe.trigger('templateChange');
                $signatureItem.removeClass('ui-selected');
            });

            this.enableCustomBar($signatureItem);
        },

        enableCustomBar: function($item) {
            var self = this;

            $item.on('dragstart resizestart', function(e, ui) {
                start.call(self, ui.helper);
            });
            $item.find('.o_sign_config_area .fa.fa-arrows').on('mousedown', function(e) {
                start.call(self, $item);
                process.call(self, $item, $item.position());
            });
            $item.on('drag resize', function(e, ui) {
                process.call(self, ui.helper, ui.position);
            });
            $item.on('dragstop resizestop', function(e, ui) {
                end.call(self);
            });
            $item.find('.o_sign_config_area .fa.fa-arrows').on('mouseup', function(e) {
                end.call(self);
            });

            function start($helper) {
                this.$hBarTop.detach().insertAfter($helper).show();
                this.$hBarBottom.detach().insertAfter($helper).show();
                this.$vBarLeft.detach().insertAfter($helper).show();
                this.$vBarRight.detach().insertAfter($helper).show();
            }
            function process($helper, position) {
                this.$hBarTop.css('top', position.top);
                this.$hBarBottom.css('top', position.top+parseFloat($helper.css('height'))-1);
                this.$vBarLeft.css('left', position.left);
                this.$vBarRight.css('left', position.left+parseFloat($helper.css('width'))-1);
            }
            function end() {
                this.$hBarTop.hide();
                this.$hBarBottom.hide();
                this.$vBarLeft.hide();
                this.$vBarRight.hide();
            }
        },

        updateSignItem: function($signatureItem) {
            this._super.apply(this, arguments);

            if(this.editMode) {
                var responsibleName = this.parties[$signatureItem.data('responsible')].name;
                $signatureItem.find('.o_sign_responsible_display').text(responsibleName).prop('title', responsibleName);
            }
        },
    });

    var Template = AbstractAction.extend(ControlPanelMixin, {
        className: "o_sign_template",

        events: {
            'click .fa-pencil': function(e) {
                this.$templateNameInput.focus().select();
            },

            'input .o_sign_template_name_input': function(e) {
                this.$templateNameInput.attr('size', this.$templateNameInput.val().length);
            },

            'change .o_sign_template_name_input': function(e) {
                this.saveTemplate();
                if(this.$templateNameInput.val() === "") {
                    this.$templateNameInput.val(this.initialTemplateName);
                }
            },

            'keydown .o_sign_template_name_input': function (e) {
                if (e.keyCode === 13) {
                    this.$templateNameInput.blur();
                }
            },

            'templateChange iframe.o_sign_pdf_iframe': function(e) {
                this.saveTemplate();
            },

            'click .o_sign_duplicate_sign_template': function(e) {
                this.saveTemplate(true);
            },
        },

        go_back_to_kanban: function() {
            return this.do_action("sign.sign_template_action", {
                clear_breadcrumbs: true,
            });
        },

        init: function(parent, options) {
            this._super.apply(this, arguments);

            if(options.context.id === undefined) {
                return;
            }

            this.templateID = options.context.id;
            this.rolesToChoose = {};

            var self = this;
            var $sendButton = $('<button/>', {html: _t("Send"), type: "button"})
                .addClass('btn btn-primary')
                .on('click', function() {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'sign.send.request',
                        views: [[false, 'form']],
                        target: 'new',
                        context: {
                            'active_id': self.templateID,
                        },
                    });
                });
            var $shareButton = $('<button/>', {html: _t("Share"), type: "button"})
                .addClass('btn btn-secondary')
                .on('click', function() {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'sign.template.share',
                        views: [[false, 'form']],
                        target: 'new',
                        context: {
                            'active_id': self.templateID,
                        },
                    });
                });
            this.cp_content = {$buttons: $sendButton.add($shareButton)};
        },

        willStart: function() {
            if(this.templateID === undefined) {
                return this._super.apply(this, arguments);
            }
            return $.when(this._super(), this.perform_rpc());
        },

        perform_rpc: function() {
            var self = this;

            var defTemplates = this._rpc({
                    model: 'sign.template',
                    method: 'read',
                    args: [[this.templateID]],
                })
                .then(function prepare_template(template) {
                    template = template[0];
                    self.sign_template = template;
                    self.has_sign_requests = (template.sign_request_ids.length > 0);

                    var defSignItems = self._rpc({
                            model: 'sign.item',
                            method: 'search_read',
                            args: [[['template_id', '=', template.id]]],
                            kwargs: {context: session.user_context},
                        })
                        .then(function (sign_items) {
                            self.sign_items = sign_items;
                        });
                    var defIrAttachments = self._rpc({
                            model: 'ir.attachment',
                            method: 'read',
                            args: [[template.attachment_id[0]], ['mimetype', 'name', 'datas_fname']],
                            kwargs: {context: session.user_context},
                        })
                        .then(function(attachment) {
                            attachment = attachment[0];
                            self.sign_template.attachment_id = attachment;
                            self.isPDF = (attachment.mimetype.indexOf('pdf') > -1);
                        });

                    return $.when(defSignItems, defIrAttachments);
                });

            var defParties = this._rpc({
                    model: 'sign.item.role',
                    method: 'search_read',
                    kwargs: {context: session.user_context},
                })
                .then(function(parties) {
                    self.sign_item_parties = parties;
                });

            var defItemTypes = this._rpc({
                    model: 'sign.item.type',
                    method: 'search_read',
                    kwargs: {context: session.user_context},
                })
                .then(function(types) {
                    self.sign_item_types = types;
                });

            return $.when(defTemplates, defParties, defItemTypes);
        },

        start: function() {
            if(this.templateID === undefined) {
                return this.go_back_to_kanban();
            }
            this.initialize_content();
            if(this.$('iframe').length) {
                core.bus.on('DOM_updated', this, init_iframe);
            }

            $('body').on('click', function (e) {
                $('div.popover').each(function () {
                    if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                        $(this).find('.o_sign_validate_field_button').click();
                    }
                });
            });

            return this._super();

            function init_iframe() {
                if(this.$el.parents('html').length && !this.$el.parents('html').find('.modal-dialog').length) {
                    var self = this;
                    framework.blockUI({overlayCSS: {opacity: 0}, blockMsgClass: 'o_hidden'});
                    this.iframeWidget = new EditablePDFIframe(this,
                                                              '/web/image/' + this.sign_template.attachment_id.id,
                                                              true,
                                                              {
                                                                  parties: this.sign_item_parties,
                                                                  types: this.sign_item_types,
                                                                  signatureItems: this.sign_items,
                                                              });
                    return this.iframeWidget.attachTo(this.$('iframe')).then(function() {
                        framework.unblockUI();
                        self.iframeWidget.currentRole = self.sign_item_parties[0].id;
                    });
                }
            }
        },

        initialize_content: function() {
            this.$el.append(core.qweb.render('sign.template', {widget: this}));

            this.$('iframe,.o_sign_template_name_input').prop('disabled', this.has_sign_requests);

            this.$templateNameInput = this.$('.o_sign_template_name_input').first();
            this.$templateNameInput.trigger('input');
            this.initialTemplateName = this.$templateNameInput.val();

            this.refresh_cp();
        },

        do_show: function() {
            this._super();

            var self = this; // The iFrame cannot be detached, so we 'restart' the widget
            return this.perform_rpc().then(function() {
                if(self.iframeWidget) {
                    self.iframeWidget.destroy();
                    self.iframeWidget = undefined;
                }
                self.$el.empty();
                self.initialize_content();
            });
        },

        refresh_cp: function() {
            this.update_control_panel({
                cp_content: this.cp_content,
                search_view_hidden: true,
                clear: true
            });
        },

        prepareTemplateData: function() {
            this.rolesToChoose = {};
            var data = {}, newId = 0;
            var configuration = (this.iframeWidget)? this.iframeWidget.configuration : {};
            for(var page in configuration) {
                for(var i = 0 ; i < configuration[page].length ; i++) {
                    var resp = configuration[page][i].data('responsible');

                    data[configuration[page][i].data('item-id') || (newId--)] = {
                        'type_id': configuration[page][i].data('type'),
                        'required': configuration[page][i].data('required'),
                        'name': configuration[page][i].data('name'),
                        'responsible_id': resp,
                        'page': page,
                        'posX': configuration[page][i].data('posx'),
                        'posY': configuration[page][i].data('posy'),
                        'width': configuration[page][i].data('width'),
                        'height': configuration[page][i].data('height'),
                    };

                    this.rolesToChoose[resp] = this.iframeWidget.parties[resp];
                }
            }
            return data;
        },

        saveTemplate: function(duplicate) {
            duplicate = (duplicate === undefined)? false : duplicate;

            var data = this.prepareTemplateData();
            var $majInfo = this.$('.o_sign_template_saved_info').first();

            var self = this;
            this._rpc({
                    model: 'sign.template',
                    method: 'update_from_pdfviewer',
                    args: [this.templateID, !!duplicate, data, this.$templateNameInput.val() || this.initialTemplateName],
                })
                .then(function(templateID) {
                    if(!templateID) {
                        Dialog.alert(self, _t('Somebody is already filling a document which uses this template'), {
                            confirm_callback: function() {
                                self.go_back_to_kanban();
                            },
                        });
                    }

                    if(duplicate) {
                        self.do_action({
                            type: "ir.actions.client",
                            tag: 'sign.Template',
                            name: _t("Duplicated Template"),
                            context: {
                                id: templateID,
                            },
                        });
                    } else {
                        $majInfo.stop().css('opacity', 1).animate({'opacity': 0}, 1500);
                    }
                });
        },
    });

    core.action_registry.add('sign.Template', Template);
});

odoo.define('sign.DocumentBackend', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var core = require('web.core');
    var framework = require('web.framework');
    var AbstractAction = require('web.AbstractAction');
    var Document = require('sign.Document');

    var _t = core._t;

    var DocumentBackend = AbstractAction.extend(ControlPanelMixin, {
        className: 'o_sign_document',

        go_back_to_kanban: function () {
            return this.do_action("sign.sign_request_action", {
                clear_breadcrumbs: true,
            });
        },

        init: function (parent, options) {
            this._super.apply(this, arguments);
            if(options.context.id === undefined) {
                return;
            }

            this.documentID = options.context.id;
            this.token = options.context.token;
            this.create_uid = options.context.create_uid;
            this.state = options.context.state;

            var self = this;

            this.$downloadButton = $('<a/>', {html: _t("Download Document")}).addClass('btn btn-primary o_hidden');
            this.cp_content = {$buttons: this.$downloadButton};
        },

        start: function () {
            var self = this;
            if(this.documentID === undefined) {
                return this.go_back_to_kanban();
            }
            var def = this._rpc({
                route: '/sign/get_document/' + this.documentID + '/' + this.token,
                params: {message: this.message}
            }).then(function(html) {
                self.$el.append($(html.trim()));

                var $cols = self.$('.col-lg-4').toggleClass('col-lg-6 col-lg-4');
                var $buttonsContainer = $cols.first().remove();

                var url = $buttonsContainer.find('.o_sign_download_document_button').attr('href');
                self.$downloadButton.attr('href', url).toggleClass('o_hidden', !url);

                var init_page = function() {
                    if(self.$el.parents('html').length) {
                        self.refresh_cp();
                        framework.blockUI({overlayCSS: {opacity: 0}, blockMsgClass: 'o_hidden'});
                        var def;
                        if(!self.documentPage) {
                            self.documentPage = new (self.get_document_class())(self);
                            def = self.documentPage.attachTo(self.$el);
                        } else {
                            def = self.documentPage.initialize_iframe();
                        }
                        def.then(function() {
                            framework.unblockUI();
                        });
                    }
                };
                core.bus.on('DOM_updated', null, init_page);
            });
            return $.when(this._super(), def);
        },

        get_document_class: function () {
            return Document;
        },

        refresh_cp: function () {
            this.update_control_panel({
                cp_content: this.cp_content,
                search_view_hidden: true,
                clear: true
            });
        },
    });

    return DocumentBackend;
});

odoo.define('sign.document_edition', function(require) {
    'use strict';

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var session = require('web.session');
    var DocumentBackend = require('sign.DocumentBackend');
    var sign_utils = require('sign.utils');

    var _t = core._t;

    var EditableDocumentBackend = DocumentBackend.extend({
        events: {
            'click .o_sign_resend_access_button': function(e) {
                var $envelope = $(e.target);
                this._rpc({
                        model: 'sign.request.item',
                        method: 'resend_access',
                        args: [parseInt($envelope.parent('.o_sign_signer_status').data('id'))],
                    })
                    .then(function() { $envelope.html(_t("Resent !")); });
            },
        },

        init: function(parent, options) {
            this._super.apply(this, arguments);

            var self = this;

            this.is_author = (this.create_uid === session.uid);
            this.is_sent = (this.state === 'sent');

            if (options && options.context && options.context.sign_token) {
                var $signButton = $('<button/>', {html: _t("Sign Document"), type: "button", 'class': 'btn btn-primary'});
                $signButton.on('click', function () {
                    self.do_action({
                        type: "ir.actions.client",
                        tag: 'sign.SignableDocument',
                        name: _t('Sign'),
                    }, {
                        additional_context: _.extend({}, options.context, {
                            token: options.context.sign_token,
                        }),
                    });
                });
                this.cp_content.$buttons = $signButton.add(this.cp_content.$buttons);
            }
        },

        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                if(self.is_author && self.is_sent) {
                    self.$('.o_sign_signer_status').each(function(i, el) {
                        $(el).append($('<button/>', {
                            type: 'button',
                            title: _t("Resend the invitation"),
                            text: _t('Resend'),
                            class: 'o_sign_resend_access_button btn btn-link ml8',
                            style: 'vertical-align: baseline;',
                        }));
                    });
                }
            });
        },
    });

    core.action_registry.add('sign.Document', EditableDocumentBackend);
});

odoo.define('sign.document_signing_backend', function(require) {
    'use strict';

    var core = require('web.core');
    var DocumentBackend = require('sign.DocumentBackend');
    var document_signing = require('sign.document_signing');

    var _t = core._t;

    var NoPubThankYouDialog = document_signing.ThankYouDialog.extend({
        template: "sign.no_pub_thank_you_dialog",

        init: function (parent, RedirectURL, requestID, options) {
            options = (options || {});
            if (!options.buttons) {
                options.buttons = [{text: _t("Ok"), close: true}];
            }
            this._super(parent, RedirectURL, requestID, options);
        },

        on_closed: function () {
            var self = this;
            self._rpc({
                model: 'sign.request',
                method: 'go_to_document',
                args: [self.requestID],
            }).then(function(action) {
                self.do_action(action);
                self.destroy();
            });
        },
    });

    var SignableDocument2 = document_signing.SignableDocument.extend({
        get_thankyoudialog_class: function () {
            return NoPubThankYouDialog;
        },
    });

    var SignableDocumentBackend = DocumentBackend.extend({
        get_document_class: function () {
            return SignableDocument2;
        },
    });

    var SMSSignerDialogBackend = document_signing.SMSSignerDialog.include({
        get_thankyoudialog_class: function () {
            return NoPubThankYouDialog;
        },
    });

    core.action_registry.add('sign.SignableDocument', SignableDocumentBackend);
});
