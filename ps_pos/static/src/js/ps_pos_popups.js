odoo.define('ps_point_of_sale.popups', function (require) {
    "use strict";

    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var _t  = require('web.core')._t;

    var PsPasswordPopupWidget = PosBaseWidget.extend({
        template: 'PsNumberPopupWidget',
        events: {
            'click .button.cancel':  'click_cancel',
            'click .button.confirm': 'click_confirm',
            'click .selection-item': 'click_item',
            'click .input-button':   'click_numpad',
            'click .mode-button':    'click_numpad',
        },

        init: function(parent, args) {
            this._super(parent, args);
            var self = this;
            this.keypress_handler = function (event) {
                var inputEvent = event;
                if (event.type === 'keypress'){
                    if (event.keyCode >= 48 && event.keyCode <= 57){
                        var key = event.keyCode - 48;
                        inputEvent.target = self.$(".number-char[data-action='"+key+"']")[0];
                        self.click_numpad(inputEvent);
                    } else if (event.keyCode === 13){
                        self.click_confirm();
                    }
                }

            }
        },

        show: function(options){
            if(options === undefined){
                options = {}
            }
            options = options || {};
            if (typeof options === 'string') {
                this.options = {title: options};
            } else {
                this.options = options || {};
            }
            this.options = options;

            if(this.$el){
                this.$el.removeClass('oe_hidden');
            }
            if (typeof options === 'string') {
                this.options = {title: options};
            } else {
                this.options = options || {};
            }

            this.inputbuffer = '' + (options.value   || '');
            this.decimal_separator = _t.database.parameters.decimal_point;
            this.renderElement();
            this.firstinput = true;

            $('body').on('keypress', this.keypress_handler);

        },

        renderElement: function(){
            if(this.options === undefined ){
                this.options = {}
            }
            this._super();
            this.$('.popup').addClass('popup-password');
        },

        hide: function(){
            this._super();
            var self = this;
            if (this.$el) {
                this.$el.addClass('oe_hidden');
            }
            $('body').off('keypress', this.keypress_handler);
        },

        click_confirm: function(){
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,this.inputbuffer);
            }
        },

        click_cancel: function(){
            this.gui.close_popup();
            if (this.options.cancel) {
                this.options.cancel.call(this);
            }
        },

        close: function(){

        },

        click_numpad: function(event){
            var newbuf = this.gui.numpad_input(
                this.inputbuffer,
                $(event.target).data('action'),
                {'firstinput': this.firstinput});
            this.firstinput = (newbuf.length === 0);
            if (newbuf !== this.inputbuffer) {
                this.inputbuffer = newbuf;
                this.$('.value').text(this.inputbuffer);
            }
            var $value = this.$('.value');
            $value.text($value.text().replace(/./g, '•'));
        },

    });
    gui.define_popup({name:'ps_password', widget: PsPasswordPopupWidget});

});