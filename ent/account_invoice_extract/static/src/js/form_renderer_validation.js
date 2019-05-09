odoo.define('account_extract_invoice.form_renderer_validation', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');

var ThreadField = require('mail.ThreadField');
var FormView = require('web.FormView');
var BasicModel = require('web.BasicModel');
var FormController = require('web.FormController');
require('mail_enterprise.ThreadField');
var view_registry = require('web.view_registry');
var field_utils = require('web.field_utils');

ThreadField.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
    * Override the thread rendering to warn the FormRenderer about attachments.
    * This is used by the FormRenderer to display an attachment preview.
    *
    * @override
    * @private
    */
    _fetchAndRenderThread: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            if (self._threadWidget.attachments.length) {
                self.trigger_up('preview_attachment_validation', {
                    attachments: self._threadWidget.attachments,
                });
            }
        });
    },
});

var AccountInvoiceExtractFormRenderer = FormRenderer.extend({
    custom_events: _.extend({}, FormRenderer.prototype.custom_events, {
        preview_attachment_validation: '_onAttachmentPreviewValidation',
        display_boxes: '_display_boxes',
        save_choices: '_save_choices',
    }),

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Add click event on a boxLayer
     *
     * @private
     */
    _add_click_on_box_layer: function ($boxLayer) {
        var self = this;
        $boxLayer.click(function (event) {
            var $user_selected = $(this).find(".userChosenBox");
            if ($user_selected.length != 0) {
                var id = $user_selected[0].getAttribute("data_id");
                if (self.mode == "edit") {
                    self._rpc({
                        model: 'account.invoice',
                        method: 'remove_user_selected_box',
                        args: [[self.state.res_id], id],
                    }).then(function (result) {
                        var user_selected_found = false;
                        for (var index in self.boxes) {
                            if (self.boxes[index]["feature"] == self.selected_feature) {
                                if (self.boxes[index]["user_selected"] == true) {
                                    self.boxes[index]["user_selected"] = false;
                                    user_selected_found = true;
                                }
                            }
                        }
                        if (user_selected_found) {
                            for (var index in self.boxes) {
                                if (self.boxes[index]["feature"] == self.selected_feature) {
                                    if (self.boxes[index]["selected_status"] != 0) {
                                        self.boxes[index]["selected_status"] = 1;
                                    }
                                }
                            }
                        } else {
                            for (var index in self.boxes) {
                                if (self.boxes[index]["feature"] == self.selected_feature) {
                                    if (self.boxes[index]["feature"] == self.selected_feature) {
                                        self.boxes[index]["selected_status"] = 0;
                                    }
                                }
                            }
                        }
                        self.trigger_up('display_boxes', {feature: self.selected_feature});
                        var changes = {}
                        var feature = $user_selected[0].getAttribute("data_feature");
                        if (feature == "date") {
                            changes = {
                                date:field_utils.parse.date(result.split(" ")[0])
                            }
                        }
                        else if (feature == "supplier") {
                            changes = {
                                partner_id:{
                                    id:result
                                }
                            }
                        }
                        else if (feature == "VAT") {
                            changes = {
                                partner_id:{
                                    id:result
                                }
                            }
                        }
                        else if (feature == "due_date") {
                            changes = {
                                date_due:field_utils.parse.date(result.split(" ")[0])
                            }
                        }
                        else if (feature == "total") {
                            if (result["line_id"] != -1) {
                                changes = {
                                    invoice_line_ids:{
                                        id: self.state.data.invoice_line_ids.data[0].id,
                                        operation: "UPDATE",
                                        data: {
                                            price_unit: parseFloat(result["total"]),
                                        },
                                    }
                                }
                            } else {
                                //no invoice line, automatic change disabled
                                return;
                            }
                        }
                        else if (feature == "invoice_id") {
                            changes = {
                                reference:result
                            }
                        }
                        else if (feature == "currency") {
                            changes = {
                                currency_id:result
                            }
                        }
                        self.trigger_up('field_changed', {
                            dataPointID: self.state.id,
                            changes: changes,
                        });
                    });  
                }
            }
        });
    },

    /**
     * Add feature buttons on top of page
     *
     * @private
     */
    _add_feature_buttons: function (page) {
        var $buttonsDiv = this.$attachmentPreview.find('.o_features_buttons');
        if ($buttonsDiv.length > 0) {
            return;
        }
        $(page).before($('<div class="o_features_buttons"/>'));
        $buttonsDiv = this.$attachmentPreview.find('.o_features_buttons');
        var self = this;
        this._rpc({
            model: 'account.invoice',
            method: 'get_boxes',
            args: [this.state.res_id],
        }).then(function (result) {
            self.boxes = result;
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'VAT',
                click: function () { 
                    self.selected_feature = 'VAT_Number'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            }));
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'Vendor',
                click: function () { 
                    self.selected_feature = 'supplier'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            }));
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'Currency',
                click: function () { 
                    self.selected_feature = 'currency'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                },
            }));
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'Total',
                click: function () { 
                    self.selected_feature = 'total'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                },
            }));
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'Date',
                click: function () { 
                    self.selected_feature = 'date'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            }));
            $buttonsDiv.append($('<button/>',
            {
                type:'button',
                class: 'btn ml4',
                text: 'Due Date',
                click: function () { 
                    self.selected_feature = 'due_date'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            }));
            $buttonsDiv.append($('<button/>', {
                type:'button',
                class: 'btn ml4',
                text: 'Vendor Reference',
                click: function () { 
                    self.selected_feature = 'invoice_id'
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            }));
            if ($(page).hasClass("img-fluid")) { //in case of png
                $(page).after('<div class="boxLayer"/>');
                var boxLayer = self.$attachmentPreview[0].getElementsByClassName('boxLayer');
                self._add_click_on_box_layer($(boxLayer));
                $(boxLayer)[0].style.width = $(page)[0].clientWidth + "px";
                $(boxLayer)[0].style.height = $(page)[0].clientHeight + "px";
                $(boxLayer)[0].style.left = $(page)[0].offsetLeft + "px";
                $(boxLayer)[0].style.top = $(page)[0].offsetTop + "px";
            }
            if ($(page).is("iframe")) { //in case of pdf
                $(page)[0].style.height = "calc(100% - " + $buttonsDiv.height() + "px)";
            }
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Triggered from the mail chatter, send attachments data for preview
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onAttachmentPreviewValidation: function (ev) {
        var self = this;
        if (this.$attachmentPreview === undefined) {
            return; 
        }

        this.$attachmentPreview.find('iframe').load(function () { // wait for iframe to load
            var $frameDoc = self.$attachmentPreview.find('iframe').contents()[0];
            $frameDoc.addEventListener("pagerendered", function (evt) {
                var $iframe = self.$attachmentPreview.find('iframe')[0];
                var ocr_success = $(".o_success_ocr");
                if ($iframe != undefined && ocr_success.length > 0 && !ocr_success.hasClass("o_invisible_modifier") && self.mode == "edit") {
                    var document = $iframe.contentDocument;

                    self._add_feature_buttons($iframe);

                    if ($("account_invoice_extract_css").length == 0)
                        $(document.head).append('<link id="account_invoice_extract_css" rel="stylesheet" type="text/css" href="/account_invoice_extract/static/src/css/account_invoice_extract.css">');
                    var textLayer = document.getElementsByClassName('textLayer');
                    $(document.getElementsByClassName('boxLayer')).remove();
                    $(textLayer).after('<div class="boxLayer"/>');
                    var boxLayer = document.getElementsByClassName('boxLayer');
                    self._add_click_on_box_layer($(boxLayer));
                    $(boxLayer).each(function (index) {
                        $(this)[0].style.width = $(textLayer)[index].style.width;
                        $(this)[0].style.height = $(textLayer)[index].style.height;
                    })
                }
                if (!self.selected_feature) {
                    self.trigger_up('display_boxes', {feature: self.selected_feature}); 
                }
            });
        });
        var $document_img = self.$attachmentPreview.find('.img-fluid')[0];
        var attachment = document.getElementById('attachment_img');
        if (attachment != null && attachment.complete) {
            var ocr_success = $(".o_success_ocr");
            if ($document_img != undefined && ocr_success.length > 0 && !ocr_success.hasClass("o_invisible_modifier") && self.mode == "edit") {
                self._add_feature_buttons($document_img);
                if ($("account_invoice_extract_css").length == 0)
                    $(document.head).append('<link id="account_invoice_extract_css" rel="stylesheet" type="text/css" href="/account_invoice_extract/static/src/css/account_invoice_extract.css">');
            }
        } else {
            self.$attachmentPreview.find('.img-fluid').load(function () {
                var ocr_success = $(".o_success_ocr");
                if ($document_img != undefined && ocr_success.length > 0 && !ocr_success.hasClass("o_invisible_modifier") && self.mode == "edit") {
                    self._add_feature_buttons($document_img);
                    if ($("account_invoice_extract_css").length == 0)
                        $(document.head).append('<link id="account_invoice_extract_css" rel="stylesheet" type="text/css" href="/account_invoice_extract/static/src/css/account_invoice_extract.css">');
                }
            })
        }
        
    },

    /**
     * @private
     * @param {OdooEvent} ev
     */
    _display_boxes: function (ev) {
        var self = this;
        var $iframe = this.$attachmentPreview.find('iframe')[0];
        var document = undefined;
        if ($iframe == undefined) {
            if (self.$attachmentPreview.find('.img-fluid').length > 0) {
                document = self.$attachmentPreview.find('.o_attachment_preview_img')[0];
            }
        } else {
            document = $iframe.contentDocument;
        }
        if (document === undefined) {
            return;
        }
        var boxLayer = document.getElementsByClassName('boxLayer');
        if (boxLayer.length > 0) {
            $(boxLayer).each(function(index) {
                while ($(this)[0].firstChild) {
                    $(this)[0].removeChild($(this)[0].firstChild);
                }
            })
            for (var index in this.boxes) {
                var box = this.boxes[index];
                if (box["feature"] == ev.data.feature) {
                    var classDiv = "simpleBox";
                    if (box["selected_status"] == 2) {
                        classDiv += " ocrChosenBox";
                    }
                    if (box["user_selected"] == true || box["selected_status"] == 1) {
                        classDiv = "simpleBox userChosenBox";
                    }
                    if ($(boxLayer).length > box["page"]) {
                        $($(boxLayer)[box["page"]]).append("<div class='" + classDiv + 
                            "' style='left:" + (box["box_midX"] * parseInt($(boxLayer)[box["page"]].style.width)) + "px;" + 
                            "top:" + (box["box_midY"] * parseInt($(boxLayer)[box["page"]].style.height))  + "px;" + 
                            "width:" + ((box["box_width"]) * parseInt($(boxLayer)[box["page"]].style.width)) + "px;" + 
                            "height:" + ((box["box_height"]) * parseInt($(boxLayer)[box["page"]].style.height))  + "px;" + 
                            "transform: translate(-50%, -50%) rotate(" + box["box_angle"] + "deg);" + 
                            "-ms-transform: translate(-50%, -50%) rotate(" + box["box_angle"] + "deg);" + 
                            "-webkit-transform: translate(-50%, -50%) rotate(" + box["box_angle"] + "deg);" + "' data_id='" + box["id"] + "' data_feature='" + box['feature'] +"' data_text='" + box['text'] +"'/>");
                    }
                }
            }
            $(boxLayer).find(".simpleBox").click(function (event) {
                event.stopPropagation();
                var id = $(event.target)[0].getAttribute("data_id");
                if (self.mode == "edit") {
                    self._rpc({
                        model: 'account.invoice',
                        method: 'set_user_selected_box',
                        args: [[self.state.res_id], id],
                    }).then(function (result) {
                        for (var index in self.boxes) {
                            if (self.boxes[index]["id"] == id) {
                                self.boxes[index]["user_selected"] = true;
                            } else {
                                if (self.boxes[index]["feature"] == self.selected_feature) {
                                    self.boxes[index]["user_selected"] = false;
                                    if (self.boxes[index]["selected_status"] != 0) {
                                        self.boxes[index]["selected_status"] = 2;
                                    }
                                }
                            }
                        }
                        self.trigger_up('display_boxes', {feature: self.selected_feature});
                        var changes = {}
                        var feature = $(event.target)[0].getAttribute("data_feature");
                        if (feature == "date") {
                            changes = {
                                date_invoice:field_utils.parse.date(result.split(" ")[0])
                            }
                        }
                        else if (feature == "supplier") {
                            if (result == 0) {
                                return;
                            }
                            changes = {
                                partner_id:{
                                    id:result
                                }
                            }
                        }
                        else if (feature == "VAT_Number") {
                            changes = {
                                partner_id:{
                                    id:result
                                }
                            }
                        }
                        else if (feature == "due_date") {
                            changes = {
                                date_due:field_utils.parse.date(result.split(" ")[0])
                            }
                        }
                        else if (feature == "total") {
                            if (result["line_id"] != -1) {
                                changes = {
                                    invoice_line_ids:{
                                        id: self.state.data.invoice_line_ids.data[0].id,
                                        operation: "UPDATE",
                                        data: {
                                            price_unit: parseFloat(result["total"]),
                                        },
                                    }
                                }
                            } else {
                                //no invoice line, automatic change disabled
                                return;
                            }
                        }
                        else if (feature == "invoice_id") {
                            changes = {
                                reference:result
                            }
                        }
                        else if (feature == "currency") {
                            changes = {
                                currency_id: {
                                    id: result,
                                }
                            }
                        }
                        self.trigger_up('field_changed', {
                            dataPointID: self.state.id,
                            changes: changes,
                        });
                    });  
                } else {
                    //self.trigger_up('reload');
                }
            });
        }
    },
});

var AccountInvoiceExtractPreview = FormView.extend({
    config: _.extend({}, FormRenderer.prototype.config, {
        Model: BasicModel,
        Renderer: AccountInvoiceExtractFormRenderer,
        Controller: FormController,
    }),
})

view_registry.add('account_invoice_extract_preview', AccountInvoiceExtractPreview);

return {
    Renderer: AccountInvoiceExtractFormRenderer,
}

});
    
