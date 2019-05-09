odoo.define('hr_contract_salary.tour', function (require) {
'use strict';

var Tour = require('web_tour.tour');

Tour.register('hr_contract_salary_tour', {
        test: true,
        url: '/',
        wait_for: $.when(odoo.__TipTemplateDef)
    },[
        {
            content: "Go on configurator",
            trigger: 'nav.o_main_navbar',
            run: function () {
                window.location.href = window.location.origin + '/web';
            },
        },

        {
            content: "Recruitment",
            trigger: 'a[data-menu-xmlid="hr_recruitment.menu_hr_recruitment_root"]',
            run: 'click',
        },
        {
            content: "Select Experienced Developer",
            trigger: ".o_kanban_record:eq(3) .oe_kanban_action_button",
            run: 'click',
        },
        {
            content: "Create Applicant",
            trigger: '.o_cp_buttons .o-kanban-button-new',
            extra_trigger: 'li.active:contains("Applications")',
            run: 'click',
        },
        {
            content: "Application Name",
            trigger: '.oe_title input[name="name"]',
            run: "text Mitchell's Application",
        },
        {
            content: "Applicant\'s Name",
            trigger: '.oe_title input[name="partner_name"]',
            run: 'text Mitchell Admin',
        },
        {
            content: "Applicant Contact",
            trigger: '.o_field_widget.o_field_many2one[name=partner_id]',
            run: function (actions) {
                actions.text("Mitchell", this.$anchor.find("input"));
            },
        },
        {
            trigger: ".ui-autocomplete > li > a:contains(Mitchell)",
            auto: true,
        },
        {
            content: "Create Employee",
            trigger: ".o_statusbar_buttons > button[name='create_employee_from_applicant']",
            extra_trigger: ".o_statusbar_buttons",
            run: 'click',
        },
        {
            content: "Save",
            trigger: '.o_form_buttons_edit .o_form_button_save',
            extra_trigger: '.oe_button_box .o_button_icon.fa-archive',
            run: 'click',
        },
        {
            content: "Create Contract",
            trigger: '.oe_button_box .oe_stat_button:contains("Contracts")',
            extra_trigger: '.o_cp_buttons .btn-primary.o_form_button_edit',
            run: 'click',
        },
        {
            content: "Create",
            trigger: '.o_cp_buttons .o-kanban-button-new',
            extra_trigger: 'li.active:contains("Contracts")',
            run: 'click',
        },
        {
            content: "Contract Reference",
            trigger: '.oe_title input[name="name"]',
            run: 'text Mitchell Admin PFI Contract',
        },
        {
            content: "Salary Structure",
            trigger: '.o_field_widget.o_field_many2one[name=struct_id]',
            run: function (actions) {
                actions.text("Belgian Employee", this.$anchor.find("input"));
            },
        },
        {
            trigger: ".ui-autocomplete > li > a:contains('Belgian Employee')",
            auto: true,
        },
        {
            content: "HR Responsible",
            trigger: '.o_field_widget.o_field_many2one[name=hr_responsible_id]',
            run: function (actions) {
                actions.text("Marc Demo", this.$anchor.find("input"));
            },
        },
        {
            trigger: ".ui-autocomplete > li > a:contains('Marc Demo')",
            auto: true,
        },
        {
            content: "Contract Update Template",
            trigger: '.o_field_widget.o_field_many2one[name=contract_update_template_id]',
            run: function (actions) {
                actions.text("CDI", this.$anchor.find("input"));
            },
        },
        {
            trigger: ".ui-autocomplete > li > a:contains('CDI - Experienced Developer')",
            auto: true,
        },
        {
            content: "Contract Information",
            trigger: ".o_content .o_form_view .o_notebook li.nav-item:eq(1) a",
            run: "click",
        },
        {
            content: "Contract Information",
            trigger: "div.o_input[name='wage'] input",
            run: "text 2950",
        },
        {
            content: "Contract Information",
            trigger: "div.o_input[name='fuel_card'] input",
            run: "text 250",
        },
        {
            content: "Contract Information",
            trigger: "div.o_input[name='commission_on_target'] input",
            run: "text 1000",
        },
        {
            content: "Contract Information",
            trigger: "div.o_field_boolean[name='transport_mode_car'] input",
            run: "click",
        },
        {
            content: "Contract Information",
            trigger: '.o_field_widget.o_field_many2one[name=car_id]',
            run: function (actions) {
                actions.text("JFC", this.$anchor.find("input"));
            },
        },
        {
            trigger: ".ui-autocomplete > li > a:contains('1-JFC-095')",
            auto: true,
        },
        {
            content: "Contract Information",
            trigger: "input.o_input[name='ip_wage_rate']",
            run: "text 25",
        },
        {
            content: "Contract Information",
            trigger: "div.o_field_boolean[name='ip'] input",
            run: "click",
        },
        {
            content: "Generate Simulation Link",
            trigger: ".o_statusbar_buttons > button.btn-primary span:contains('Simulation')",
            extra_trigger: ".o_statusbar_buttons",
            run: 'click',
        },
        {
            content: "Send Offer",
            trigger: "button[name='send_offer']",
            run: 'click',
        },
        {
            content: "Send Offer",
            trigger: "button[name='action_send_mail']",
            run: 'click',
        },
        {
            content: "Go on configurator",
            trigger: '.o_mail_thread .o_thread_message:eq(0) a',
            run: function () {
                var simulation_link = $(".o_mail_thread .o_thread_message:eq(0) a")[0].href;
                // Retrieve the link without the origin to avoid
                // mismatch between localhost:8069 and 127.0.0.1:8069 
                // when running the tour with chrome headless
                var regex = '/salary_package/simulation/.*';
                var url = simulation_link.match(regex)[0];
                window.location.href = window.location.origin + url;
            },
        },
        {
            content: "BirthDate",
            trigger: 'input[name="birthdate"]',
            run: function () {
                $("input[name='birthdate']").val('2017-09-01');
            },
        },
        {
            content: "National Identification Number",
            trigger: 'input[name="national_number"]',
            run: 'text 11.11.11-111.11',
        },
        {
            content: "Street",
            trigger: 'input[name="street"]',
            run: 'text Rue des Wallons',
        },
        {
            content: "City",
            trigger: 'input[name="city"]',
            run: 'text Louvain-la-Neuve',
        },
        {
            content: "Zip Code",
            trigger: 'input[name="zip"]',
            run: 'text 1348',
        },
        {
            content: "Email",
            trigger: 'input[name="email"]',
            run: 'text mitchell.stephen@example.com',
        },
        {
            content: "Phone Number",
            trigger: 'input[name="phone"]',
            run: 'text 1234567890',
        },
        {
            content: "Phone Number",
            trigger: 'input[name="place_of_birth"]',
            run: 'text Brussels',
        },
        {
            content: "KM Home/Work",
            trigger: 'input[name="km_home_work"]',
            run: 'text 75',
        },
        {
            content: "School",
            trigger: 'input[name="certificate_school"]',
            run: 'text UCL',
        },
        {
            content: "School Level",
            trigger: 'input[name="certificate_name"]',
            run: 'text Civil Engineering, Applied Mathematics',
        },
        {
            content: "Bank Account",
            trigger: 'input[name="bank_account"]',
            run: 'text BE10 3631 0709 4104',
        },
        {
            content: "Bank Account",
            trigger: 'input[name="emergency_person"]',
            run: 'text Batman',
        },
        {
            content: "Bank Account",
            trigger: 'input[name="emergency_phone_number"]',
            run: 'text +32 2 290 34 90',
        },
        {
            content: "Nationality",
            trigger: 'select[name="nationality"]',
            run: 'text Belgium',
        },
        {
            content: "Country of Birth",
            trigger: 'select[name="country_of_birth"]',
            run: 'text Belgium',
        },
        {
            content: "Country",
            trigger: 'select[name="country"]',
            run: 'text Belgium',
        },
        {
            content: "submit",
            trigger: 'button#hr_cs_submit',
            run: 'click',
        },
        {
            content: "Next",
            trigger: 'iframe .o_sign_sign_item_navigator',
            run: 'click',
        },
        {
            content: "Type Date",
            trigger: 'iframe input.ui-selected',
            run: 'text 17/09/2018',
        },
        {
            content: "Next",
            trigger: 'iframe .o_sign_sign_item_navigator',
            run: 'click',
        },
        {
            content: "Type Number",
            trigger: 'iframe input.ui-selected',
            run: 'text 58/4',
        },
        // fill signature
        {
            content: "Next",
            trigger: 'iframe .o_sign_sign_item_navigator',
            run: 'click',
        },
        {
            content: "Click Signature",
            trigger: 'iframe button.o_sign_sign_item',
            run: 'click',
        },
        {
            content: "Select automatic signature",
            trigger: '.o_sign_mode[data-mode=auto]',
            run: 'click',
        },
        {
            content: "Adopt and Sign",
            trigger: 'footer.modal-footer button.btn-primary',
            run: function (actions) {
                // the jsSignature library draws the signature in a setTimeout,
                // and we have to wait for it to be drawn before validating,
                // otherwise it would consider that the signature is still empty
                setTimeout(actions.auto.bind(actions), 10);
            },
        },
        // fill date
        {
            content: "Next",
            trigger: 'iframe .o_sign_sign_item_navigator',
            run: 'click',
        },
        {
            content: "Type Date",
            trigger: 'iframe input.ui-selected',
            run: 'text 17/09/2018',
        },
        {
            content: "Validate and Sign",
            trigger: ".o_sign_validate_banner button",
            run: 'click',
        },
    ]
);

});
