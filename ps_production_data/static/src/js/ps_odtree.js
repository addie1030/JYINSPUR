odoo.define('ps_odtree', function (require) {
    "use strict";


    var core = require('web.core');
    var ajax = require('web.ajax');
    var FormController = require('web.FormController');
    var FormRenderer = require('web.FormRenderer');
    var qweb = core.qweb;

    var node_id_selected = 0;
    var treejson = [];
    var treeObj;
    var last_view_type;
    var controller;


    var buildTree = function (renderer) {
        var categ_model=renderer.arch.attrs.categ_model;
        var categ_property=renderer.arch.attrs.categ_property;
        var categ_parent_key=renderer.arch.attrs.categ_parent_key;
        var setting = {
            data: {
                simpleData: {
                    enable: true
                }
            },
            callback: {
                onClick: function (event, treeId, treeNode, clickFlag) {
                    node_id_selected = treeNode.id;
                    if(treeNode.child_id[0] != renderer.state.data.id){
                        renderer._rpc({
                            model: 'mrp.bom',
                            method: 'search_view_id',
                            args: [node_id_selected, treeNode.version, treeNode.child_id[0]]
                        }).then(function(res){
                            if(res){
                                renderer.do_action({
                                    type: 'ir.actions.act_window',
                                    view_mode: 'form',
                                    res_model: 'mrp.bom',
                                    target: 'new',
                                    res_id: res[1],
                                    views: [[res[0], 'form']],
                                },
                                {
                                    on_close: function () {
                                        renderer._renderView();
                                    }
                                })
                            }
                        })
                    }
                }
            }
        };
        var fields = ['id', 'version', 'child_id', 'name'];
        if (categ_parent_key != null) {
            fields.push(categ_parent_key);
        }
        var ctx =renderer.state.getContext();
        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
            model: categ_model,
            method: 'search_read',
            args: [],
            kwargs: {
                domain: [],
                fields: fields,
                order: 'id asc',
                context: ctx
            }
        }).then(function (respdata) {
            if (respdata.length > 0) {
                var treejson_cur = [];
                for (var index = 0; index < respdata.length; index++) {
                    var obj = respdata[index];
                    var parent_id = 0;
                    if (obj.hasOwnProperty(categ_parent_key)) {
                        parent_id = obj[categ_parent_key];
                        if (parent_id !== null || parent_id !== undefined || parent_id !== false) {
                            parent_id = parent_id[0];
                        }
                    }
                    treejson_cur.push({id: obj['id'], pId: parent_id, name: obj['name'], version: obj['version'], child_id: obj['child_id'], open: false});
                }
                renderer._rpc({
                    model: 'ps.bom.tree',
                    method: 'tree_parent',
                    args:[renderer.state.data.id]
                }).then(function(res){
                    var arr = [];
                    var arr1 = [];
                    for(var i=0; i<treejson_cur.length; i++){
                        if(treejson_cur[i].child_id[0] == renderer.state.data.id){
                            treejson_cur[i].pId = false;
                            arr1.push(treejson_cur[i]);
                        }
                        for(var j=0; j<res.length; j++){
                            if(treejson_cur[i].id == res[j].id){
                                treejson_cur[i].pId = res[j].pId;
                                arr.push(treejson_cur[i]);
                            }
                        }
                    }
                    arr.push(arr1[0]);
                    if (renderer.getParent().$('.o_list_view_categ').length === 0
                         || last_view_type !== renderer.viewType
                         || (JSON.stringify(treejson) !== JSON.stringify(arr))) {
                        last_view_type =renderer.viewType;
                        renderer.getParent().$('.o_list_view_categ').remove();
                        renderer.getParent().$('.o_kanban_view').addClass(' col-xs-12 col-md-10');
                        treejson=arr;
                        var fragment = document.createDocumentFragment();
                        var content = qweb.render('Odtree');
                        $(content).appendTo(fragment);
                        renderer.getParent().$el.prepend(fragment);
                        treeObj = $.fn.zTree.init(renderer.getParent().$('.ztree'), setting, treejson);
                        renderer.getParent().$(".handle_menu_arrow").on('click', function (e) {
                           if ( renderer.getParent().$('.handle_menu_arrow').hasClass("handle_menu_arrow_left")){
                                renderer.getParent().$('.handle_menu_arrow').removeClass("handle_menu_arrow_left");
                                renderer.getParent().$('.handle_menu_arrow').addClass("handle_menu_arrow_right");
                                renderer.getParent().$('.ztree').css("display","none");
                                renderer.getParent().$('.o_list_view_categ').removeClass('col-xs-12 col-md-2');
                                renderer.getParent().$('.o_list_view_categ').addClass('o_list_view_categ_hidden');
                                renderer.getParent().$('.o_kanban_view').removeClass(' col-xs-12 col-md-10');
                           }else{
                                renderer.getParent().$('.handle_menu_arrow').removeClass("handle_menu_arrow_right");
                                renderer.getParent().$('.handle_menu_arrow').addClass("handle_menu_arrow_left");
                                renderer.getParent().$('.ztree').css("display","block");
                                renderer.getParent().$('.o_list_view_categ').removeClass('o_list_view_categ_hidden');
                                renderer.getParent().$('.o_list_view_categ').addClass('col-xs-12 col-md-2');
                                renderer.getParent().$('.o_kanban_view').addClass(' col-xs-12 col-md-10');
                           }
                        });
                    }
                    if (node_id_selected != null && node_id_selected > 0) {
                        var node = treeObj.getNodeByParam('id', node_id_selected, null);
                        treeObj.selectNode(node);
                    }
                })
            }
        });

    };

    FormController.include({
        renderPager: function ($node, options) {
            controller=this;
            this._super($node, options);
        },
    });

 //
    FormRenderer.include({

        _renderView: function () {
            var self=this;

            var result = this._super.apply(this, arguments);
            if (self.arch.attrs.categ_property && self.arch.attrs.categ_model){
                self._rpc({
                    model: 'ps.bom.tree',
                    method: 'table_create',
                }).then(function(){
                    self.getParent().$('.o_form_sheet').addClass("o_list_view_width_withcateg");
                    self.getParent().$('.o_form_sheet').css("width",'auto');
                    self.getParent().$('.o_form_sheet').css("overflow-x", "auto");
                    buildTree(self);
                })
            }else {
                self.getParent().$('.o_list_view_categ').remove();
            }
            return result;
        }
    });

});
