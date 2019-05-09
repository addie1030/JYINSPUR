odoo.define('web_enterprise.mobile_menu_tests', function (require) {
"use strict";

var Menu = require('web_enterprise.Menu');
var testUtils = require('web.test_utils');
var SystrayMenu = require('web.SystrayMenu');
var UserMenu = require('web.UserMenu');

/**
 * create a menu from given parameters.
 *
 * @param {Object} params This object will be given to addMockEnvironment, so
 *   any parameters from that method applies
 * @param {Object} params.menuData This object will define the menu's data
 *   structure to render
 * @param {Widget[]} [params.systrayMenuItems=[]] This array will define the systray
 *  items to use. Will at least contain and default to UserMenu
 * @returns {Menu}
 */
function createMenu(params) {
    var parent = testUtils.createParent({});

    var systrayMenuItems = params.systrayMenuItems || [];
    if (params.systrayMenuItems) {
        delete params.systrayMenuItems;
    }

    var initialSystrayMenuItems = _.clone(SystrayMenu.Items);
    SystrayMenu.Items = _.union([UserMenu], systrayMenuItems);

    var menuData = params.menuData || {};
    if (params.menuData) {
        delete params.menuData;
    }

    var menu = new Menu(parent, menuData);
    testUtils.addMockEnvironment(menu, params);
    menu.appendTo($('#qunit-fixture'));

    var menuDestroy = menu.destroy;
    menu.destroy = function () {
        SystrayMenu.Items = initialSystrayMenuItems;
        menuDestroy.call(this);
        parent.destroy();
    };

    return menu;
}

QUnit.module('web_enterprise mobile_menu_tests', {
    beforeEach: function () {
        this.data = {
            all_menu_ids: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            name: "root",
            children: [{
                id: 1,
                name: "Discuss",
                children: [],
             }, {
                 id: 2,
                 name: "Calendar",
                 children: []
             }, {
                id: 3,
                name: "Contacts",
                children: [{
                    id: 4,
                    name: "Contacts",
                    children: [],
                }, {
                    id: 5,
                    name: "Configuration",
                    children: [{
                        id: 6,
                        name: "Contact Tags",
                        children: [],
                    }, {
                        id: 7,
                        name: "Contact Titles",
                        children: [],
                    }, {
                        id: 8,
                        name: "Localization",
                        children: [{
                            id: 9,
                            name: "Countries",
                            children: [],
                        }, {
                            id: 10,
                            name: "Fed. States",
                            children: [],
                        }],
                    }],
                 }],
           }],
        };
    }
}, function () {

    QUnit.module('Burger Menu');

    QUnit.test('Burger Menu on home menu', function (assert) {
        assert.expect(1);

        var mobileMenu = createMenu({ menuData: this.data });

        mobileMenu.$('.o_mobile_menu_toggle').click();
        assert.ok(!$(".o_burger_menu").hasClass('o_hidden'),
            "Burger menu should be opened on button click");
        mobileMenu.$('.o_burger_menu_close').click();

        mobileMenu.destroy();
    });

    QUnit.test('Burger Menu on an App', function (assert) {
        assert.expect(4);

        var mobileMenu = createMenu({ menuData: this.data });

        mobileMenu.change_menu_section(3);
        mobileMenu.toggle_mode(false);

        mobileMenu.$('.o_mobile_menu_toggle').click();
        assert.ok(!$(".o_burger_menu").hasClass('o_hidden'),
            "Burger menu should be opened on button click");
        assert.strictEqual($('.o_burger_menu .o_burger_menu_app .o_menu_sections > *').length, 2,
            "Burger menu should contains top levels menu entries");
        $('.o_burger_menu_topbar').click();
        assert.ok(!$(".o_burger_menu_content").hasClass('o_burger_menu_dark'),
            "Toggle to usermenu on header click");
        $('.o_burger_menu_topbar').click();
        assert.ok($(".o_burger_menu_content").hasClass('o_burger_menu_dark'),
            "Toggle back to main sales menu on header click");

        mobileMenu.destroy();
    });
});
});
