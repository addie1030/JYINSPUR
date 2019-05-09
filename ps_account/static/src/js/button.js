odoo.define('account_china.button', function (require){
    "use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var FormController = require('web.FormController');
    var QWeb = core.qweb;
    var _t = core._t;


    var ImportViewMixin = {
        /**
         * @override
         */
        init: function (viewInfo, params) {
            var importEnabled = 'import_enabled' in params ? params.import_enabled : true;
            // if true, the 'Import' button will be visible
            this.controllerParams.importEnabled = importEnabled;
        },
    };
    var ImportControllerMixin = {
        /**
         * @override
         */
        init: function (parent, model, renderer, params) {
            this.importEnabled = params.importEnabled;
        },


        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Adds an event listener on the import button.
         *
         * @private
         */
        _bindImport: function () {
            if (!this.$buttons) {
                return;
            }


            var self = this;

            //凭证审核按钮
            this.$buttons.on('click', '.o_button_check', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        check_id.push(state.res_ids[i]);
                    }
                 }
                 var ctx = state.context;
//                 console.log(state.context);
                 ctx['active_ids'] = check_id;
/**
                $.ajax({
                        url: '/account/check',
                        data: JSON.stringify({ // 转换成JSON
                            "params":ctx
                        }),
                        dataType: 'json',
                        type: "POST",
                        async: false,
                        contentType: "application/json",
                        success: function (data) {
                            alert("保存成功！");
                            window.location.reload();
                        },
                        error: function (jqXHR, textStatus, errorThrown) {
                            alert('保存失败！');
                        }
                    });
*/

                if(check_id.length>0){
                    self._rpc({
                        model:"ps.check.post.account.move",
                        method:"get_check_view_id",
                    }).then(function(result){
                        var view_id=result;
                        self.do_action(
                        {
                            type: "ir.actions.act_window",
                            name: _t("凭证审核"),
                            res_model: "ps.check.post.account.move",
                            views: [[view_id || false,'form']],
                            target: 'new',
                            view_type : 'form',
                            view_mode : 'form',
                            context: ctx,
                            flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                        },
                         {    on_reverse_breadcrumb: function () {
                                        self.reload();
                                    },
                              on_close: function () {
                                        self.reload();
                                    }
                                }
                         );
                    })

                }else{
                    $(function() {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要审核的记录");
                        $div=$div.append($p);
                        $div.dialog({
                          modal: true,
                          buttons: {
                            确定: function() {
                              $( this ).dialog( "close" );
                            }
                          }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});

                    });

                }


            });

            //凭证记账按钮
            this.$buttons.on('click', '.o_button_post', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        check_id.push(state.res_ids[i]);
                    }
                 }
                 var ctx = state.context;
                 ctx['active_ids'] = check_id;

                 if(check_id.length > 0){
                        self.do_action(
                            {
                                type: "ir.actions.act_window",
                                name: _t("凭证记账"),
                                res_model: "ps.post.account.move",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context: ctx,
                                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                            }
                            ,
                             {    on_reverse_breadcrumb: function () {
                                            self.reload();
                                        },
                                  on_close: function () {
                                            self.reload();
                                        }
                             }
                         );
                 }else{
                    $(function() {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要记账的记录");
                        $div=$div.append($p);
                        $div.dialog({
                          modal: true,
                          buttons: {
                            确定: function() {
                              $( this ).dialog( "close" );
                            }
                          }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});

                    });
                 }


            });


            //**************取消审核********
            this.$buttons.on('click', '.o_button_uncheck', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        check_id.push(state.res_ids[i]);
                    }
                 }
                 var ctx = state.context;
                 ctx['active_ids'] = check_id;

                 if(check_id.length > 0){
                        self.do_action(
                            {
                                type: "ir.actions.act_window",
                                name: _t("取消审核"),
                                res_model: "ps.uncheck.account.move",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context: ctx,
                                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                            }
                            ,
                             {    on_reverse_breadcrumb: function () {
                                            self.reload();
                                        },
                                  on_close: function () {
                                            self.reload();
                                        }
                             }
                         );
                 }else{
                    $(function() {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要取消审核的记录");
                        $div=$div.append($p);
                        $div.dialog({
                          modal: true,
                          buttons: {
                            确定: function() {
                              $( this ).dialog( "close" );
                            }
                          }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});

                    });
                 }
            });
            //**************End取消审核*****

            //**************取消记账********
            this.$buttons.on('click', '.o_button_unpost', function () {
                 var state = self.model.get(self.handle, {raw: true});
                 var check_id=[];
                 for(var i=0;i<$('tbody .o_list_record_selector input').length;i++){
                    if($('tbody .o_list_record_selector input')[i].checked===true){
                        check_id.push(state.res_ids[i]);
                    }
                 }
                 var ctx = state.context;
                 ctx['active_ids'] = check_id;

                 if(check_id.length > 0){
                        self.do_action(
                            {
                                type: "ir.actions.act_window",
                                name: _t("取消记账"),
                                res_model: "ps.unpost.account.move",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context: ctx,
                                flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                            }
                            ,
                             {    on_reverse_breadcrumb: function () {
                                            self.reload();
                                        },
                                  on_close: function () {
                                            self.reload();
                                        }
                             }
                         );
                 }else{
                    $(function() {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要取消记账的记录");
                        $div=$div.append($p);
                        $div.dialog({
                          modal: true,
                          buttons: {
                            确定: function() {
                              $( this ).dialog( "close" );
                            }
                          }
                        });
                        $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});

                    });
                 }
            });
            //**************End取消记账*****


            //**************calculator*****
            var flag = 0;
            this.$buttons.on('click', '.o_button_calculator', function () {

                var oBody = document.getElementsByTagName('body')[0];
                var oCalculator = document.createElement('div');
                oCalculator.style.width = '265px';
                oCalculator.style.border = '2px solid darkseagreen';
                oCalculator.id = 'iCalcluator';

                oCalculator.innerHTML =
                    "<div id='Msg'>" +
                        "<div id='last_msg'></div>" +
                        "<hr />" +
                        "<div id='Calculation'>0</div>" +
                        "<div id='Result'>=0</div>" +
                    "</div>" +
                    "<ul>" +
                        "<li>" +
                            "<button id='button_C'>C</button>" +
                            "<button id='button_delete'>←</button>" +
                            "<button id='button_square'>x²</button>" +
                            "<button id='button_multiplication'>*</button>" +
                        "</li>" +
                        "<li>" +
                            "<button id='button_7'>7</button>" +
                            "<button id='button_8'>8</button>" +
                            "<button id='button_9'>9</button>" +
                            "<button id='button_except'>/</button>" +
                        "</li>" +
                        "<li>" +
                            "<button id='button_4'>4</button>" +
                            "<button id='button_5'>5</button>" +
                            "<button id='button_6'>6</button>" +
                            "<button id='button_plus'>+</button>" +
                            "</li>" +
                        "<li>" +
                            "<button id='button_1'>1</button>" +
                            "<button id='button_2'>2</button>" +
                            "<button id='button_3'>3</button>" +
                            "<button id='button_reduce'>-</button>" +
                        "</li>" +
                        "<li>" +
                            "<button id='button_close'>关闭</button>" +
                            "<button id='button_0'>0</button>" +
                            "<button id='button_point'>.</button>" +
                            "<button id='button_equal'>=</button>" +
                        "</li>" +
                    "</ul>";

                if (flag == 1) {
                    var iCalculator = document.getElementById('iCalcluator');
                    oBody.removeChild(iCalculator);
                    flag = 0;
                    document.onkeydown=false;
                    return flag;
                }

                if (flag == 0) {
                    oBody.appendChild(oCalculator);
                    flag = 1;
                }

                var Div_last_msg = document.getElementById('last_msg');
                var Div_calculation = document.getElementById('Calculation');
                var Div_result = document.getElementById('Result');
                var Btn_c = document.getElementById('button_C');
                var Btn_delete = document.getElementById('button_delete');
                var Btn_square = document.getElementById('button_square');
                var Btn_multiplication = document.getElementById('button_multiplication');
                var Btn_7 = document.getElementById('button_7');
                var Btn_8 = document.getElementById('button_8');
                var Btn_9 = document.getElementById('button_9');
                var Btn_except = document.getElementById('button_except');
                var Btn_4 = document.getElementById('button_4');
                var Btn_5 = document.getElementById('button_5');
                var Btn_6 = document.getElementById('button_6');
                var Btn_plus = document.getElementById('button_plus');
                var Btn_1 = document.getElementById('button_1');
                var Btn_2 = document.getElementById('button_2');
                var Btn_3 = document.getElementById('button_3');
                var Btn_reduce = document.getElementById('button_reduce');
                var Btn_close = document.getElementById('button_close');
                var Btn_0 = document.getElementById('button_0');
                var Btn_point = document.getElementById('button_point');
                var Btn_equal = document.getElementById('button_equal');

                var last_next = 0; // 倒数第二个元素的值
                var last = 0; // 最后一个元素的值

                Btn_1.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_1.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_1.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_2.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_2.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_2.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_3.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_3.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_3.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_4.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_4.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_4.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_5.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_5.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_5.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_6.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_6.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_6.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_7.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_7.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_7.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_8.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_8.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_8.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_9.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (Div_calculation.innerHTML === '0' && last != '.') {
                        Div_calculation.innerHTML = Btn_9.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_9.innerText;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_0.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    last_next = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 2);
                    if (Div_calculation.innerHTML === '0' && last == 0) {
                        Div_calculation.innerHTML = 0;
                        return;
                    }
                    if (Div_calculation.innerHTML == 0 && last != '.') {
                        Div_calculation.innerHTML += Btn_0.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_0.innerText;
                        if (last == 0 && isNaN(last_next) && last_next != '.'){
                            Div_calculation.innerHTML = Div_calculation.innerHTML.substring(0, Div_calculation.innerHTML.length - 1);
                        }
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }
                Btn_point.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (last == '.') {
                        return;
                    }
                    for (var i=Div_calculation.innerHTML.length - 1;i>=0;i--) {
                        if (isNaN(Div_calculation.innerHTML.charAt(i)) && Div_calculation.innerHTML.charAt(i) != '.') {
                            break;
                        }
                        if (Div_calculation.innerHTML.charAt(i) == '.') {
                            return;
                        }
                    }
                    if (Div_calculation.innerHTML == 0 && Div_calculation.innerHTML.length == 1) {
                        Div_calculation.innerHTML += Btn_point.innerText;
                    } else {
                        Div_calculation.innerHTML += Btn_point.innerText;
                        Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                    }
                }

                Btn_c.onclick = function() {
                    Div_calculation.innerHTML = 0;
                    Div_result.innerHTML = "=" + 0;
                    Div_last_msg.innerHTML = "";
                }
                Btn_plus.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (!isNaN(last)) {
                        Div_calculation.innerHTML += Btn_plus.innerText;
                    }
                }
                Btn_reduce.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (!isNaN(last)) {
                        Div_calculation.innerHTML += Btn_reduce.innerText;
                    }
                }
                Btn_multiplication.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (!isNaN(last)) {
                        Div_calculation.innerHTML += Btn_multiplication.innerText;
                    }
                }
                Btn_except.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (!isNaN(last)) {
                        Div_calculation.innerHTML += Btn_except.innerText;
                    }
                }

                Btn_square.onclick = function() {
                    var str_num = "";
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (!isNaN(last)) {
                        for (var i=Div_calculation.innerHTML.length - 1;i>=0;i--){
                            if (isNaN(Div_calculation.innerHTML.charAt(i)) && Div_calculation.innerHTML.charAt(i) != '.') {
                                break;
                            }
                            str_num = Div_calculation.innerHTML.charAt(i) + str_num;
                        }
                        Div_calculation.innerHTML += "*" + str_num;
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                }

                Btn_delete.onclick = function() {
                    if (Div_calculation.innerHTML.length == 1) {
                        Div_calculation.innerHTML = 0;
                    } else {
                        last_next = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 2);

                        Div_calculation.innerHTML = Div_calculation.innerHTML.substring(0, Div_calculation.innerHTML.length - 1);
                        if (isNaN(last_next)) {
                            Div_calculation.innerHTML = Div_calculation.innerHTML.substring(0, Div_calculation.innerHTML.length - 1);
                        }
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                    if (isNaN(last_next)) {
                        Div_calculation.innerHTML += last_next;
                    }

                    last_next = 0;
                    return last_next;
                }

                Btn_equal.onclick = function() {
                    last = Div_calculation.innerHTML.charAt(Div_calculation.innerHTML.length - 1);
                    if (isNaN(last)) {
                        Div_calculation.innerHTML = Div_calculation.innerHTML.substring(0, Div_calculation.innerHTML.length - 1);
                    }
                    Div_result.innerHTML = "=" + eval(Div_calculation.innerHTML);
                    if (Div_calculation.innerHTML != Div_result.innerHTML.substring(1, Div_result.innerHTML.length)) {
                        Div_last_msg.innerHTML = Div_calculation.innerHTML + Div_result.innerHTML;
                    }
                    Div_calculation.innerHTML = eval(Div_calculation.innerHTML);
                    if (isNaN(last)) {
                        Div_calculation.innerHTML += last;
                    }

                    last = 0;
                    return last;
                }

                Btn_close.onclick = function() {
                    var iCalculator = document.getElementById('iCalcluator');
                    oBody.removeChild(iCalculator);
                    flag = 0;
                    document.onkeydown=false;
                    return flag;
                }

                // 键盘事件
                function keyDown(e) {
                    var keycode=e.which || event.keyCode;
                    var Btn_keyycode = keycode-48;
                    if (Btn_keyycode == 0 || Btn_keyycode == 48) {Btn_0.onclick();}
                    if (Btn_keyycode == 1 || Btn_keyycode == 49) {Btn_1.onclick();}
                    if (Btn_keyycode == 2 || Btn_keyycode == 50) {Btn_2.onclick();}
                    if (Btn_keyycode == 3 || Btn_keyycode == 51) {Btn_3.onclick();}
                    if (Btn_keyycode == 4 || Btn_keyycode == 52) {Btn_4.onclick();}
                    if (Btn_keyycode == 5 || Btn_keyycode == 53) {Btn_5.onclick();}
                    if (Btn_keyycode == 6 || Btn_keyycode == 54) {Btn_6.onclick();}
                    if (Btn_keyycode == 7 || Btn_keyycode == 55) {Btn_7.onclick();}
                    if (Btn_keyycode == 8 || Btn_keyycode == 56) {Btn_8.onclick();}
                    if (Btn_keyycode == 9 || Btn_keyycode == 57) {Btn_9.onclick();}
                    if (Btn_keyycode == 62) {Btn_point.onclick();}
                    if (Btn_keyycode == -40 || Btn_keyycode == -2) {Btn_delete.onclick();} // <--
                    if (Btn_keyycode == 59) {Btn_plus.onclick();} // +
                    if (Btn_keyycode == 61 || Btn_keyycode == 125) {Btn_reduce.onclick();} // -
                    if (Btn_keyycode == 58) {Btn_multiplication.onclick();} // *
                    if (Btn_keyycode == 63) {Btn_except.onclick();} // /
                    if (Btn_keyycode == 13) {Btn_equal.onclick();} // =
                    if (Btn_keyycode == -21) {Btn_close.onclick();} // close
                }

                document.onkeydown=keyDown;

                // 下弹效果
                function down(){
                    var iCalculator = document.getElementById('iCalcluator');
                    var Ctop = parseInt(iCalculator.offsetTop);
                    var alpha = 0;
                    var speed = 1;
                    var t=setInterval(rollTop,speed);
                    //向左移动
                    function rollTop(){
                        Ctop += 0.5;
                        iCalculator.style.top = Ctop+'px';
                        if(Ctop >= 120 ) {
                            alpha += 5;
                            iCalculator.style.filter = 'alpha(opacity=' + alpha + ')';
                            iCalculator.style.opacity = alpha / 100;
                        }
                        if(Ctop == 130 ) {
                            clearInterval(t);
                        }
                    }
                }
                down();

                return flag
            });

            //************End calculator*****
        }
    };


    ListView.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportViewMixin.init.apply(this, arguments);
        },
    });

    ListController.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin.init.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);
            // this.init.call(this);
            if(this.modelName=="ps.account.move.check"){
                this.$buttons.find(".o_button_check").css("display","inline-block");
                this.$buttons.find(".o_button_uncheck").css("display","inline-block");
                this.$buttons.find(".o_list_button_add").css("display","none");
                this.$buttons.find(".o_button_import").css("display","none");
            }
            if(this.modelName=="ps.account.move.post"){
                this.$buttons.find(".o_button_post").css("display","inline-block");
                this.$buttons.find(".o_button_unpost").css("display","inline-block");
                this.$buttons.find(".o_list_button_add").css("display","none");
                this.$buttons.find(".o_button_import").css("display","none");
            }
            if(this.modelName=="account.account"){
                this.$buttons.find(".o_button_import").css("display","none");
            }
        }
    });

    FormView.include({
        init: function (viewInfo) {
            this._super.apply(this, arguments);
            this.controllerParams.viewID = viewInfo.view_id;
            ImportViewMixin.init.apply(this, arguments);
        },
    });

    FormController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.viewID = params.viewID;
            ImportControllerMixin.init.apply(this, arguments);
        },

        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);
            if (this.modelName == "ps.adjustment.exchange.rate") {
                this.$buttons.find(".o_form_button_save").css("display", "none");
                this.$buttons.find(".o_form_button_cancel").css("display", "none");
            }
            if(this.modelName=="account.move"){
                this.$buttons.find(".o_button_calculator").css("display","inline-block");
            }
        }
    });
}


);