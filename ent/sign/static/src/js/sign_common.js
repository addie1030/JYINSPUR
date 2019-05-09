odoo.define('sign.PDFIframe', function (require) {
    'use strict';

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');

    var _t = core._t;

    var PDFIframe = Widget.extend({
        init: function(parent, attachmentLocation, editMode, datas, role) {
            this._super(parent);

            this.attachmentLocation = attachmentLocation;
            this.editMode = editMode;
            for(var dataName in datas) {
                this._set_data(dataName, datas[dataName]);
            }

            this.role = role || 0;
            this.configuration = {};

            this.fullyLoaded = new $.Deferred();
        },

        _set_data: function(dataName, data) {
            this[dataName] = {};
            if(data instanceof jQuery) {
                var self = this;
                data.each(function(i, el) {
                    self[dataName][$(el).data('id')] = $(el).data();
                }).detach();
            } else {
                for(var i = 0 ; i < data.length ; i++) {
                    this[dataName][data[i].id] = data[i];
                }
            }
        },

        start: function() {
            this.$iframe = this.$el; // this.$el will be changed to the iframe html tag once loaded
            var self = this;
            this.pdfView = (this.$iframe.attr('readonly') === "readonly");
            this.readonlyFields = this.pdfView || this.editMode;

            var viewerURL = "/web/static/lib/pdfjs/web/viewer.html?file=";
            viewerURL += encodeURIComponent(this.attachmentLocation).replace(/'/g,"%27").replace(/"/g,"%22") + "#page=1&zoom=page-width";
            this.$iframe.load(function() {
                self.waitForPDF();
            });
            this.$iframe.attr('src', viewerURL);

            return $.when(this._super(), this.fullyLoaded);
        },

        waitForPDF: function() {
            if(this.$iframe.contents().find('#errorMessage').is(":visible")) {
                this.fullyLoaded.resolve();
                return Dialog.alert(this, _t("Need a valid PDF to add signature fields !"));
            }

            var nbPages = this.$iframe.contents().find('.page').length;
            var nbLayers = this.$iframe.contents().find('.textLayer').length;
            if(nbPages > 0 && nbLayers > 0) {
                this.nbPages = nbPages;
                this.doPDFPostLoad();
            } else {
                var self = this;
                setTimeout(function() { self.waitForPDF(); }, 50);
            }
        },

        doPDFPostLoad: function() {
            var self = this;
            this.setElement(this.$iframe.contents().find('html'));

            this.$('#openFile, #pageRotateCw, #pageRotateCcw, #pageRotateCcw, #viewBookmark').add(this.$('#lastPage').next()).hide();
            this.$('button#print').prop('title', _t("Print original document"));
            this.$('button#download').prop('title', _t("Download original document"));
            this.$('button#zoomOut').click().click();

            for(var i = 1 ; i <= this.nbPages ; i++) {
                this.configuration[i] = [];
            }

            var $cssLink = $("<link/>", {
                rel: "stylesheet", type: "text/css",
                href: "/sign/static/src/css/iframe.css"
            });
            var $faLink = $("<link/>", {
                rel: "stylesheet", type: "text/css",
                href: "/web/static/lib/fontawesome/css/font-awesome.css"
            });
            var $jqueryLink = $("<link/>", {
                rel: "stylesheet", type: "text/css",
                href: "/web/static/lib/jquery.ui/jquery-ui.css"
            });
            var $jqueryScript = $("<script></script>", {
                type: "text/javascript",
                src: "/web/static/lib/jquery.ui/jquery-ui.js"
            });
            var $select2Css = $("<link/>", {
                rel: "stylesheet", type: "text/css",
                href: "/web/static/lib/select2/select2.css"
            });
            // use Node.appendChild to add resources and not jQuery that load script in top frame
            this.$('head')[0].appendChild($cssLink[0]);
            this.$('head')[0].appendChild($faLink[0]);
            this.$('head')[0].appendChild($jqueryLink[0]);
            this.$('head')[0].appendChild($jqueryScript[0]);
            this.$('head')[0].appendChild($select2Css[0]);

            var waitFor = [];

            $(Object.keys(this.signatureItems).map(function(id) { return self.signatureItems[id]; }))
                .sort(function(a, b) {
                    if(a.page !== b.page) {
                        return (a.page - b.page);
                    }

                    if(Math.abs(a.posY - b.posY) > 0.01) {
                        return (a.posY - b.posY);
                    } else {
                        return (a.posX - b.posX);
                    }
                }).each(function(i, el) {
                    var $signatureItem = self.createSignItem(
                        self.types[parseInt(el.type || el.type_id[0])],
                        !!el.required,
                        parseInt(el.responsible || el.responsible_id[0]) || 0,
                        parseFloat(el.posX),
                        parseFloat(el.posY),
                        parseFloat(el.width),
                        parseFloat(el.height),
                        el.value,
                        el.name
                    );
                    $signatureItem.data({itemId: el.id, order: i});

                    self.configuration[parseInt(el.page)].push($signatureItem);
                });

            $.when.apply($, waitFor).then(function() {
                refresh_interval();

                self.$('.o_sign_sign_item').each(function(i, el) {
                    self.updateSignItem($(el));
                });
                self.updateFontSize();

                self.$('#viewerContainer').css('visibility', 'visible').animate({'opacity': 1}, 1000);
                self.fullyLoaded.resolve();

                /**
                 * This function is called every 2sec to check if the PDFJS viewer did not detach some signature items.
                 * Indeed, when scrolling, zooming, ... the PDFJS viewer replaces page content with loading icon, removing
                 * any custom content with it.
                 * Previous solutions were tried (refresh after scroll, on zoom click, ...) but this did not always work
                 * for some reason when the PDF was too big.
                 */
                function refresh_interval() {
                    try { // if an error occurs it means the iframe has been detach and will be reinitialized anyway (so the interval must stop)
                        self.refreshSignItems();
                        self.refresh_timer = setTimeout(refresh_interval, 2000);
                    } catch (e) {}
                }
            });
        },

        refreshSignItems: function() {
            for(var page in this.configuration) {
                var $pageContainer = this.$('body #pageContainer' + page);
                for(var i = 0 ; i < this.configuration[page].length ; i++) {
                    if(!this.configuration[page][i].parent().hasClass('page')) {
                        $pageContainer.append(this.configuration[page][i]);
                    }
                }
            }
            this.updateFontSize();
        },

        updateFontSize: function() {
            var self = this;
            var normalSize = this.$('.page').first().innerHeight() * 0.015;
            this.$('.o_sign_sign_item').each(function(i, el) {
                var $elem = $(el);
                var size = parseFloat($elem.css('height'));
                if($.inArray(self.types[$elem.data('type')].type, ['signature', 'initial', 'textarea']) > -1) {
                    size = normalSize;
                }

                $elem.css('font-size', size * 0.8);
            });
        },

        createSignItem: function(type, required, responsible, posX, posY, width, height, value, name) {
            var self = this;
            var readonly = this.readonlyFields || (responsible > 0 && responsible !== this.role) || !!value;

            var $signatureItem = $(core.qweb.render('sign.sign_item', {
                editMode: this.editMode,
                readonly: readonly,
                type: type['type'],
                value: value || "",
                placeholder: type['placeholder']
            }));

            return $signatureItem.data({type: type['id'], required: required, responsible: responsible, posx: posX, posy: posY, width: width, height: height, name:name})
                                 .data('hasValue', !!value);
        },

        deleteSignItem: function($item) {
            var pageNo = parseInt($item.parent().prop('id').substr('pageContainer'.length));
            $item.remove();
            for(var i = 0 ; i < this.configuration[pageNo].length ; i++) {
                if(this.configuration[pageNo][i].data('posx') === $item.data('posx') && this.configuration[pageNo][i].data('posy') === $item.data('posy')) {
                    this.configuration[pageNo].splice(i, 1);
                }
            }
        },

        updateSignItem: function($signatureItem) {
            var posX = $signatureItem.data('posx'), posY = $signatureItem.data('posy');
            var width = $signatureItem.data('width'), height = $signatureItem.data('height');

            if(posX < 0) {
                posX = 0;
            } else if(posX+width > 1.0) {
                posX = 1.0-width;
            }
            if(posY < 0) {
                posY = 0;
            } else if(posY+height > 1.0) {
                posY = 1.0-height;
            }

            $signatureItem.data({posx: Math.round(posX*1000)/1000, posy: Math.round(posY*1000)/1000})
                          .css({left: posX*100 + '%', top: posY*100 + '%', width: width*100 + '%', height: height*100 + '%'});

            var resp = $signatureItem.data('responsible');
            $signatureItem.toggleClass('o_sign_sign_item_required', ($signatureItem.data('required') && (this.editMode || resp <= 0 || resp === this.role)))
                          .toggleClass('o_sign_sign_item_pdfview', (this.pdfView || !!$signatureItem.data('hasValue') || (resp !== this.role && resp > 0 && !this.editMode)));
        },

        disableItems: function() {
            this.$('.o_sign_sign_item').addClass('o_sign_sign_item_pdfview').removeClass('ui-selected');
        },

        destroy: function() {
            clearTimeout(this.refresh_timer);
            this._super.apply(this, arguments);
        },
    });

    return PDFIframe;
});

odoo.define('sign.Document', function (require) {
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var PDFIframe = require('sign.PDFIframe');
    var Widget = require('web.Widget');

    var _t = core._t;

    var Document = Widget.extend({
        start: function() {
            this.attachmentLocation = this.$('#o_sign_input_attachment_location').val();
            this.requestID = parseInt(this.$('#o_sign_input_sign_request_id').val());
            this.requestToken = this.$('#o_sign_input_sign_request_token').val();
            this.accessToken = this.$('#o_sign_input_access_token').val();
            this.signerName = this.$('#o_sign_signer_name_input_info').val();
            this.signerPhone = this.$('#o_sign_signer_phone_input_info').val();
            this.RedirectURL = this.$('#o_sign_input_optional_redirect_url').val();
            this.types = this.$('.o_sign_field_type_input_info');
            this.items = this.$('.o_sign_item_input_info');

            this.$validateBanner = this.$('.o_sign_validate_banner').first();

            return $.when(this._super.apply(this, arguments), this.initialize_iframe());
        },

        get_pdfiframe_class: function () {
            return PDFIframe;
        },

        initialize_iframe: function() {
            this.$iframe = this.$('iframe.o_sign_pdf_iframe').first();
            if(this.$iframe.length > 0 && !this.iframeWidget) {
                this.iframeWidget = new (this.get_pdfiframe_class())(this,
                                                                     this.attachmentLocation,
                                                                     !this.requestID,
                                                                     {
                                                                         types: this.types,
                                                                         signatureItems: this.items,
                                                                     },
                                                                     parseInt(this.$('#o_sign_input_current_role').val()));
                return this.iframeWidget.attachTo(this.$iframe);
            }
            return $.when();
        },
    });

    return Document;
});

odoo.define('sign.utils', function (require) {
    'use strict';

    var ajax = require("web.ajax");
    var core = require('web.core');

    var _t = core._t;

    function getResponsibleSelectConfiguration(parties) {
        if(getResponsibleSelectConfiguration.configuration === undefined) {
            var select2Options = {
                placeholder: _t("Select the responsible"),
                allowClear: false,
                width: '100%',

                formatResult: function(data, resultElem, searchObj) {
                    if(!data.text) {
                        $(data.element[0]).data('create_name', searchObj.term);
                        return $("<div/>", {text: _t("Create: \"") + searchObj.term + "\""});
                    }
                    return $("<div/>", {text: data.text});
                },

                formatSelection: function(data) {
                    if(!data.text) {
                        return $("<div/>", {text: $(data.element[0]).data('create_name')}).html();
                    }
                    return $("<div/>", {text: data.text}).html();
                },

                matcher: function(search, data) {
                    if(!data) {
                        return (search.length > 0);
                    }
                    return (data.toUpperCase().indexOf(search.toUpperCase()) > -1);
                }
            };

            var selectChangeHandler = function(e) {
                var $select = $(e.target), $option = $(e.added.element[0]);

                var resp = parseInt($option.val());
                var name = $option.text() || $option.data('create_name');

                if(resp >= 0 || !name) {
                    return false;
                }

                ajax.rpc('/web/dataset/call_kw/sign.item.role/add', {
                    model: 'sign.item.role',
                    method: 'add',
                    args: [name],
                    kwargs: {}
                }).then(process_party);

                function process_party(partyID) {
                    parties[partyID] = {id: partyID, name: name};
                    getResponsibleSelectConfiguration.configuration = undefined;
                    setAsResponsibleSelect($select, partyID, parties);
                }
            };

            var $responsibleSelect = $('<select/>').append($('<option/>'));
            for(var id in parties) {
                $responsibleSelect.append($('<option/>', {
                    value: parseInt(id),
                    text: parties[id].name,
                }));
            }
            $responsibleSelect.append($('<option/>', {value: -1}));

            getResponsibleSelectConfiguration.configuration = {
                html: $responsibleSelect.html(),
                options: select2Options,
                handler: selectChangeHandler,
            };
        }

        return getResponsibleSelectConfiguration.configuration;
    }

    function resetResponsibleSelectConfiguration() {
        getResponsibleSelectConfiguration.configuration = undefined;
    }

    function setAsResponsibleSelect($select, selected, parties) {
        var configuration = getResponsibleSelectConfiguration(parties);

        $select.select2('destroy');
        $select.html(configuration.html).addClass('form-control');
        if(selected !== undefined) {
            $select.val(selected);
        }
        $select.select2(configuration.options);
        $select.off('change').on('change', configuration.handler);
    }

    return {
        setAsResponsibleSelect: setAsResponsibleSelect,
        resetResponsibleSelectConfiguration: resetResponsibleSelectConfiguration,
    };
});

// Signing part
odoo.define('sign.document_signing', function(require) {
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var Widget = require('web.Widget');
    var Document = require('sign.Document');
    var PDFIframe = require('sign.PDFIframe');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var Tour = require('web_tour.tour');

    var _t = core._t;

    var SignatureDialog = Dialog.extend({
        template: 'sign.signature_dialog',

        events: {
            'click a.o_sign_mode': function(e) {
                e.preventDefault();

                this.$modeButtons.removeClass('active');
                $(e.target).addClass('active');
                this.$signatureField.jSignature('reset');

                this.mode = $(e.target).data('mode');

                this.$selectStyleButton.toggle(this.mode === 'auto');
                this.$clearButton.toggle(this.mode === 'draw');
                this.$loadButton.toggle(this.mode === 'load');

                if(this.mode === 'load') {
                    this.$loadButton.click();
                }
                this.$signatureField.jSignature((this.mode === 'draw')? "enable" : "disable");

                this.$fontDialog.hide().css('width', 0);
                this.$signerNameInput.trigger('input');
            },

            'input .o_sign_signer_name': function(e) {
                if(this.mode !== 'auto') {
                    return true;
                }
                this.signerName = this.$signerNameInput.val();
                this.printText(SignatureDialog.fonts[this.currentFont], this.getSignatureText());
            },

            'click .o_sign_select_style': function(e) {
                var self = this;
                var width = Math.min(
                    self.$fontDialog.find('a').first().height() * self.signatureRatio * 1.25,
                    this.$signerNameInput.width()
                );

                e.preventDefault();
                this.$fontDialog.find('a').empty().append($('<div/>').addClass("o_sign_loading"));
                this.$fontDialog.show().animate({'width': width}, 500, function() {
                    self.buildPreviewButtons();
                });
            },

            'mouseover .o_sign_font_dialog a': function(e) {
                this.currentFont = $(e.currentTarget).data('font-nb');
                this.$signerNameInput.trigger('input');
            },

            'click .o_sign_font_dialog a, .o_sign_signature': function(e) {
                this.$fontDialog.hide().css('width', 0);
            },

            'click .o_sign_clean': function (e) {
                e.preventDefault();

                this.$signatureField.jSignature('reset');
            },

            'change .o_sign_load': function(e) {
                var f = e.target.files[0];
                if(f.type.substr(0, 5) !== "image") {
                    return false;
                }

                var self = this, reader = new FileReader();
                reader.onload = function(e) {
                    self.printImage(this.result);
                };
                reader.readAsDataURL(f);
            },
        },

        init: function(parent, signerName, options) {
            options = (options || {});

            options.title = options.title || _t("Adopt Your Signature");
            options.size = options.size || 'medium';
            options.technical = false;

            if(!options.buttons) {
                options.buttons = [];
                options.buttons.push({text: _t("Adopt and Sign"), classes: "btn-primary", click: function(e) {
                    this.confirmFunction(this.$signerNameInput.val(), this.$signatureField.jSignature("getData"));
                }});
                options.buttons.push({text: _t("Cancel"), close: true});
            }

            this._super(parent, options);
            this.options = options || {};

            this.signerName = signerName;

            this.signatureRatio = 3.0;
            this.signatureType = 'signature';
            this.currentFont = 0;
            this.mode = 'draw';

            this.confirmFunction = function() {};
        },

        start: function() {
            this.$modeButtons = this.$('a.o_sign_mode');
            this.$signatureField = this.$(".o_sign_signature").first();
            this.$fontDialog = this.$(".o_sign_font_dialog").first();
            this.$fontSelection = this.$(".o_sign_font_selection").first();
            for(var i = 0 ; i < SignatureDialog.fonts.length ; i++) {
                this.$fontSelection.append($("<a/>").data('fontNb', i).addClass('btn btn-block'));
            }
            this.$clearButton = this.$('.o_sign_clean').first();
            this.$selectStyleButton = this.$('.o_sign_select_style').first();
            this.$loadButton = this.$('.o_sign_load').first();
            this.$signerNameInput = this.$(".o_sign_signer_name").first();

            return this._super.apply(this, arguments);
        },

        open: function() {
            var self = this;
            this.opened(function(e) {
                var width = self.$signatureField.width();
                var height = width / self.signatureRatio;

                // necessary because the lib is adding invisible div with margin
                // signature field too tall without this code
                self.$signatureField.css({
                    width: width,
                    height: height,
                });
                self.$signatureField.empty().jSignature({
                    'decor-color': 'transparent',
                    'background-color': '#FFF',
                    'color': '#000',
                    'lineWidth': 2,
                    'width': width,
                    'height': height
                });

                // TDE FIXME: ugly FP-request RPC to dynamically fetch signature instead of
                // pre-filled sign.request.item
                if (self.options.signatureType !== undefined) {
                    rpc.query({
                        route: '/sign/get_signature/' + self.getParent().getParent().requestID + '/' + self.getParent().getParent().accessToken,
                        params: {
                            signature_type: self.options.signatureType,
                        }
                    }).then(function (signature) {
                        if (signature) {
                            signature = 'data:image/png;base64,' + signature;
                            self.$signatureField.jSignature("importData", signature);
                        }
                    });
                }
                self.emptySignature = self.$signatureField.jSignature("getData");

                self.$modeButtons.filter('.btn.active').click();
                self.$signerNameInput.focus();
            });

            return this._super.apply(this, arguments);
        },

        getSignatureText: function() {
            var text = this.$signerNameInput.val().replace(/[^[\w\u00E0-\u00FC]-'" ]/g, '');
            if(this.signatureType === 'initial') {
                return (text.split(' ').map(function(w) { return w[0]; }).join('.') + '.');
            }
            return text;
        },

        getSVGText: function(font, text) {
            var canvas = this.$signatureField.find('canvas')[0];

            var $svg = $(core.qweb.render('sign.svg_text', {
                width: canvas.width,
                height: canvas.height,
                font: font,
                text: text,
                type: this.signatureType,
            }));
            $svg.attr({
                "xmlns": "http://www.w3.org/2000/svg",
                "xmlns:xlink": "http://www.w3.org/1999/xlink",
            });

            return ("data:image/svg+xml," + encodeURI($svg[0].outerHTML));
        },

        printText: function(font, text) {
            return this.printImage(this.getSVGText(font, text));
        },

        printImage: function(imgSrc) {
            var self = this;

            var image = new Image;
            image.onload = function() {
                var width = 0, height = 0;
                var ratio = image.width/image.height;

                self.$signatureField.jSignature('reset');
                var $canvas = self.$signatureField.find('canvas'), context = $canvas[0].getContext("2d");

                if(image.width / $canvas[0].width > image.height / $canvas[0].height) {
                    width = $canvas[0].width;
                    height = width / ratio;
                } else {
                    height = $canvas[0].height;
                    width = height * ratio;
                }

                setTimeout(function() {
                    var ignoredContext = _.pick(context, ['shadowOffsetX', 'shadowOffsetY']);
                    _.extend(context, {shadowOffsetX: 0, shadowOffsetY: 0});
                    context.drawImage(image, 0, 0, image.width, image.height, ($canvas[0].width - width)/2, ($canvas[0].height - height)/2, width, height);
                    _.extend(context, ignoredContext);
                }, 0);
            };
            image.src = imgSrc;
        },

        buildPreviewButtons: function() {
            var self = this;
            this.$fontDialog.find('a').each(function(i, el) {
                var $img = $('<img/>', {src: self.getSVGText(SignatureDialog.fonts[$(el).data('fontNb')], self.getSignatureText())});
                $img.addClass('img-fluid');
                $(el).empty().append($img);
            });
        },

        onConfirm: function(fct) {
            this.confirmFunction = fct;
        },
    });

    var SignItemNavigator = Widget.extend({
        className: 'o_sign_sign_item_navigator',

        events: {
            'click': 'onClick'
        },

        init: function(parent, types) {
            this._super(parent);

            this.types = types;
            this.started = false;
            this.isScrolling = false;
        },

        start: function() {
            this.$signatureItemNavLine = $('<div/>').addClass("o_sign_sign_item_navline").insertBefore(this.$el);
            this.setTip(_t('Click to start'));
            this.$el.focus();

            return this._super();
        },

        setTip: function(tip) {
            this.$el.text(tip);
        },

        onClick: function(e) {
            var self = this;

            if(!self.started) {
                self.started = true;

                self.getParent().$iframe.prev().animate({'height': '0px', 'opacity': 0}, {
                    duration: 750,
                    complete: function() {
                        self.getParent().$iframe.prev().hide();
                        self.getParent().refreshSignItems();

                        self.onClick();
                    }
                });

                return false;
            }

            var $toComplete = self.getParent().checkSignItemsCompletion().sort(function(a, b) {
                return ($(a).data('order') || 0) - ($(b).data('order') || 0);
            });
            if($toComplete.length > 0) {
                self.scrollToSignItem($toComplete.first());
            }
        },

        scrollToSignItem: function($item) {
            if(!this.started) {
                return;
            }

            var $container = this.getParent().$('#viewerContainer');
            var $viewer = $container.find('#viewer');
            var containerHeight = $container.outerHeight();
            var viewerHeight = $viewer.outerHeight();

            var scrollOffset = containerHeight/4;
            var scrollTop = $item.offset().top - $viewer.offset().top - scrollOffset;
            if(scrollTop + containerHeight > viewerHeight) {
                scrollOffset += scrollTop + containerHeight - viewerHeight;
            }
            if(scrollTop < 0) {
                scrollOffset += scrollTop;
            }
            scrollOffset += $container.offset().top - this.$el.outerHeight()/2 + parseInt($item.css('height'))/2;

            var duration = Math.min(
                1000,
                5*(Math.abs($container[0].scrollTop - scrollTop) + Math.abs(parseFloat(this.$el.css('top')) - scrollOffset))
            );

            var self = this;
            this.isScrolling = true;
            var def1 = $.Deferred(), def2 = $.Deferred();
            $container.animate({'scrollTop': scrollTop}, duration, function() {
                def1.resolve();
            });
            this.$el.add(this.$signatureItemNavLine).animate({'top': scrollOffset}, duration, function() {
                def2.resolve();
            });
            $.when(def1, def2).then(function() {
                if($item.val() === "" && !$item.data('signature')) {
                    self.setTip(self.types[$item.data('type')].tip);
                }

                self.getParent().refreshSignItems();
                $item.focus();
                self.isScrolling = false;
            });

            this.getParent().$('.ui-selected').removeClass('ui-selected');
            $item.addClass('ui-selected').focus();
        },
    });

    var PublicSignerDialog = Dialog.extend({
        template: "sign.public_signer_dialog",

        init: function(parent, requestID, requestToken, RedirectURL, options) {
            var self = this;
            options = (options || {});

            options.title = options.title || _t("Final Validation");
            options.size = options.size || "medium";
            options.technical = false;

            if(!options.buttons) {
                options.buttons = [];
                options.buttons.push({text: _t("Validate & Send"), classes: "btn-primary", click: function(e) {
                    var name = this.$inputs.eq(0).val();
                    var mail = this.$inputs.eq(1).val();
                    if(!name || !mail || mail.indexOf('@') < 0) {
                        this.$inputs.eq(0).closest('.form-group').toggleClass('o_has_error', !name).find('.form-control, .custom-select').toggleClass('is-invalid', !name);
                        this.$inputs.eq(1).closest('.form-group').toggleClass('o_has_error', !mail || mail.indexOf('@') < 0).find('.form-control, .custom-select').toggleClass('is-invalid', !mail || mail.indexOf('@') < 0);
                        return false;
                    }

                    ajax.jsonRpc("/sign/send_public/" + this.requestID + '/' + this.requestToken, 'call', {
                        name: name,
                        mail: mail,
                    }).then(function() {
                        self.close();
                        self.sent.resolve();
                    });
                }});
                options.buttons.push({text: _t("Cancel"), close: true});
            }

            this._super(parent, options);

            this.requestID = requestID;
            this.requestToken = requestToken;
            this.sent = $.Deferred();
        },

        open: function(name, mail) {
            var self = this;
            this.opened(function() {
                self.$inputs = self.$('input');
                self.$inputs.eq(0).val(name);
                self.$inputs.eq(1).val(mail);
            });
            return this._super.apply(this, arguments);
        },
    });

    var SMSSignerDialog = Dialog.extend({
        template: "sign.public_sms_signer",

        events: {
            'click button.o_sign_resend_sms': function(e) {
                var route = '/sign/send-sms/' + this.requestID + '/' + this.requestToken + '/' + this.$('#o_sign_phone_number_input').val();
                session.rpc(route, {}).then(function(success) {
                    if (!success) {
                        Dialog.alert(self, _t("Unable to send the SMS, please contact the sender of the document."), {
                            title: _t("Error"),
                            confirm_callback: function() {
                                window.location.reload();
                            },
                        });
                    }
                    else {
                        self.$('.o_sign_resend_sms').html('Send Again');
                    }
                });
            }
        },

        _onValidateSMS: function () {
            var input = this.$('#o_sign_public_signer_sms_input')
            if(!input.val()) {
                input.closest('.form-group').toggleClass('o_has_error').find('.form-control, .custom-select').toggleClass('is-invalid');
                return false;
            }
            var route = '/sign/sign/' + this.requestID + '/' + this.requestToken + '/' + input.val();
            var params = {
                signature: this.signature
            };
            var self = this;
            session.rpc(route, params).then(function(response) {
                if (!response) {
                    Dialog.alert(self, _t("Sorry, an error occured, please try to fill the document again."), {
                        title: _t("Error"),
                    });
                }
                if (response === true) {
                    (new (self.get_thankyoudialog_class())(self, self.RedirectURL, self.requestID)).open();
                    self.do_hide();
                }
                if (typeof response === 'object') {
                    if (response.url) {
                        document.location.pathname = success['url'];
                    }
                }
            });
        },

        get_thankyoudialog_class: function () {
            return ThankYouDialog;
        },

        init: function(parent, requestID, requestToken, signature, signerPhone, RedirectURL, options) {
            options = (options || {});
            options.title = options.title || _t("Final Validation");
            options.size = options.size || "medium";
            if(!options.buttons) {
                options.buttons = [{
                    text: _t("Verify"),
                    classes: "btn btn-primary o_sign_validate_sms",
                    click: this._onValidateSMS
                }]
            }
            this._super(parent, options);
            this.requestID = requestID;
            this.requestToken = requestToken;
            this.signature = signature;
            this.signerPhone = signerPhone;
            this.RedirectURL = RedirectURL;
            this.sent = $.Deferred();
        },
    });

    var ThankYouDialog = Dialog.extend({
        template: "sign.thank_you_dialog",
        events: {
            'click .o_go_to_document': 'on_closed',
        },

        init: function(parent, RedirectURL, requestID, options) {
            options = (options || {});
            options.title = options.title || _t("Thank You !");
            options.subtitle = options.subtitle || _t("Your signature has been saved.");
            options.size = options.size || "medium";
            options.technical = false;
            options.buttons = [];
            this.RedirectURL = RedirectURL;
            this.requestID = requestID;
            this._super(parent, options);

            this.on('closed', this, this.on_closed);
        },

        /**
         * @override
         */
        renderElement: function () {
            this._super.apply(this, arguments);
            this.$modal.addClass('o_sign_thank_you_dialog');
            this.$modal.find('.modal-header .o_subtitle').before('<br/>');
        },

        on_closed: function () {
            window.location.reload();
        },
    });

    var SignablePDFIframe = PDFIframe.extend({
        init: function() {
            this._super.apply(this, arguments);

            this.events = _.extend(this.events || {}, {
                'keydown .page .ui-selected': function(e) {
                    if((e.keyCode || e.which) !== 9) {
                        return true;
                    }
                    e.preventDefault();
                    this.signatureItemNav.onClick();
                },
            });
        },

        doPDFPostLoad: function() {
            var self = this;
            this.fullyLoaded.then(function() {
                self.signatureItemNav = new SignItemNavigator(self, self.types);
                var def = self.signatureItemNav.prependTo(self.$('#viewerContainer'));

                self.checkSignItemsCompletion();

                self.$('#viewerContainer').on('scroll', function(e) {
                    if(!self.signatureItemNav.isScrolling && self.signatureItemNav.started) {
                        self.signatureItemNav.setTip(_t('next'));
                    }
                });

                return def;
            });

            this._super.apply(this, arguments);
        },

        createSignItem: function(type, required, responsible, posX, posY, width, height, value, name) {
            var self = this;
            var $signatureItem = this._super.apply(this, arguments);
            var readonly = this.readonlyFields || (responsible > 0 && responsible !== this.role) || !!value;

            if(!readonly) {
                if(type['type'] === "signature" || type['type'] === "initial") {
                    $signatureItem.on('click', function(e) {
                        self.refreshSignItems();
                        var $signedItems = self.$('.o_sign_sign_item').filter(function(i) {
                            var $item = $(this);
                            return ($item.data('type') === type['id']
                                        && $item.data('signature') && $item.data('signature') !== $signatureItem.data('signature')
                                        && ($item.data('responsible') <= 0 || $item.data('responsible') === $signatureItem.data('responsible')));
                        });

                        if($signedItems.length > 0) {
                            $signatureItem.data('signature', $signedItems.first().data('signature'));
                            $signatureItem.html('<span class="o_sign_helper"/><img src="' + $signatureItem.data('signature') + '"/>');
                            $signatureItem.trigger('input');
                        } else {
                            var signDialog = new SignatureDialog(self, self.getParent().signerName || "", {
                                signatureType: type['type'],
                            });
                            signDialog.signatureType = type['type'];
                            signDialog.signatureRatio = parseFloat($signatureItem.css('width'))/parseFloat($signatureItem.css('height'));

                            signDialog.open().onConfirm(function(name, signature) {
                                if(signature !== signDialog.emptySignature) {
                                    self.getParent().signerName = signDialog.signerName;
                                    $signatureItem.data('signature', signature)
                                                  .empty()
                                                  .append($('<span/>').addClass("o_sign_helper"), $('<img/>', {src: $signatureItem.data('signature')}));
                                } else {
                                    $signatureItem.removeData('signature')
                                                  .empty()
                                                  .append($('<span/>').addClass("o_sign_helper"), type['placeholder']);
                                }

                                $signatureItem.trigger('input').focus();
                                signDialog.close();
                            });
                        }
                    });
                }

                if(type['auto_field']) {
                    $signatureItem.on('focus', function(e) {
                        if($signatureItem.val() === "") {
                            $signatureItem.val(type['auto_field']);
                            $signatureItem.trigger('input');
                        }
                    });
                }

                $signatureItem.on('input', function(e) {
                    self.checkSignItemsCompletion(self.role);
                    self.signatureItemNav.setTip(_t('next'));
                });
            } else {
                $signatureItem.val(value);
            }

            return $signatureItem;
        },

        checkSignItemsCompletion: function() {
            this.refreshSignItems();
            var $toComplete = this.$('.o_sign_sign_item.o_sign_sign_item_required:not(.o_sign_sign_item_pdfview)').filter(function(i, el) {
                var $elem = $(el);
                return !(($elem.val() && $elem.val().trim()) || $elem.data('signature'));
            });

            this.signatureItemNav.$el.add(this.signatureItemNav.$signatureItemNavLine).toggle($toComplete.length > 0);
            this.$iframe.trigger(($toComplete.length > 0)? 'pdfToComplete' : 'pdfCompleted');

            return $toComplete;
        },
    });

    var SignableDocument = Document.extend({
        events: {
            'pdfToComplete .o_sign_pdf_iframe': function(e) {
                this.$validateBanner.hide().css('opacity', 0);
            },

            'pdfCompleted .o_sign_pdf_iframe': function(e) {
                this.$validateBanner.show().animate({'opacity': 1}, 500);
            },

            'click .o_sign_validate_banner button': 'signItemDocument',
            'click .o_sign_sign_document_button': 'signDocument',
        },

        custom_events: { // do_notify is not supported in backend so it is simulated with a bootstrap alert inserted in a frontend-only DOM element
            'notification': function(e) {
                $('<div/>', {html: e.data.message}).addClass('alert alert-success').insertAfter(self.$('.o_sign_request_reference_title'));
            },
        },

        start: function() {
            return $.when(this._super.apply(this, arguments), ajax.jsonRpc('/sign/get_fonts', 'call', {}).then(function(data) {
                SignatureDialog.fonts = data;
            }));
        },

        get_pdfiframe_class: function () {
            return SignablePDFIframe;
        },

        get_thankyoudialog_class: function () {
            return ThankYouDialog;
        },

        signItemDocument: function(e) {
            var mail = "";
            this.iframeWidget.$('.o_sign_sign_item').each(function(i, el) {
                var value = $(el).val();
                if(value && value.indexOf('@') >= 0) {
                    mail = value;
                }
            });

            if(this.$('#o_sign_is_public_user').length > 0) {
                (new PublicSignerDialog(this, this.requestID, this.requestToken, this.RedirectURL))
                    .open(this.signerName, mail).sent.then(_.bind(_sign, this));
            } else {
                _sign.call(this);
            }

            function _sign() {
                var signatureValues = {};
                for(var page in this.iframeWidget.configuration) {
                    for(var i = 0 ; i < this.iframeWidget.configuration[page].length ; i++) {
                        var $elem = this.iframeWidget.configuration[page][i];
                        var resp = parseInt($elem.data('responsible')) || 0;
                        if(resp > 0 && resp !== this.iframeWidget.role) {
                            continue;
                        }
                        var value = ($elem.val() && $elem.val().trim())? $elem.val() : false;
                        if($elem.data('signature')) {
                            value = $elem.data('signature');
                        }
                        if($elem[0].type === 'checkbox') {
                            if ($elem[0].checked) {
                                value = 'on';
                            } else {
                                value = 'off';
                            }
                        }
                        if(!value) {
                            if($elem.data('required')) {
                                this.iframeWidget.checkSignItemsCompletion();
                                Dialog.alert(this, _t("Some fields have still to be completed !"), {title: _t("Warning")});
                                return;
                            }
                            continue;
                        }

                        signatureValues[parseInt($elem.data('item-id'))] = value;
                    }
                }
                var route = '/sign/sign/' + this.requestID + '/' + this.accessToken;
                var params = {
                    signature: signatureValues
                };
                var self = this;
                session.rpc(route, params).then(function(response) {
                    if (!response) {
                        Dialog.alert(self, _t("Sorry, an error occured, please try to fill the document again."), {
                            title: _t("Error"),
                            confirm_callback: function() {
                                window.location.reload();
                            },
                        });
                    }
                    if (response === true) {
                        self.iframeWidget.disableItems();
                        (new (self.get_thankyoudialog_class())(self, self.RedirectURL, self.requestID)).open();
                    }
                    if (typeof response === 'object') {
                        if (response.sms) {
                            (new SMSSignerDialog(self, self.requestID, self.accessToken, signatureValues, self.signerPhone, self.RedirectURL))
                                .open();
                        }
                        if (response.credit_error) {
                            Dialog.alert(self, _t("Unable to send the SMS, please contact the sender of the document."), {
                                title: _t("Error"),
                                confirm_callback: function() {
                                    window.location.reload();
                                },
                            });
                        }
                        if (response.url) {
                            document.location.pathname = response['url'];
                        }
                    }
                });
            }
        },

        signDocument: function(e) {
            var self = this;

            var signDialog = (new SignatureDialog(this, this.signerName));
            signDialog.open().onConfirm(function(name, signature) {
                var isEmpty = ((signature)? (signDialog.emptySignature === signature) : true);

                signDialog.$('.o_sign_signer_info').toggleClass('o_has_error', !name).find('.form-control, .custom-select').toggleClass('is-invalid', !name);
                signDialog.$('.o_sign_signature_draw').toggleClass('bg-danger text-white', isEmpty);
                if(isEmpty || !name) {
                    return false;
                }

                signDialog.$('.modal-footer .btn-primary').prop('disabled', true);
                signDialog.close();

                if(self.$('#o_sign_is_public_user').length > 0) {
                    (new PublicSignerDialog(self, self.requestID, self.requestToken, this.RedirectURL))
                        .open(name, "").sent.then(_sign);
                } else {
                    _sign();
                }

                function _sign() {
                    ajax.jsonRpc('/sign/sign/' + self.requestID + '/' + self.accessToken, 'call', {
                        signature: ((signature)? signature.substr(signature.indexOf(",")+1) : false)
                    }).then(function(success) {
                        if(!success) {
                            setTimeout(function() { // To be sure this dialog opens after the thank you dialog below
                                Dialog.alert(self, _t("Sorry, an error occured, please try to fill the document again."), {
                                    title: _t("Error"),
                                    confirm_callback: function() {
                                        window.location.reload();
                                    },
                                });
                            }, 500);
                        }
                    });
                    (new (self.get_thankyoudialog_class())(self, self.RedirectURL, self.requestID)).open();
                }
            });
        },
    });

    function initDocumentToSign() {
        return session.session_bind(session.origin).then(function () {
            // Manually add 'sign' to module list and load the
            // translations.
            session.module_list.push('sign');
            return session.load_translations().then(function () {
                var documentPage = new SignableDocument(null);
                return documentPage.attachTo($('body')).then(function() {
                    // Geolocation
                    var askLocation = ($('#o_sign_ask_location_input').length > 0);
                    if(askLocation && navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(function(position) {
                            var coords = _.pick(position.coords, ['latitude', 'longitude']);
                            ajax.jsonRpc('/sign/save_location/' + documentPage.requestID + '/' + documentPage.accessToken, 'call', coords);
                        });
                    }
                });
            });
        });
    }

    return {
        ThankYouDialog: ThankYouDialog,
        initDocumentToSign: initDocumentToSign,
        SignableDocument: SignableDocument,
        SMSSignerDialog: SMSSignerDialog
    };
});
