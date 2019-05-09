var QWeb = instance.web.qweb,
        _t = instance.web._t,
        _lt = instance.web._lt;
    instance.web.agh_enhance = instance.web.agh_enhance || {};
    /**
     * 合并发货
     * */
    instance.web.ListView.include({
        init: function() {
            var self = this;
            this._super.apply(this, arguments);
            this.on('list_view_loaded', this, function(data) {
                if(self.__parentedParent.$el.find('.oe_generate_po').length == 0
                    && self.dataset.model == 'ps.account.move.check' ){
                    var button = $("<button type='button' class='oe_button oe_highlight oe_generate_po'>审核</button>")
                        .click(this.proxy('create_journal_check_bill'));
                    self.__parentedParent.$el.find('.oe_list_buttons').append(button);
                }
            });
        },
        create_journal_check_bill: function () {
            var self=this;
            var ctx = this.ActionManager.action.context;
            var active_records = this.groups.get_selection();
            ctx['active_records'] = active_records;
        }
    });


