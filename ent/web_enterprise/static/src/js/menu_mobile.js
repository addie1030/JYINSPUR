odoo.define('web_enterprise.MenuMobile', function (require) {
"use strict";

/**
 * This file includes the widget Menu in mobile to render the BurgerMenu which
 * opens fullscreen and displays the user menu and the current app submenus.
 */

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var Menu = require('web_enterprise.Menu');

var QWeb = core.qweb;

if (!config.device.isMobile) {
    return;
}

Menu.include({
    events: _.extend({}, Menu.prototype.events, {
        'click .o_mobile_menu_toggle': '_onOpenBurgerMenu',
    }),
    menusTemplate: 'Menu.sections.mobile',

    /**
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments).then(this._renderBurgerMenu.bind(this));
    },
    /**
     * @override
     */
    destroy: function () {
        this.$burgerMenu.remove();
        this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _closeBurgerMenu: function () {
        var self = this;
        this.$burgerMenu.animate({left: '100%'}, 200, function () {
            self.$burgerMenu.addClass("o_hidden");
        });
    },
    /**
     * @private
     */
    _renderBurgerMenu: function () {
        this.$burgerMenu = $(QWeb.render('BurgerMenu', {session: session}));
        this.$burgerMenu.addClass("o_hidden");

        // move user menu and app sub menus inside the burger menu
        this.$('.o_user_menu_mobile').appendTo(this.$burgerMenu.find('.o_burger_menu_user'));
        this.$section_placeholder.appendTo(this.$burgerMenu.find('.o_burger_menu_app'));

        this.$burgerMenu.on('click', '.o_burger_menu_close', this._onCloseBurgerMenu.bind(this));
        this.$burgerMenu.on('click', '.o_burger_menu_company', this._onCompanyClicked.bind(this));
        this.$burgerMenu.on('click', '.o_burger_menu_topbar.o_toggler', this._onTopbarClicked.bind(this));
        this.$burgerMenu.on('click', '.o_burger_menu_section', this._onBurgerMenuSectionClick.bind(this));

        $('body').append(this.$burgerMenu);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Toggles the clicked sub menu
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onBurgerMenuSectionClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $target = $(ev.currentTarget);
        $target.toggleClass('show');
        $target.find('> a .toggle_icon').toggleClass('fa-chevron-down fa-chevron-right');
    },
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onCloseBurgerMenu: function (ev) {
        ev.stopPropagation();
        this._closeBurgerMenu();
    },
    /**
     * Switches company
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onCompanyClicked: function (ev) {
        ev.preventDefault();
        this._rpc({
            model: 'res.users',
            method: 'write',
            args: [[session.uid], {company_id: $(ev.currentTarget).data('id')}],
        }).then(function () {
            window.location.reload();
        });
    },
    /**
     * Opens burger menu in mobile
     *
     * @private
     * @param {MouseEvent} event
     */
    _onOpenBurgerMenu: function (ev) {
        ev.preventDefault();

        // update the burger menu content: either display the submenus (if we
        // are in an app, and if it contains submenus) or the user menu
        var displaySubMenus = !this.home_menu_displayed;
        if (displaySubMenus) {
            var app = _.findWhere(this.menu_data.children, {id: this.current_primary_menu});
            displaySubMenus = !!(app && app.children.length);
        }
        this.$burgerMenu.find('.o_burger_menu_topbar').toggleClass('o_toggler', displaySubMenus);
        this.$burgerMenu.find('.o_burger_menu_content').toggleClass('o_burger_menu_dark', displaySubMenus);
        this.$burgerMenu.find('.o_burger_menu_caret').toggleClass('o_hidden', !displaySubMenus);
        this.$burgerMenu.find('.o_burger_menu_app').toggleClass('o_hidden', !displaySubMenus);
        this.$burgerMenu.find('.o_burger_menu_user').toggleClass('o_hidden', displaySubMenus);

        // display the burger menu
        this.$burgerMenu.css({left: '100%'});
        this.$burgerMenu.animate({left: '0%'}, 200).removeClass('o_hidden');
    },
    /**
     * @override
     * @private
     */
    _on_secondary_menu_click: function () {
        this._super.apply(this, arguments);
        this._closeBurgerMenu();
    },
    /**
     * Toggles user menu and app submenus
     *
     * @private
     */
    _onTopbarClicked: function () {
        this.$burgerMenu.find('.o_burger_menu_content').toggleClass('o_burger_menu_dark');
        this.$burgerMenu.find('.o_burger_menu_caret').toggleClass('dropup');
        this.$burgerMenu.find('.o_burger_menu_app, .o_burger_menu_user').toggleClass('o_hidden');
        this.$burgerMenu.find('.o_burger_menu_app .fa-chevron-down').toggleClass('fa-chevron-down fa-chevron-right');
    },
});

});
