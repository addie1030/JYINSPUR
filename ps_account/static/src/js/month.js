odoo.define('account_china.month',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var _t = core._t;

    var HomePage=AbstractAction.extend({
        template: 'MonthIndex',
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
            this.$el[0].children[0].children[0].children[3].onclick=function(){
                $(".group_bottom").children("ul").empty();
                self._rpc({
                    model: 'account.move',
                    method: 'ps_period_end_check',
                    args: [self.$("#select2 option:selected").val()],
                })
                .then(function(result) {
                    console.log(result)
                    if(result[0]==true){
                        $("#yj").removeAttr("disabled","disabled");
                    }
                    //资产科目类
                    var a=$("#first_bottom").children("ul");
                    var x=0;
                    var y=0;
                    for(var i=0;i<result[1][2].content.length;i++){
                        var $li=$("<li>", {class: 'row'})
                        $li=$li.append($("<a>").html(result[1][2].content[i].content)).append($("<span>", {class: 'col-4'}).html(result[1][2].content[i].name))
                        if(result[1][2].content[i].status==0){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-check-circle'}).css("color","#76f06d"))
                        }else if(result[1][2].content[i].status==1){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-info-circle'}).css("color","#e6e30b"))
                            x=x+1;
                        }else if(result[1][2].content[i].status==2){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-times-circle'}).css("color","#e51730"))
                            y=y+1;
                        }
                        var num=x+y;
                        a=a.append($li)
                        $("#first_top").children(".details").html(_t("Total")+result[1][2].content.length+_t("item category, where")+num+_t("item category is risky"));
                    }
                    //期末结转
                    var b=$("#second_bottom").children("ul");
                    var m=0;
                    var n=0;
                    for(var i=0;i<result[1][1].content.length;i++){
                        var $li=$("<li>", {class: 'row'})
                        $li=$li.append($("<a>").html(result[1][1].content[i].content)).append($("<span>", {class: 'col-4'}).html(result[1][1].content[i].name))
                        if(result[1][1].content[i].status==0){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-check-circle'}).css("color","#76f06d"))
                        }else if(result[1][1].content[i].status==1){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-info-circle'}).css("color","#e6e30b"))
                            m=m+1;
                        }else if(result[1][1].content[i].status==2){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-times-circle'}).css("color","#e51730"))
                            n=n+1;
                        }
                        var num=m+n;
                        b=b.append($li)
                        $("#second_top").children(".details").html(_t("Total")+result[1][1].content.length+_t("item category, where")+num+_t("item category is risky"));
                    }

                    //--------------------------------------------------------------------
                    // var b=$("#second_bottom").children("ul");
                    // var m=0;
                    // var n=0;
                    // var $li=$("<li>",{class: 'row'})
                    // if(result[1][1].content.content==_t("Unfollowed")){
                    //     $li=$li.append($("<a>",{class: 'loss_url'}).html(result[1][1].content.content)).append($("<span>",{class: 'col-4'}).html(result[1][1].content.name))
                    // }else{
                    //     $li=$li.append($("<a>").html(result[1][1].content.content)).append($("<span>",{class: 'col-4'}).html(result[1][1].content.name))
                    // }
                    // if(result[1][1].content.status==0){
                    //     $li=$li.append($("<i>",{class: 'fa fa-lg fa-check-circle'}).css("color","#76f06d"))
                    // }else if(result[1][1].content.status==1){
                    //     $li=$li.append($("<i>",{class: 'fa fa-lg fa-info-circle'}).css("color","#e6e30b"))
                    //     m=m+1
                    // }else if(result[1][1].content.status==2){
                    //     $li=$li.append($("<i>",{class: 'fa fa-lg fa-times-circle'}).css("color","#e51730"))
                    //     n=n+1
                    // }
                    // var l=m+n;
                    // b=b.append($li)
                    // $("#second_top").children(".details").html(_t("There are 1 category, of which")+l+_t("item category is risky"));
                    // var loss_name=self.$el[0].children[1].children[3].children[0].children[0].children[0].getAttribute("class");
                    // if(loss_name=="loss_url"){
                    //     self.$el[0].children[1].children[3].children[0].children[0].children[0].onclick=function(){
                    //         self.do_action({
                    //             type: "ir.actions.client",
                    //             name:_t("Profit and loss carryover"),
                    //             tag: "loss.homepage",
                    //             target: 'current',
                    //         })
                    //         $(".group_bottom").slideUp();
                    //         $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                    //     }
                    // }
                    //------------------------------------------------------------------

                    //凭证状态
                    var c=$("#third_bottom").children("ul");
                    var x=0;
                    var y=0;
                    for(var i=0;i<result[1][0].content.length;i++){
                        var $li=$("<li>",{class: 'row'})
                        if(result[1][0].content[i].status==0){
                            $li=$li.append($("<a>").html(result[1][0].content[i].content)).append($("<span>",{class: 'col-4'}).html(result[1][0].content[i].name))
                        }else{
                            if(result[1][0].content[i].name==_t("Pending certificate")){
                                $li=$li.append($("<a>",{class: 'check_url'}).html(result[1][0].content[i].content)).append($("<span>",{class: 'col-4'}).html(result[1][0].content[i].name))
                                // console.log(self.$el)
                            }
                            if(result[1][0].content[i].name==_t("Pending voucher")){
                                $li=$li.append($("<a>",{class: 'post_url'}).html(result[1][0].content[i].content)).append($("<span>",{class: 'col-4'}).html(result[1][0].content[i].name))
                            }
                        }
                        if(result[1][0].content[i].status==0){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-check-circle'}).css("color","#76f06d"))
                        }else if(result[1][0].content[i].status==1){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-info-circle'}).css("color","#e6e30b"))
                            x=x+1
                        }else if(result[1][0].content[i].status==2){
                            $li=$li.append($("<i>",{class: 'fa fa-lg fa-times-circle'}).css("color","#e51730"))
                            y=y+1
                        }
                        var num=x+y;
                        c=c.append($li)
                        $("#third_top").children(".details").html(_t("Total")+result[1][0].content.length+_t("item category, where")+num+_t("item category is risky"));
                    }
                    var check_name=self.$el[0].children[1].children[5].children[0].children[0].children[0].getAttribute("class");
                    var post_name=self.$el[0].children[1].children[5].children[0].children[1].children[0].getAttribute("class");
                    if(check_name=="check_url"){
                        self.$el[0].children[1].children[5].children[0].children[0].children[0].onclick=function(){
                            self.do_action({
                                type: "ir.actions.act_window",
                                name:_t("Certificate review"),
                                res_model: "ps.account.move.check",
                                views: [[false,'list']],
                                target: 'current',
                                view_type : 'form',
                                view_mode : 'tree',
                            })
                            $(".group_bottom").slideUp();
                            $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                        }
                    }
                    if(post_name=="post_url"){
                        self.$el[0].children[1].children[5].children[0].children[1].children[0].onclick=function(){
                            self.do_action({
                                type: "ir.actions.act_window",
                                name:_t("Certificate accounting"),
                                res_model: "ps.account.move.post",
                                views: [[false,'list']],
                                target: 'current',
                                view_type : 'form',
                                view_mode : 'tree',
                            })
                            $(".group_bottom").slideUp();
                            $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                        }
                    }
                    //其他异常,凭证断号
                    console.log(result)
                    var d=$("#forth_bottom").children("ul");
                    var h=0;
                    var $li=$("<li>",{class: 'row'})
                    if(result[1][3].content.content==_t("Broken Number Exists")){
                        $li=$li.append($("<a>",{class: 'dh_url'}).html(result[1][3].content.content)).append($("<span>",{class: 'col-4'}).html(result[1][3].content.name))
                    }else{
                        $li=$li.append($("<a>").html(result[1][3].content.content)).append($("<span>",{class: 'col-4'}).html(result[1][3].content.name))
                    }
                    if(result[1][3].content.status==0){
                        $li=$li.append($("<i>",{class: 'fa fa-lg fa-check-circle'}).css("color","#76f06d"))
                    }else if(result[1][3].content.status==2){
                        $li=$li.append($("<i>",{class: 'fa fa-lg fa-times-circle'}).css("color","#e51730"))
                        h=h+1
                    }
                    var num=h;
                    d=d.append($li)
                    $("#forth_top").children(".details").html(_t("There are 1 category, of which")+num+_t("item category is risky"));
                    var dh_name=self.$el[0].children[1].children[7].children[0].children[0].children[0].getAttribute("class");
                    if(dh_name=="dh_url"){
                        self.$el[0].children[1].children[7].children[0].children[0].children[0].onclick=function(){
                            self.do_action({
                                 type: "ir.actions.act_window",
                                name:_t("Certificate break number"),
                                res_model: "ps.account.move.no.process",
                                views: [[false,'form']],
                                target: 'current',
                                view_type : 'form',
                                view_mode : 'form',
                            })
                            $(".group_bottom").slideUp();
                            $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                        }
                    }

                    $(".group_bottom").slideDown();
                    $(".symbol").attr("src","/ps_account/static/src/img/jx.png")
                });
            }
            this.$el[0].children[0].children[0].children[4].onclick=function(){
                self._rpc({
                    model: 'account.move',
                    method: 'ps_period_end_handle',
                    args: [self.$("#select2 option:selected").val()],
                }).then (function(result){
                    if(result==true){
                        $(".o_menu_sections").children()[0].children[0].click()
                        $(".group_bottom").slideUp();
                        $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                    }
                })
            }
            this.$el[0].children[0].children[0].children[5].onclick=function(){
                self._rpc({
                    model: 'account.move',
                    method: 'ps_period_end_cancel_handle',
                    args: [self.$("#select2 option:selected").val()],
                }).then (function(result){
                    if(result==true){
                        $(".o_menu_sections").children()[0].children[0].click()
                        $(".group_bottom").slideUp();
                        $(".symbol").attr("src","/ps_account/static/src/img/jr.png")
                    }
                })
            }
        }
    });
    core.action_registry.add('month.homepage', HomePage);
});