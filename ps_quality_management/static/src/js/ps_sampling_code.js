odoo.define('ps_quality_management.quality_sampling_code_report', function (require) {
    'use strict';

    var core = require('web.core');
    var stock_report_generic = require('stock.stock_report_generic');

    var sampling_code_report = stock_report_generic.extend({

        get_html: function () {
            var self = this;
            var args = [
                this.given_context.active_id
            ];
            return this._rpc({
                model: 'report.report_ps_quality_sampling_code',
                method: 'get_html',
                args: args,
                context: this.given_context,
            })
                .then(function (result) {
                    self.data = result;
                });
        },
        set_html: function () {
            var self = this;
            return this._super().then(function () {
                self.$el.html(self.data.lines);
            });
        },
        //     render_html: function (event, $el, result) {
        //         if (result.indexOf('mrp.document') > 0) {
        //             if (this.$('.o_mrp_has_attachments').length === 0) {
        //                 var column = $('<th/>', {
        //                     class: 'o_mrp_has_attachments',
        //                     title: 'Files attached to the product Attachments',
        //                     text: 'Attachments',
        //                 });
        //                 this.$('table thead th:last-child').after(column);
        //             }
        //         }
        //         $el.after(result);
        //         $(event.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
        //     },
        //     _onClickUnfold: function (ev) {
        //         var redirect_function = $(ev.currentTarget).data('function');
        //         this[redirect_function](ev);
        //     },
        //     _onClickFold: function (ev) {
        //         this._removeLines($(ev.currentTarget).closest('tr'));
        //         $(ev.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
        //     },
        //     _onClickAction: function (ev) {
        //         ev.preventDefault();
        //         return this.do_action({
        //             type: 'ir.actions.act_window',
        //             res_model: $(ev.currentTarget).data('model'),
        //             res_id: $(ev.currentTarget).data('res-id'),
        //             views: [[false, 'form']],
        //             target: 'current'
        //         });
        //     },
        //     _onClickShowAttachment: function (ev) {
        //         ev.preventDefault();
        //         var ids = $(ev.currentTarget).data('res-id');
        //         return this.do_action({
        //             name: _t('Attachments'),
        //             type: 'ir.actions.act_window',
        //             res_model: $(ev.currentTarget).data('model'),
        //             domain: [['id', 'in', ids]],
        //             views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
        //             view_mode: 'kanban,list,form',
        //             target: 'current',
        //         });
        //     },
    });
    core.action_registry.add('quality_sampling_code_report', sampling_code_report);
    return sampling_code_report;
});