odoo.define('ps_pos_hw_point_of_sale.screens', function (require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var PosOrderWidget = screens.OrderWidget;
    var PosClientListScreenWidget = screens.ClientListScreenWidget;
    var _super_posmodel = models.PosModel.prototype;
    var electron = nodeRequire('electron');
    var ActionManager = require('web.ActionManager');
    var gui = require('point_of_sale.gui');
    var rpc = require('web.rpc');

    PosOrderWidget.include({
        change_selected_order: function() {
            var self = this;
            self._super();
            if (self.pos.ipcRenderer != null && !self.pos.rfid_read_start){
                self.pos.rfid_read_start = true;
                self.pos.ipcRenderer.sendSync('rfid:read');
            }
        },
    });
    ActionManager.include({
        do_action: function (action, options) {
            var self = this;
            if (action && action.constructor == Object && action.type == 'ir.actions.exec_js') {
                self.dialog_stop();
                return $.when(eval(action.exec)).then(function(){
                });
            }
            return self._super(action, options);
        },
    });
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var self = this;
            _super_posmodel.initialize.call(self, session, attributes);
            self.rfid_read_start = true;
            self.ipcRenderer = null;

            // 用来输出日志
            self.logger = null;
            try {
                var remote = null;
                try {
                    remote = electron.remote;
                } catch (e) {
                    remote = nodeRequire('remote');
                }
                var log4js = remote.nodeRequire("log4js");
                if(log4js != null) {
                    self.logger = log4js.getLogger('rfid_log_file');
                }
            }catch(err){

            }
            try{
                self.ipcRenderer = electron.ipcRenderer;
                self.ipcRenderer.on('rfid:read', function(event, ret){
                    var result = ret.result;
                    var context = ret.context;

                    var def = new $.Deferred();
                    if (context.sync == true){// 本函数只处理异步
                        def.reject();
                        return def;
                    }

                    if (!self.rfid_read_start){
                        def.reject();
                        return def;
                    }
                    if (result == null) {
                        setTimeout(function(){self.ipcRenderer.sendSync('rfid:read');},50);
                        def.reject();
                        return def;
                    }

                    self.rfid_read_start = false;

                    rpc.query({
                        model: 'res.partner',
                        method: 'search_member',
                        args: [result.blockStr],
                    }).then(function(res){
                        if(typeof res !== 'undefined'){
                            self.db.add_partners(self.partners);
                            var partner = self.db.get_partner_by_id(res);
                            self.get('selectedOrder').set_client(partner);
                            if(self.changed.selectedClient){
                               self.get('selectedOrder').set_pricelist(_.findWhere(self.pricelists, {'id': self.changed.selectedClient.property_product_pricelist[0]}) || self.default_pricelist);
                            }
                            self.chrome.widget.username.renderElement();
                            def.resolve();
                        }
                        else{
                            //setTimeout(function(){self.ipcRenderer.sendSync('rfid:read');},50);
                            def.reject([]);
                        }
                    })
                    return def;

                });

                self.ipcRenderer.on('rfid:write', function(event, ret){
                    var result = ret.result;
                    var context = ret.context;

                    var def = new $.Deferred();
                    if (context.sync == true){// 本函数只处理异步
                        def.reject();
                        return def;
                    }

                    if (result == null) {
                        def.reject();
                        return self.gui.show_popup('error',{
                            'body': _t('Write failed！'),//写卡失败
                        });
                    }
                    rpc.query({
                        model: 'ps.member.card',
                        method: 'write_card_info_ex',
                        args: [result.pSnr,result.blockStr,'normal',context.partner_id],
                    }).then(function(res){
                        if(res[0]){
                            var partner = self.db.get_partner_by_id(res[1]);
                            partner.ps_member_no = res[2];
                            // self.db.add_partners(self.partners);
                            return self.gui.show_popup('confirm',{
                                'body': _t('Successful card writing！'),//写卡成功
                                confirm: function(){
                                    // self.gui.current_screen.partner_cache.cache[res[1]].addClass('highlight');
                                    // self.gui.current_screen.show();
                                    self.gui.current_screen.display_client_details('show', partner)
                                },
                            });
                        }else{
                            return self.gui.show_popup('error',{
                               'body': _t('The membership card failed to write! Please try again'),//会员卡写卡失败！请重试
                            });
                        }
                    })
                    return def;
                });

            } catch (e) {
                console.log(e);
            }
        },

        rfid_read: function (args) {
            var self = this;
            if (self.ipcRenderer == null){
                return;
            }
            var readResult = self.ipcRenderer.sendSync('rfid:read', {context:{sync:true}});
            if (readResult.result == null){
                return self.gui.show_popup('error',{
                    'body': _t('Card reading failed！'),//读卡失败
                });
            }
            self.do_action({
                type: "ir.actions.act_window",
                name:_t("Membership card information"),
                res_model: "ps.member.card.read.wizard",
                views: [[false,'form']],
                target: 'new',
                view_type : 'form',
                view_mode : 'form',
            })
        },

        rfid_write: function (args) {
            var self = this;
            if (self.ipcRenderer == null){
                return;
            }
            var readResult = self.ipcRenderer.sendSync('rfid:read', {context:{sync:true}});
            if (readResult.result == null){
                return self.gui.show_popup('error',{
                    'body': _t('Card reading failed！'),//读卡失败
                });
            }
            rpc.query({
                model: 'res.partner',
                method: 'write_card_info',
                args: [args.context.partner_id],
            }).then(function (res) {
                if (!res){
                    return self.gui.show_popup('confirm', {
                        'title': _t('warning'),//警告
                        'body': _t('This card has been bound to the membership. Do you want to continue? (Continue to rewrite this card)'),//此卡已绑定会员，是否继续？(继续将重写此卡)
                        confirm: function () {
                            args.context.sync = false;
                            self.ipcRenderer.sendSync('rfid:write', args);
                        }
                    });
                }
                else{
                    args.context.sync = false;
                    self.ipcRenderer.sendSync('rfid:write', args);
                }
            });

        },

        load_server_data: function () {
            var self = this;
            return _super_posmodel.load_server_data.apply(self, arguments).then(function () {
                if (self.ipcRenderer != null){
                    self.ipcRenderer.sendSync('rfid:read');
                }
            });
        },

    });
    PosClientListScreenWidget.include({
        show: function () {
            var self = this;
            if (self.pos.ipcRenderer == null){
                return this._super();
            }
            self.pos.rfid_read_start = false;
            self._super();
        },
        close:function(){
            var self = this;
            if (self.pos.ipcRenderer == null){
                return this._super();
            }
            self.pos.rfid_read_start = true;
            setTimeout(function(){self.pos.ipcRenderer.sendSync('rfid:read');},50);
            self._super();
        },
        display_client_details: function (visibility, partner, clickpos) {
            var self = this;
            self._super(visibility, partner, clickpos);
            if (visibility === 'show') {
                $("#rfid_card_manage").on("click", function(){
                    if(self.new_client){
                        var ps_id = self.new_client.id;
                    }else{
                        var ps_id = self.old_client.id;
                    }
                    self.do_action({
                        type: "ir.actions.act_window",
                        name:_t("Membership card management"),
                        res_model: "ps.member.card.manage.wizard",
                        views: [[false,'form']],
                        target: 'new',
                        view_type : 'form',
                        view_mode : 'form',
                        context: {
                            'active_id': ps_id,
                            'active_ids': [ps_id],
                            'active_model': 'res.partner',
                            'partner_id': ps_id,
                            'company_id': self.pos.company.id
                        }
                    })
                });
            } else{
                $("#rfid_card_manage").off("click");
            }
        },

    });
});

