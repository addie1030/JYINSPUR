odoo.define('documents.tour', function(require) {
"use strict";

var core = require('web.core');
var tour = require('web_tour.tour');

var _t = core._t;

tour.register('documents_tour', {
    url: "/web",
}, [{
    trigger: '.o_app[data-menu-xmlid="documents.menu_root"]',
    content: _t("Want to become a <b>paperless company</b>? Let's discover Odoo DMS."),
    position: 'bottom',
}, {
    trigger: '.o_kanban_record:contains(People)',
    content: _t("Click on a card to <b>view the document</b>."),
    position: 'bottom',
}, {
    trigger: '.o_preview_available',
    content: _t("Go to the <b>images, videos & PDF viewer</b> by clicking on the preview area."),
    position: 'bottom',
}, {
    trigger: '.o_close_btn',
    extra_trigger: '.o_documents_kanban',
    content: _t("<b>Close the preview</b> to go back to your selection of documents"),
    position: 'left',
}, {
    trigger: '.o_inspector_open_chatter',
    content: _t("This icons gets you to the <b>discussion board</b>, to chat with followers of this document"),
    position: 'left',
}, {
    trigger: '.o_chatter_button_new_message',
    extra_trigger: '.o_documents_kanban',
    content: _t("Try to <b>post a message</b>"),
    position: 'bottom',
}, {
    trigger: '.o_composer_button_send',
    extra_trigger: '.o_documents_kanban',
    content: _t("It will be sent to the followers of this document"),
    position: 'bottom',
}, {
    trigger: '.o_document_close_chatter',
    extra_trigger: '.o_documents_kanban',
    content: _t("Click here to <b>close the discussion board</b>"),
    position: 'bottom',
}, {
    trigger: '.o_inspector_trigger_rule',
    extra_trigger: '.o_documents_kanban',
    content: _t("<b>Actions</b> allows you to assign tags, automate actions like creating a task or vendor bill,</br> create activities for users, etc.</br> Actions can be customized through the Configuration menu."),
    position: 'left',
}, {
    trigger: "span:contains('Finance')",
    extra_trigger: '.o_documents_kanban',
    content: _t("Use <b>folders</b> to organize documents by departments, or group of interests"),
    position: 'right',
}, {
    trigger: "label:contains('Inbox')",
    extra_trigger: '.o_documents_kanban',
    content: _t("<b>Use tags</b> to easily filter documents. Tags are defined according to the folder."),
    position: 'right',
}, {
    trigger: ".o_documents_kanban_upload",
    content: _t("When you <b>upload documents</b>, they appear in the selected folder and tags."),
    position: 'bottom',
}, {
    trigger: '.o_inspector_archive',
    extra_trigger: '.o_documents_kanban',
    content: _t("To delete files, archive them first. </br>Archived documents can still be accessed using the Archive option in the Filters top menu."),
    position: 'left',
}]);
});
