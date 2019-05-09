odoo.define('account_china.loss_account',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var _t = core._t;

    var HomePage=AbstractAction.extend({
        template: 'LossAccountIndex',
        init: function(parent){
            this._super(parent);
            this.name="NameTest";
        },
        start: function(){
            var self=this;
            this._rpc({
                model: 'ps.account.period',
                method: 'get_all_period',
            })
            .then(function(result) {
                for(var i=0;i<result.length;i++){
                    var $option1=$("<option>").html(result[i].year).attr("state",result[i].state);
                    if(result[i].state==1){
                        $option1=$option1.attr("selected","selected");
                        for(var j=0;j<result[i].month.length;j++){
                            var $option2=$("<option>").html(result[i].month[j].displayname).attr("state",result[i].month[j].state).attr("value",result[i].month[j].value);
                            if(result[i].month[j].state==1){
                                $option2=$option2.attr("selected","selected");
                            }
                            $("#select2").append($option2)
                        }
                    }
                    $("#select1").append($option1)
                    $("#select1").change(function(){
                        $("#select2").empty();
                        for(var x=0;x<result.length;x++){
                            if($("#select1 option:selected").text()==result[x].year){
                                console.log(x)
                                console.log(result[x].month)
                                for(var j=0;j<result[x].month.length;j++){
                                    var $option2=$("<option>").html(result[x].month[j].displayname).attr("state",result[x].month[j].state).attr("value",result[x].month[j].value);
                                    if(result[x].month[j].state==1){
                                        $option2=$option2.attr("selected","selected");
                                    }
                                    $("#select2").append($option2)
                                }
                            }
                        }
                        $(".group_bottom").children("ul").empty();
                        $(".details").html(_t("Not checked yet"));
                        if($("#select2 option:selected").attr("state")==2){
                            $("#jc").css("display","none");
                            $("#yj").attr("disabled","disabled");
                            $("#fyj").removeAttr("disabled","disabled");
                        }else{
                            $("#jc").css("display","inline-block");
                            $("#fyj").attr("disabled","disabled");
                            $("#yj").attr("disabled","disabled");
                        }
                    })
                }
                $("#select2").change(function(){
                    // $("#select2").empty();
                    $(".group_bottom").children("ul").empty();
                    $(".details").html(_t("Not checked yet"));
                    if($("#select2 option:selected").attr("state")==2){
                        $("#jc").css("display","none");
                        $("#yj").attr("disabled","disabled");
                        $("#fyj").removeAttr("disabled","disabled");
                    }else{
                        $("#jc").css("display","inline-block");
                        $("#fyj").attr("disabled","disabled");
                        $("#yj").attr("disabled","disabled");
                    }
                })
            });
            this.$el[0].children[1].children[0].children[1].children[0].onclick=function(){
                self._rpc({
                    model:"res.config.settings",
                    method:"get_view_id",
                }).then(function(result){
                    var view_id=result;
                    self.do_action({
                        type: "ir.actions.act_window",
                        name:_t("Profit and loss carry-over parameter setting"),
                        res_model: "res.config.settings",
                        views: [[view_id||false,'form']],
                        target: 'new',
                        view_type : 'form',
                        view_mode : 'form',
                    })
                })
            }
            this.$el[0].children[1].children[0].children[2].children[0].onclick=function(){
                self._rpc({
                    model: 'account.move',
                    method: 'create_profit_loss_move',
                    args: [self.$("#select2 option:selected").val()],
                }).then(function(result){
                    self.do_action(result)
                })
            }
        }
    });
    core.action_registry.add('loss.homepage', HomePage);
});