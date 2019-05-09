odoo.define('ps_production_data.mrp_mfq_report', function (require) {
'use strict';

var core = require('web.core');
var framework = require('web.framework');
var stock_report_generic = require('stock.stock_report_generic');

var QWeb = core.qweb;
var _t = core._t;

var  MaterialsForwardQuery = stock_report_generic.extend({
    events: {
        'click .o_mrp_bom_unfoldable': '_onClickUnfold',
        'click .o_mrp_bom_foldable': '_onClickFold',
        'click .o_mrp_bom_action': '_onClickAction',
        'click .o_mrp_show_attachment_action': '_onClickShowAttachment',
    },
    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.given_context.active_id = 0;
        this.given_context.searchProduct = 0;
    },
    get_html: function() {
        var self = this;
        if(this.given_context.hasOwnProperty("searchBomVersion")){
            if(!this.given_context.searchBomVersion){
                this.given_context.searchBomVersion = false;
            }
        }
        var args = [
            parseInt(this.given_context.searchProduct),
            this.given_context.searchQty || 1,
            parseInt(this.given_context.searchProduct),
            parseInt(this.given_context.searchBomVersion) || null,
            this.given_context.searchLayer,
        ];
        this.given_context.active_id = parseInt(self.given_context.searchProduct) || null;
        return this._rpc({
                model: 'report.ps_production_data.report_mfq_structure',
                method: 'get_html',
                args: args,
                context: this.given_context,
            })
            .then(function (result) {
                self.data = result;
            });
    },
    set_html: function() {
        var self = this;
        return this._super().then(function () {
            self.$el.html(self.data.lines);
            self.renderSearch();
            self.update_cp();
        });
    },
    render_html: function(event, $el, result){
        if (result.indexOf('mrp.document') > 0) {
            if (this.$('.o_mrp_has_attachments').length === 0) {
                var column = $('<th/>', {
                    class: 'o_mrp_has_attachments',
                    title: 'Files attached to the product Attachments',
                    text: 'Attachments',
                });
                this.$('table thead th:last-child').after(column);
            }
        }
        $el.after(result);
        $(event.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
        this._reload_report_type();
    },
    get_bom: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('id');
      var productID = $parent.data('product_id');
      var lineID = $parent.data('line');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      return this._rpc({
              model: 'report.ps_production_data.report_mfq_structure',
              method: 'get_bom',
              args: [
                  activeID,
                  productID,
                  parseFloat(qty),
                  lineID,
                  level + 1,
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    get_operations: function(event) {
      var self = this;
      var $parent = $(event.currentTarget).closest('tr');
      var activeID = $parent.data('bom-id');
      var qty = $parent.data('qty');
      var level = $parent.data('level') || 0;
      return this._rpc({
              model: 'report.ps_production_data.report_mfq_structure',
              method: 'get_operations',
              args: [
                  activeID,
                  parseFloat(qty),
                  level + 1
              ]
          })
          .then(function (result) {
              self.render_html(event, $parent, result);
          });
    },
    update_cp: function () {
        var status = {
            cp_content: {
                $buttons: this.$buttonPrint,
                $searchview_buttons: this.$searchView
            },
        };
        return this.update_control_panel(status);
    },
    renderSearch: function () {
        this.$buttonPrint = $(QWeb.render('mrp.button'));
        this.$buttonPrint.filter('.o_mrp_bom_print').on('click', this._onClickPrint.bind(this));
        this.$buttonPrint.filter('.o_mrp_bom_print_unfolded').on('click', this._onClickPrint.bind(this));
        this.$searchView = $(QWeb.render('report_materials_forward_query_search', _.omit(this.data, 'lines')));
        this.$searchView.find('.o_mrp_bom_report_product').on('change', this._onChangeProduct.bind(this));
        this.$searchView.find('.o_mrp_bom_report_bom_version').on('change', this._onChangeBomVersion.bind(this));
        this.$searchView.find('.o_mrp_bom_report_layer').on('change', this._onChangeLayer.bind(this));
    },
    _onClickPrint: function (ev) {
        var self = this;
        var childBomIDs = _.map(this.$el.find('.o_mrp_bom_foldable').closest('tr'), function (el) {
            return $(el).data('id');
        });
        framework.blockUI();
        var searchProduct = $(".o_mrp_bom_report_product").find('option:selected').attr('value');
        var searchBomVersion = $(".o_mrp_bom_report_bom_version").find('option:selected').attr('value');
        this._rpc({
            model: 'report.ps_production_data.report_mfq_structure',
            method: 'get_bom_by_version_productid',
            args: [parseInt(searchProduct), parseInt(searchBomVersion)],
        })
        .then(function (result) {
            var reportname = 'ps_production_data.report_mfq_structure?docids=' + result + '&report_type=' + self.given_context.report_type;
            if (! $(ev.currentTarget).hasClass('o_mrp_bom_print_unfolded')) {
                reportname += '&quantity=' + (self.given_context.searchQty || 1) +
                              '&childs=' + JSON.stringify(childBomIDs);
            }
            if (self.given_context.searchProduct) {
                reportname += '&variant=' + self.given_context.searchProduct;
            }
            var action = {
                'type': 'ir.actions.report',
                'report_type': 'qweb-pdf',
                'report_name': reportname,
                'report_file': 'ps_production_data.report_mfq_structure',
                'model': 'mrp.bom',
            };
            return self.do_action(action).then(function (){
                framework.unblockUI();
            });
        });
    },
    _onChangeProduct: function (ev) {
        var self = this;
        var product = $(ev.currentTarget).val().trim();
        if (product)
        {
            this.given_context.searchProduct = product;
        }

        this._rpc({
            model: 'report.ps_production_data.report_mfq_structure',
            method: 'get_bom_versions_by_productid',
            args: [parseInt(this.given_context.searchProduct)],
        })
        .then(function (result) {
            $(".o_mrp_bom_report_bom_version").empty();
            var i = 0;
            for(var key in result[0])
            {
                if(i == 0)
                {
                    $(".o_mrp_bom_report_bom_version").append("<option value='"+key+"' selected = \"selected\">" + result[0][key] + "</option>");
                }
                else
                {
                    $(".o_mrp_bom_report_bom_version").append("<option value='"+key+"'>" + result[0][key] + "</option>");
                }
                i = i + 1;
            }
            self.given_context.searchBomVersion = $(".o_mrp_bom_report_bom_version").find('option:selected').attr('value');
            self.given_context.searchLayer = $(".o_mrp_bom_report_layer").find('option:selected').attr('data-type');
            var args = [
                parseInt(self.given_context.searchProduct),
                self.given_context.searchQty || 1,
                parseInt(self.given_context.searchProduct),
                parseInt(self.given_context.searchBomVersion),
                self.given_context.searchLayer,
            ];
            self.given_context.active_id = parseInt(self.given_context.searchProduct) || null;
            self._rpc({
                model: 'report.ps_production_data.report_mfq_structure',
                method: 'get_html',
                args: args,
                context: self.given_context,
            })
            .then(function (result) {
                self.data = result;
            });
            self._reload();
        });
    },
    _onChangeLayer: function (ev) {
        var layer = $("option:selected", $(ev.currentTarget)).data('type');
        this.given_context.searchLayer = layer;
        this.given_context.searchProduct = $(".o_mrp_bom_report_product").find('option:selected').attr('value');
        this.given_context.searchBomVersion = $(".o_mrp_bom_report_bom_version").find('option:selected').attr('value');
        var self = this;
        var args = [
            parseInt(this.given_context.searchProduct),
            this.given_context.searchQty || 1,
            parseInt(this.given_context.searchProduct),
            parseInt(this.given_context.searchBomVersion),
            this.given_context.searchLayer,
        ];
        this.given_context.active_id = parseInt(self.given_context.searchProduct) || null;
        this._rpc({
            model: 'report.ps_production_data.report_mfq_structure',
            method: 'get_html',
            args: args,
            context: this.given_context,
        })
        .then(function (result) {
            self.data = result;
        });
        this._reload();
    },
    _onChangeBomVersion: function (ev) {
        this.given_context.searchBomVersion = $(ev.currentTarget).val();
        this.given_context.searchProduct = $(".o_mrp_bom_report_product").find('option:selected').attr('value');
        this.given_context.searchLayer = $(".o_mrp_bom_report_layer").find('option:selected').attr('data-type');
        var self = this;
        var args = [
            parseInt(this.given_context.searchProduct),
            this.given_context.searchQty || 1,
            parseInt(this.given_context.searchProduct),
            parseInt(this.given_context.searchBomVersion),
            this.given_context.searchLayer,
        ];
        this.given_context.active_id = parseInt(self.given_context.searchProduct) || null;
        this._rpc({
            model: 'report.ps_production_data.report_mfq_structure',
            method: 'get_html',
            args: args,
            context: this.given_context,
        })
        .then(function (result) {
            self.data = result;
        });
        this._reload();
    },
    _onClickUnfold: function (ev) {
        var redirect_function = $(ev.currentTarget).data('function');
        this[redirect_function](ev);
    },
    _onClickFold: function (ev) {
        this._removeLines($(ev.currentTarget).closest('tr'));
        $(ev.currentTarget).toggleClass('o_mrp_bom_foldable o_mrp_bom_unfoldable fa-caret-right fa-caret-down');
    },
    _onClickAction: function (ev) {
        ev.preventDefault();
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: $(ev.currentTarget).data('model'),
            res_id: $(ev.currentTarget).data('res-id'),
            views: [[false, 'form']],
            target: 'current'
        });
    },
    _onClickShowAttachment: function (ev) {
        ev.preventDefault();
        var ids = $(ev.currentTarget).data('res-id');
        return this.do_action({
            name: _t('Attachments'),
            type: 'ir.actions.act_window',
            res_model: $(ev.currentTarget).data('model'),
            domain: [['id', 'in', ids]],
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            view_mode: 'kanban,list,form',
            target: 'current',
        });
    },
    _reload: function () {
        var self = this;
        return this.get_html().then(function () {
            self.$el.html(self.data.lines);
            self._reload_report_type();
        });
    },
    _reload_report_type: function () {
        this.$('.o_mrp_bom_cost.o_hidden, .o_mrp_prod_cost.o_hidden').toggleClass('o_hidden');
        if (this.given_context.report_type === 'bom_structure') {
            this.$('.o_mrp_bom_cost').toggleClass('o_hidden');
        }
        if (this.given_context.report_type === 'bom_cost') {
            this.$('.o_mrp_prod_cost').toggleClass('o_hidden');
        }
    },
    _removeLines: function ($el) {
        var self = this;
        var activeID = $el.data('id');
        _.each(this.$('tr[parent_id='+ activeID +']'), function (parent) {
            var $parent = self.$(parent);
            var $el = self.$('tr[parent_id='+ $parent.data('id') +']');
            if ($el.length) {
                self._removeLines($parent);
            }
            $parent.remove();
        });
    },
});

core.action_registry.add('mrp_mfq_report',  MaterialsForwardQuery);
return  MaterialsForwardQuery;

});