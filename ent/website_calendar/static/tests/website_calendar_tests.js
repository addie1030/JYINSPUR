odoo.define('website_calendar.tests', function (require) {
"use strict";

var FormView = require('web.FormView');
var testUtils = require('web.test_utils');

var createView = testUtils.createView;

QUnit.module('website_calendar', {
    beforeEach: function () {
        this.data = {
            'calendar.appointment.type': {
                fields: {
                    name: {type: 'char'},
                    website_url: {type: 'char'},
                    employee_ids: {type: 'many2many', relation: 'hr.employee'},
                },
                records: [{
                    id: 1,
                    name: 'Very Interdesting Meeting',
                    website_url: '/website/calendar/schedule-a-demo-1/appointment',
                    employee_ids: [214],
                }],
            },
            'hr.employee': {
                fields: {
                    id: {type: 'integer'},
                    name: {type: 'char'},
                },
                records: [{
                    id: 214,
                    name: 'Denis Ledur',
                },{
                    id: 216,
                    name: 'Bhailalbhai',
                }],
            },
        };
    },
}, function () {

    QUnit.test("empty previous_order widget", function (assert) {
        assert.expect(2);

        var form = createView({
            View: FormView,
            arch: '<form>' +
                    '<field name="website_url" invisible="1"/>' +
                    '<sheet>' +
                        '<field name="employee_ids">' +
                            '<tree string="Employees">' +
                                '<field name="name"/>' +
                                '<field name="id" widget="appointment_employee_url" string="Individual Appointment Link" context="{\'url\': parent.website_url}" readonly="1"/>' +
                            '</tree>' +
                            '<form string="Employees">' +
                                '<group>' +
                                    '<field name="name" class="avoid_me"/>' +
                                '</group>' +
                            '</form>' +
                        '</field>' +
                    '</sheet>' +
                  '</form>',
            data: this.data,
            res_id: 1,
            session: {
                'web.base.url': 'http://amazing.odoo.com',
            },
            model: 'calendar.appointment.type',
        });

        assert.strictEqual(form.$('.o_form_uri').attr('href'),
            'http://amazing.odoo.com/website/calendar/schedule-a-demo-1?employee_id=214',
            'Wrong employee url copied.');

        form.$('.o_website_calendar_copy_icon').click();
        // ensure we didn't open the form view
        assert.ok($('.avoid_me').length === 0);

        form.destroy();
    }),

    QUnit.test("new record appointment_employee_url widget", function (assert) {
        assert.expect(3);
        this.data['calendar.appointment.type'].fields.employee_ids.default = [[6, 0, [214,216]]];

        var form = createView({
            View: FormView,
            arch: '<form>' +
                    '<sheet>' +
                        '<field name="website_url" />' +
                        '<field name="employee_ids">' +
                            '<tree string="Employees">' +
                                '<field name="name"/>' +
                                '<field name="id" widget="appointment_employee_url" string="Individual Appointment Link" context="{\'url\': parent.website_url}" readonly="1"/>' +
                            '</tree>' +
                        '</field>' +
                    '</sheet>' +
                  '</form>',
            data: this.data,
            res_id: 1,
            session: {
                'web.base.url': 'http://amazing.odoo.com',
            },
            model: 'calendar.appointment.type'
        });

        form.$buttons.find('.o_form_button_create').click();

        assert.strictEqual(form.$('.o_appointment_employee_url_cell').val(), '',
            'No Value should display while creating new record');

        form.$("[name='website_url']").val('/aaa/aaa/').trigger('input');
        form.$buttons.find('.o_form_button_save').click();

        form.$('.o_form_uri').each(function (i,r) {
            var link = "";
            if (i === 1) {
                link = "http://amazing.odoo.com/aaa/aaa/?employee_id=216"
            } else {
                link = "http://amazing.odoo.com/aaa/aaa/?employee_id=214"
            }
            assert.strictEqual($(r).attr('href'), link,
                'employee url with specific id should Create.');
        });
        form.destroy();
    });
});
});
