odoo.define('web_studio.tour', function(require) {
"use strict";

var core = require('web.core');
var tour = require('web_tour.tour');

var utils = require('web_studio.utils');

var _t = core._t;

tour.register('web_studio_home_menu_background_tour', {
    url: "/web",
}, [{
    trigger: '.o_web_studio_navbar_item',
    content: _t('Want to customize the background? Let’s activate <b>Odoo Studio</b>.'),
    position: 'bottom',
    extra_trigger: '.o_home_menu',
}, {
    trigger: '.o_web_studio_home_studio_menu a',
    content: _t('Click here.'),
    position: 'right',
}, {
    trigger: '.o_web_studio_home_studio_menu .dropdown-menu .dropdown-item:eq(0)',
    content: _t('Change the <b>background</b>, make it yours.'),
    position: 'bottom',
}]);

tour.register('web_studio_new_app_tour', {
    url: "/web?studio=app_creator",
}, [{
    trigger: '.o_web_studio_new_app',
    auto: true,
    position: 'bottom',
}, {
    trigger: '.o_web_studio_app_creator_next',
    content: _t('I bet you can <b>build an app</b> in 5 minutes. Ready for the challenge?'),
    position: 'top',
}, {
    trigger: '.o_web_studio_app_creator_name > input',
    content: _t('How do you want to <b>name</b> your app? Library, Academy, …?'),
    position: 'right',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_web_studio_selectors .o_web_studio_selector:eq(2)',
    content: _t('Now, customize your icon. Make it yours.'),
    position: 'top',
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
    content: _t('Go on, you are almost done!'),
    position: 'top',
}, {
    trigger: '.o_web_studio_app_creator_menu > input',
    content: _t('How do you want to name your first <b>menu</b>? My books, My courses?'),
    position: 'right',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
    content: _t('You are just one click away from <b>generating your first app</b>.'),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    content: _t('Nicely done! Let’s build your screen now; <b>drag</b> a <i>text field</i> and <b>drop</b> it in your view, on the right.'),
    position: 'bottom',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    trigger: '.o_web_studio_form_view_editor td.o_td_label',
    content: _t('To <b>customize a field</b>, click on its <i>label</i>.'),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_sidebar_content.o_display_field input[name="string"]',
    content: _t('Here, you can <b>name</b> your field (e.g. Book reference, ISBN, Internal Note, etc.).'),
    position: 'bottom',
    run: 'text My Field',
}, {
    // wait for the field to be renamed
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:contains(My Field)',
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
    content: _t('Good job! To add more <b>fields</b>, come back to the <i>Add tab</i>.'),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_selection',
    content: _t('Drag & drop <b>another field</b>. Let’s try with a <i>selection field</i>.'),
    position: 'bottom',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    trigger: '.o_web_studio_field_dialog_form > .o_web_studio_selection_new_value > input',
    content: _t("Create your <b>selection values</b> (e.g.: Romance, Polar, Fantasy, etc.)"),
    position: 'top',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_web_studio_field_dialog_form > .o_web_studio_selection_new_value button',
    auto: true,
}, {
    trigger: '.modal-footer > button:eq(0)',
    auto: true,
}, {
    trigger: '.o_web_studio_add_chatter',
    content: _t("Add a <b>chatter widget</b> to allow discussions on your document: by email or inline."),
    position: 'top',
}, {
    trigger: '.o_web_studio_form_view_editor .oe_chatter',
    content: _t("Click to edit."),
    position: 'top',
}, {
    trigger: '.o_web_studio_sidebar .o_display_chatter input[name="email_alias"]',
    content: _t("Set an <b>email alias</b>. Then, try to send an email to this address; it will create a document automatically for you. Pretty cool, huh?"),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_leave',
    content: _t("Let’s check the result. Close Odoo Studio to get an <b>overview of your app</b>."),
    position: 'left',
}, {
    trigger: 'input.o_required_modifier',
    auto: true,
    position: 'bottom',
}, {
    trigger: '.o_control_panel .o_cp_buttons .o_form_button_save',
    content: _t("Save."),
    position: 'right',
}, {
    trigger: '.o_web_studio_navbar_item',
    extra_trigger: '.o_form_view.o_form_readonly',
    content: _t("Wow, nice! And I’m sure you can make it even better! Use this icon to open <b>Odoo Studio</b> and customize any screen."),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_menu .o_menu_sections a[data-name="views"]',
    content: _t("Want more fun? Let’s create more <b>views</b>."),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_view_category .o_web_studio_view_type.o_web_studio_inactive[data-type="kanban"] .o_web_studio_thumbnail',
    content: _t("What about a <b>Kanban view</b>?"),
    position: 'bottom',
}, {
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
    content: _t("Now you’re on your own. Enjoy your <b>super power</b>."),
    position: 'bottom',
}]);

tour.register('web_studio_tests_tour', {
    test: true,
    url: "/web?studio=app_creator&debug=",
}, [{
    trigger: '.o_web_studio_new_app',
}, {
    // the next 6 steps are here to create a new app
    trigger: '.o_web_studio_app_creator_next',
}, {
    trigger: '.o_web_studio_app_creator_name > input',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_web_studio_selectors .o_web_studio_selector:eq(2)',
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
}, {
    trigger: '.o_web_studio_app_creator_menu > input',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_web_studio_app_creator_next.is_ready',
}, {
    // toggle the home menu
    trigger: '.o_menu_toggle.fa-th',
}, {
    // a invisible element cannot be used as a trigger so this small hack is
    // mandatory for the next step
    trigger: '.o_app[data-menu-xmlid*="studio"]:last',
    run: function () {
        this.$anchor.find('.o_web_studio_edit_icon').css('visibility', 'visible');
    },
}, {
    // edit an app
    trigger: '.o_app[data-menu-xmlid*="studio"]:last .o_web_studio_edit_icon',
}, {
    // design the icon
    trigger: '.o_web_studio_selector[data-type="background_color"]',
}, {
    trigger: '.o_web_studio_palette > .o_web_studio_selector:first',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // click on the created app
    trigger: '.o_app[data-menu-xmlid*="studio"]:last',
}, {
    // create a new menu
    trigger: '.o_main_navbar .o_web_edit_menu',
}, {
    trigger: '.o_web_studio_edit_menu_modal .js_add_menu',
}, {
    trigger: 'input[name="name"]',
    run: 'text ' + utils.randomString(6),
}, {
    trigger: '.o_field_many2one[name="model"] input',
    run: 'text a',
}, {
    trigger: '.ui-autocomplete > .ui-menu-item:first > a',
    in_modal: false,
}, {
    trigger: 'button:contains(Confirm):not(".disabled")',
},{
    trigger: 'button:contains(Confirm):not(".disabled")',
}, {
    // check that the Studio menu is still there
    extra_trigger: '.o_web_studio_menu',
    // switch to form view
    trigger: '.o_web_studio_views_icons > a[data-name="form"]',
}, {
    // wait for the form editor to be rendered because the sidebar is the same
    extra_trigger: '.o_web_studio_form_view_editor',
    // add an existing field (display_name)
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    // click on the field
    trigger: '.o_web_studio_form_view_editor td.o_td_label:first',
}, {
    // rename the label
    trigger: '.o_web_studio_sidebar_content.o_display_field input[name="string"]',
    run: 'text My Coucou Field',
}, {
    // verify that the field name has changed and change it
    trigger: 'input[data-type="field_name"][value="my_coucou_field"]',
    run: 'text coucou',
}, {
    // click on "Add" tab
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a new field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    // click on the new field
    trigger: '.o_web_studio_form_view_editor td.o_td_label:eq(1)',
}, {
    // rename the field with the same name
    trigger: 'input[data-type="field_name"]',
    run: 'text coucou',
}, {
    // an alert dialog should be opened
    trigger: '.modal-footer > button:first',
}, {
    // rename the label
    trigger: '.o_web_studio_sidebar_content.o_display_field input[name="string"]',
    run: 'text COUCOU',
}, {
    // verify that the field name has changed (post-fixed by _1)
    extra_trigger: 'input[data-type="field_name"][value="coucou_1"]',
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a monetary field --> create a currency field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_monetary',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    // verify that the currency field is in the view
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:contains("Currency")',
    trigger: '.o_web_studio_sidebar .o_web_studio_new',
}, {
    // add a monetary field
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_monetary',
    run: 'drag_and_drop .o_web_studio_form_view_editor .o_inner_group',
}, {
    // verify that the monetary field is in the view
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:eq(1):contains("New Monetary")',
    // switch the two first fields
    trigger: '.o_web_studio_form_view_editor .o_inner_group:first .ui-draggable:eq(1)',
    run: 'drag_and_drop .o_inner_group:first .o_web_studio_hook:first',
}, {
    // verify that the fields have been switched
    extra_trigger: '.o_web_studio_form_view_editor td.o_td_label:eq(0):contains("New Monetary")',
    // add a statusbar
    trigger: '.o_web_studio_statusbar_hook',
}, {
    trigger: '.modal-footer .btn.btn-primary',
}, {
    trigger: '.o_statusbar_status',
}, {
    // verify that a default value has been set for the statusbar
    trigger: '.o_web_studio_sidebar select[name="default_value"]:contains(First Status)',
}, {
    trigger: '.o_web_studio_views_icons a[data-name=form]',
}, {
    // verify Chatter can be added after changing view to form
    extra_trigger: '.o_web_studio_add_chatter',
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections a[data-name="views"]',
}, {
    // edit form view
    trigger: '.o_web_studio_view_category .o_web_studio_view_type[data-type="form"] .o_web_studio_thumbnail',
}, {
    // verify Chatter can be added after changing view to form
    extra_trigger: '.o_web_studio_add_chatter',
    // switch in list view
    trigger: '.o_web_studio_menu .o_web_studio_views_icons a[data-name="list"]',
}, {
    // wait for the list editor to be rendered because the sidebar is the same
    extra_trigger: '.o_web_studio_list_view_editor',
    // add an existing field (display_name)
    trigger: '.o_web_studio_sidebar .o_web_studio_field_type_container:eq(1) .o_web_studio_field_char',
    run: 'drag_and_drop .o_web_studio_list_view_editor th.o_web_studio_hook:first',
}, {
    // verify that the field is correctly named
    extra_trigger: '.o_web_studio_list_view_editor th:contains("COUCOU")',
    // leave Studio
    trigger: '.o_web_studio_leave',
}, {
    // re-open studio
    trigger: '.o_web_studio_navbar_item',
}, {
    // edit action
    trigger: '.o_web_studio_menu .o_menu_sections a[data-name="views"]',
}, {
    // add a kanban
    trigger: '.o_web_studio_view_category .o_web_studio_view_type.o_web_studio_inactive[data-type="kanban"] .o_web_studio_thumbnail',
}, {
    // enable stages
    trigger: '.o_web_studio_sidebar input[name=enable_stage]',

// TODO: we would like to test this (change an app icon) here but a
// long-standing bug (KeyError: ir.ui.menu.display_name, caused by a registry
// issue with multiple workers) on runbot prevent us from doing it. It thus have
// been moved at the beginning of this test to avoid the registry to be reloaded
// before the write on ir.ui.menu.

}, {
    trigger: '.o_menu_toggle',
}, {
    trigger: '.o_web_studio_home_studio_menu .dropdown-toggle',
}, {
    // export all modifications
    trigger: '.o_web_studio_export',
}]);

tour.register('web_studio_new_report_tour', {
    url: "/web",
    test: true,
}, [{
    // open studio
    trigger: '.o_main_navbar .o_web_studio_navbar_item',
}, {
    // click on the created app
    trigger: '.o_app[data-menu-xmlid*="studio"]:first',
}, {
    // edit reports
    trigger: '.o_web_studio_menu a[data-name="reports"]',
}, {
    // create a new report
    trigger: '.o_control_panel .o-kanban-button-new',
}, {
    // select external layout
    trigger: '.o_web_studio_report_layout_dialog div[data-layout="web.external_layout"]',
}, {
    // sidebar should display add tab
    extra_trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div.active[name="new"]',
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // edit report name
    trigger: '.o_web_studio_sidebar input[name="name"]',
    run: 'text My Awesome Report',
}, {
    // switch to 'Add' in Sidebar
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome Report"]',
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // wait for the iframe to be loaded
    extra_trigger: '.o_web_studio_report_editor iframe #wrapwrap',
    // add a 'title' building block
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Title Block)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
    auto: true,
}, {
    // click on the newly added field
    trigger: '.o_web_studio_report_editor iframe .h2 > span:contains(New Title)',
}, {
    // change the text of the H2 to 'test'
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
    run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'Test';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    extra_trigger: '.o_web_studio_report_editor iframe .h2:contains(Test)',
    // add a new group on the node
    trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] input',
    run: function () {
        this.$anchor.click();
    },
}, {
    trigger: '.ui-autocomplete:visible li:contains(Access Rights)',
}, {
    // wait for the group to appear
    extra_trigger: '.o_web_studio_sidebar .o_field_many2manytags[name="groups"] .o_badge_text:contains(Access Rights)',
    // switch to 'Add' in Sidebar
    trigger: '.o_web_studio_sidebar div[name="new"]',
}, {
    // add a 'title' building block Data Table
    trigger: '.o_web_studio_sidebar .o_web_studio_component:contains(Data table)',
    run: 'drag_and_drop .o_web_studio_report_editor iframe .article > .page',
}, {
    // expand the model selector in the popup
    trigger: 'div.o_field_selector_value',
    run: function () {
        $('div.o_field_selector_value').focusin();
    }
}, {
    // select the first element of the model (doc)
    trigger: '.o_field_selector_popover:not(.hidden) .o_field_selector_popover_body > ul > li:first()'
}, {
    // select the second element of the model (followers)
    trigger: '.o_field_selector_popover_body > ul > li:contains(Followers)'
}, {
    trigger:'.modal-content button>span:contains(Confirm)', // button
    extra_trigger:'.o_field_selector_chain_part:contains(Followers)',//content of the field is set
}, {
    // select the content of the first field of the newly added table
    trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]'
}, {
    // change the bound field
    trigger: '.o_web_studio_sidebar .card:last() div.o_field_selector_value',
    run: function () {
        $('.o_web_studio_sidebar .card:last() div.o_field_selector_value').focusin();
    }
}, {
    trigger: 'ul.o_field_selector_page li:contains(ID)'
}, {
    // update the title of the column
    trigger: '.o_web_studio_report_editor iframe table thead span:contains(Name) ', // the name title
    //extra_trigger: '.o_web_studio_report_editor iframe span[t-field="table_line.display_name"]:not(:contains(YourCompany, Administrator))', // the id has been updated in the iframe
}, {
    // update column title 'name' into another title
    trigger: '.o_web_studio_sidebar .o_web_studio_text .note-editable',
        run: function () {
        this.$anchor.focusIn();
        this.$anchor[0].firstChild.textContent = 'new column title';
        this.$anchor.keydown();
        this.$anchor.blur();
    }
}, {
    // wait to be sure the modification has been correctly applied
    extra_trigger: '.o_web_studio_report_editor iframe table thead span:contains(new column title) ',
    // leave the report
    trigger: '.o_web_studio_breadcrumb .o_back_button:contains(Reports)',
}, {
    // a invisible element cannot be used as a trigger so this small hack is
    // mandatory for the next step
    run: function () {
        $('.o_kanban_record:contains(My Awesome Report) .o_dropdown_kanban').css('visibility', 'visible');
    },
    trigger: '.o_kanban_view',
}, {
    // open the dropdown
    trigger: '.o_kanban_record:contains(My Awesome Report) .dropdown-toggle',
}, {
    // duplicate the report
    trigger: '.o_kanban_record:contains(My Awesome Report) .dropdown-menu a:contains(Duplicate)',
}, {
    // open the duplicate report
    trigger: '.o_kanban_record:contains(My Awesome Report copy(1))',
}, {
    // switch to 'Report' tab
    trigger: '.o_web_studio_report_editor_manager .o_web_studio_sidebar_header div[name="report"]',
}, {
    // wait for the duplicated report to be correctly loaded
    extra_trigger: '.o_web_studio_sidebar input[name="name"][value="My Awesome Report copy(1)"]',
    // leave Studio
    trigger: '.o_web_studio_leave',
}]);

});
