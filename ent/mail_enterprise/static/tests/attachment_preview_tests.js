odoo.define('mail_enterprise.attachment_side_preview_tests', function (require) {
"use strict";

var MailService = require('mail.Service');
var mailTestUtils = require('mail.testUtils');

var config = require('web.config');
var FormView = require('web.FormView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('MailAttachmentOnSide', {

    beforeEach: function () {
        this.data = {
            partner: {
                fields: {
                    message_attachment_count: {string: 'Attachment count', type: 'integer'},
                    display_name: { string: "Displayed name", type: "char" },
                    foo: {string: "Foo", type: "char", default: "My little Foo Value"},
                    message_ids: {
                        string: "messages",
                        type: "one2many",
                        relation: 'mail.message',
                        relation_field: "res_id",
                    },
                },
                records: [{
                    id: 2,
                    message_attachment_count: 0,
                    display_name: "first partner",
                    foo: "HELLO",
                    message_ids: [],
                }]
            },
            'ir.attachment': {
                fields: {},
                records: [],
            },
        };
        this.services = mailTestUtils.getMailServices();
    }

}, function () {

    QUnit.test('Attachment on side', function (assert) {
        assert.expect(11);

        var count = 0;
        this.data.partner.records[0].message_ids = [1];
        var messages = [{
            attachment_ids: [{
                filename: 'image1.jpg',
                id:1,
                mimetype: 'image/jpeg',
                name: 'Test Image 1',
                url: '/web/content/1?download=true',
            }],
            author_id: ["1", "Kamlesh Sulochan"],
            body: "Attachment viewer test",
            date: "2016-12-20 09:35:40",
            displayed_author: "Kamlesh Sulochan",
            id: 1,
            is_note: false,
            is_discussion: true,
            is_starred: false,
            model: 'partner',
            res_id: 2,
        }];

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form string="Partners">' +
                    '<sheet>' +
                        '<field name="foo"/>' +
                    '</sheet>' +
                    '<div class="o_attachment_preview" options="{\'order\':\'desc\'}"></div>' +
                    '<div class="oe_chatter">' +
                        '<field name="message_ids" widget="mail_thread" options="{\'display_log_button\': True}"/>' +
                    '</div>' +
                '</form>',
            res_id: 2,
            config: {
                device: {
                    size_class: config.device.SIZES.XXL,
                },
            },
            mockRPC: function (route, args) {
                if (args.method === 'search_read') {
                    if (count === 0) {
                        return $.when([messages[0].attachment_ids[0]]);
                    }
                    else {
                        return $.when([messages[0].attachment_ids[0],
                                       messages[1].attachment_ids[0]]);
                    }
                }
                if (args.method === 'message_format') {
                    var requestedMessages = _.filter(messages, function (message) {
                        return _.contains(args.args[0], message.id);
                    });
                    return $.when(requestedMessages);
                }
                if (args.method === 'message_get_suggested_recipients') {
                    return $.when({2: []});
                }
                if (_.str.contains(route, '/web/static/lib/pdfjs/web/viewer.html')){
                    var canvas = document.createElement('canvas');
                    return $.when(canvas.toDataURL());
                }
                if (args.method === 'message_post') {
                    messages.push({
                        attachment_ids: [{
                            filename: 'invoice.pdf',
                            id: 2,
                            mimetype: 'application/pdf',
                            name: 'INV007/2018',
                            url: '/web/content/1?download=true',
                        }],
                        author_id: ["5", "Bhallaldeva"],
                        body: args.kwargs.body,
                        date: "2016-12-20 10:35:40",
                        displayed_author: "Bhallaldeva",
                        id: 5,
                        is_note: false,
                        is_discussion: true,
                        is_starred: false,
                        model: 'partner',
                        res_id: 2,
                    });
                    return $.when(5);
                }
                if (args.method === 'register_as_main_attachment') {
                    return $.when(true);
                }
                return this._super.apply(this, arguments);
            },
            intercepts: {
                preview_attachment: function (event) {
                    if (count === 0) {
                        assert.strictEqual(event.data.attachments[0].id, 1,
                            "Chatter should trigger existing image attachment data for preview");
                    } else if (count === 1) {
                        assert.strictEqual(event.data.attachments[1].id, 2,
                            "Chatter should trigger new posted pdf attachment data for preview");
                    }
                    count++;
                },
            },
            services: this.services,
        });

        assert.strictEqual(form.$('.o_attachment_preview_img > img').length, 1,
            "There should be an image for attachment preview");
        assert.strictEqual(form.$('.o_form_sheet_bg > .o_chatter').length, 1,
            "Chatter should moved inside sheet");
        assert.strictEqual(form.$('.o_form_sheet_bg + .o_attachment_preview').length, 1,
            "Attachment preview should be next sibling to .o_form_sheet_bg");

        // Don't display arrow if there is no previous/next element
        assert.strictEqual(form.$('.arrow').length, 0,
            "Don't display arrow if there is no previous/next attachment");

        // normally, send_message should trigger a reload_attachment_box...
        // since all of this is fake, we force it here.
        form.renderer.chatter._areAttachmentsLoaded = false;
        // send a message with attached PDF file
        form.$('.o_chatter_button_new_message').click();
        form.$('.oe_chatter .o_composer_text_field:first()').val("Attached the pdf file");
        form.$('.oe_chatter .o_composer_button_send').click();

        assert.strictEqual(form.$('.arrow').length, 2,
            "Display arrows if there multiple attachments");
        assert.strictEqual(form.$('.o_attachment_preview_img > img').length, 0,
            "Preview image should be removed");
        assert.strictEqual(form.$('.o_attachment_preview_container > iframe').length, 1,
            "There should be iframe for pdf viewer");
        form.$('.o_move_next').click();
        assert.strictEqual(form.$('.o_attachment_preview_img > img').length, 1,
            "Display next attachment");
        form.$('.o_move_previous').click();
        assert.strictEqual(form.$('.o_attachment_preview_container > iframe').length, 1,
            "Display preview attachment");
        form.destroy();
    });

    QUnit.test('Attachment on side on new record', function (assert) {
        assert.expect(3);

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form string="Partners">' +
                    '<sheet>' +
                        '<field name="foo"/>' +
                    '</sheet>' +
                    '<div class="o_attachment_preview" options="{\'order\':\'desc\'}"></div>' +
                    '<div class="oe_chatter">' +
                        '<field name="message_ids" widget="mail_thread" options="{\'display_log_button\': True}"/>' +
                    '</div>' +
                '</form>',
            config: {
                device: {
                    size_class: config.device.SIZES.XXL,
                },
            },
            services: this.services,
        });

        assert.strictEqual(form.$('.o_form_sheet_bg .o_attachment_preview').length, 1,
            "the preview should not be displayed");
        assert.strictEqual(form.$('.o_form_sheet_bg .o_attachment_preview').children().length, 0,
            "the preview should be empty");
        assert.strictEqual(form.$('.o_form_sheet_bg + .o_chatter').length, 1,
            "chatter should not have been moved");

        form.destroy();
    });

    QUnit.test('Attachment on side not displayed on smaller screens', function (assert) {
        assert.expect(2);

        this.data.partner.records[0].message_ids = [1];
        var messages = [{
            attachment_ids: [{
                filename: 'image1.jpg',
                id:1,
                mimetype: 'image/jpeg',
                name: 'Test Image 1',
                url: '/web/content/1?download=true',
            }],
            author_id: ["1", "Kamlesh Sulochan"],
            body: "Attachment viewer test",
            date: "2016-12-20 09:35:40",
            displayed_author: "Kamlesh Sulochan",
            id: 1,
            is_note: false,
            is_discussion: true,
            is_starred: false,
            model: 'partner',
            res_id: 2,
        }];

        var form = createView({
            View: FormView,
            model: 'partner',
            data: this.data,
            arch: '<form string="Partners">' +
                    '<sheet>' +
                        '<field name="foo"/>' +
                    '</sheet>' +
                    '<div class="o_attachment_preview" options="{\'order\':\'desc\'}"></div>' +
                    '<div class="oe_chatter">' +
                        '<field name="message_ids" widget="mail_thread" options="{\'display_log_button\': True}"/>' +
                    '</div>' +
                '</form>',
            res_id: 2,
            config: {
                device: {
                    size_class: config.device.SIZES.XL,
                },
            },
            mockRPC: function (route, args) {
                if (args.method === 'message_format') {
                    var requestedMessages = _.filter(messages, function (message) {
                        return _.contains(args.args[0], message.id);
                    });
                    return $.when(requestedMessages);
                }
                return this._super.apply(this, arguments);
            },
            services: this.services,
        });
        assert.strictEqual(form.$('.o_attachment_preview').children().length, 0,
            "there should be nothing previewed");
        assert.strictEqual(form.$('.o_form_sheet_bg + .o_chatter').length, 1,
            "chatter should not have been moved");

        form.destroy();
    });


});


});
