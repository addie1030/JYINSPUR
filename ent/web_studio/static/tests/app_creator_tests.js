odoo.define('web_studio.AppCreator_tests', function (require) {
"use strict";

var testUtils = require('web.test_utils');
var triggerKeypressEvent = testUtils.triggerKeypressEvent;

var AppCreator = require('web_studio.AppCreator');


QUnit.module('Studio', {}, function () {

    QUnit.module('AppCreator');

    QUnit.test('basic stuff', function(assert) {
        assert.expect(11);

        var $target = $('#qunit-fixture');
        var app_creator = new AppCreator(null);
        app_creator.debug = false;
        app_creator.appendTo($target);

        testUtils.addMockEnvironment(app_creator, {
            session: {},
        });

        // step 1
        assert.strictEqual(
            app_creator.currentStep,
            1,
            "currentStep should be set to 1");
        assert.strictEqual(
            app_creator.$('.o_web_studio_app_creator_back').hasClass('o_hidden'),
            true,
            "back button should be hidden at step 1");
        assert.strictEqual(
            app_creator.$('.o_web_studio_app_creator_next').hasClass('is_ready'),
            true,
            "next button should be ready at step 1");

        // go to step 2
        app_creator.$('.o_web_studio_app_creator_next').click();

        assert.strictEqual(
            app_creator.currentStep,
            2,
            "currentStep should be set to 2");

        // try to go to step 3 but cannot
        app_creator.$('.o_web_studio_app_creator_next').click();

        assert.strictEqual(
            app_creator.currentStep,
            2,
            "currentStep should not be update because the input is not filled");

        app_creator.$('input[name="app_name"]').val('Kikou');

        // go to step 3
        app_creator.$('.o_web_studio_app_creator_next').click();

        assert.strictEqual(
            app_creator.currentStep,
            3,
            "currentStep should be 3");

        app_creator.$('.o_web_studio_app_creator_next').click();

        assert.strictEqual(
            app_creator.$('input[name="menu_name"]').parent().hasClass('o_web_studio_app_creator_field_warning'),
            true,
            "a warning should be displayed on the input");

        assert.strictEqual(
            app_creator.$('input[name="model_choice"]').length,
            0,
            "it shouldn't be possible to select a model without debug");

        app_creator.debug = true;
        app_creator.update();

        app_creator.$('input[name="menu_name"]').val('Petite Perruche');

        assert.strictEqual(
            app_creator.$('input[name="model_choice"]').length,
            1,
            "it should be possible to select a model in debug");

        // click to select a model
        app_creator.$('input[name="model_choice"]').click();

        assert.strictEqual(
            app_creator.$('.o_field_many2one').length,
            1,
            "there should be a many2one to select a model");

        // unselect the model
        app_creator.$('input[name="model_choice"]').click();

        assert.strictEqual(
            app_creator.$('.o_web_studio_app_creator_next').hasClass('is_ready'),
            true,
            "next button should be ready at step 3");

        app_creator.destroy();
    });

    QUnit.test('use <Enter> in the app creator', function(assert) {
        assert.expect(5);

        var $target = $('#qunit-fixture');
        var appCreator = new AppCreator(null);
        appCreator.appendTo($target);

        testUtils.addMockEnvironment(appCreator, {
            session: {},
        });

        // step 1
        assert.strictEqual(appCreator.currentStep, 1,
            "currentStep should be set to 1");

        // go to step 2
        triggerKeypressEvent('Enter');
        assert.strictEqual(appCreator.currentStep, 2,
            "currentStep should be set to 2");

        // try to go to step 3
        triggerKeypressEvent('Enter');
        assert.strictEqual(appCreator.currentStep, 2,
            "currentStep should not be update because the input is not filled");
        appCreator.$('input[name="app_name"]').val('Kikou');

        // go to step 3
        triggerKeypressEvent('Enter');
        assert.strictEqual(appCreator.currentStep, 3,
            "currentStep should be 3");

        // try to go to step 4
        triggerKeypressEvent('Enter');
        var $menu = appCreator.$('input[name="menu_name"]').parent();
        assert.ok($menu.hasClass('o_web_studio_app_creator_field_warning'),
            "a warning should be displayed on the input");

        appCreator.destroy();
    });
});

});
