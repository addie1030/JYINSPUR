odoo.define('website_calendar.select_appointment_type', function (require) {
    'use strict';

    require('web_editor.ready');
    var ajax = require('web.ajax');

    if (!$('.o_website_calendar_appointment').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_website_calendar_appointment'");
    }

    // set default timezone
    var timezone = jstz.determine();
    $(".o_website_appoinment_form select[name='timezone']").val(timezone.name());
    // on appointment type change: adapt appointment intro text and available employees (if option enabled)
    $(".o_website_appoinment_form select[id='calendarType']").change(
        _.debounce(function () {
            var appointment_id = $(this).val();
            var previous_selected_employee_id = $(".o_website_appoinment_form select[name='employee_id']").val();
            var post_url = '/website/calendar/' + appointment_id + '/appointment';
            $(".o_website_appoinment_form").attr('action', post_url);
            ajax.jsonRpc("/website/calendar/get_appointment_info", 'call', {
                appointment_id: appointment_id,
                prev_emp: previous_selected_employee_id,
            }).then(function (data) {
                if (data) {
                    $('.o_calendar_intro').html(data.message_intro);
                    if (data.assignation_method === 'chosen') {
                        $(".o_website_appoinment_form div[name='employee_select']").replaceWith(data.employee_selection_html);
                    } else {
                        $(".o_website_appoinment_form div[name='employee_select']").addClass('o_hidden');
                        $(".o_website_appoinment_form select[name='employee_id']").children().remove();
                    }
                }
            });
        }, 250)
    );
});

odoo.define('website_calendar.appointment_form', function (require) {
    'use strict';

    require('web_editor.ready');

    if (!$('.o_website_calendar_form').length) {
        return $.Deferred().reject("DOM doesn't contain '.o_website_calendar_form'");
    }

    $(".appointment_submit_form select[name='country_id']").change(function () {
        var country_code = $(this).find('option:selected').data('phone-code');
        $('.appointment_submit_form #phone_field').val(country_code);
    });
});
