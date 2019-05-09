odoo.define('tree_menu.tree_view_button', function(require)
{
    "use strict";
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require('web.ListController');
    var FormView = require('web.FormView');
    var FormController = require('web.FormController');
    var QWeb = core.qweb;

    var ImportViewMixin = {
        init: function (viewInfo, params) {
            var importEnabled = 'import_enabled' in params ? params.import_enabled : true;
            this.controllerParams.importEnabled = importEnabled;
        },
    };

    var ImportControllerMixin = {
        init: function (parent, model, renderer, params)
        {
            this.importEnabled = params.importEnabled;
        },

        _bindImport: function ()
        {
            if (!this.$buttons)
            {
                return;
            }
            var self = this;
            this.$buttons.on('click', '.o_form_button_fcreateparams', function ()
            {
                var state = self.model.get(self.handle, {raw: true});
                var formulaid = state.data.id;
                var sql = state.data.formula_design;
                var params = [];
                var param = {};
                if (typeof(formulaid) == "undefined")
                {
                    alert("需要首先保存自定义公式后再生成公式参数。");
                    return;
                }
                if (sql.length <= 0)
                {
                    alert("公式模型的值为空，请检查。");
                    return;
                }
                var args = [formulaid,sql]
                var deffiscal = self._rpc({
                    model: 'ps.statement.formulas',
                    method: 'create_params',
                    args: args
                }).then(function (result) {
                    if (result)
                    {
                        // $(".table-responsive").find("thead").find("tr").children("th:last-child").css("display","none");
                        // $(".table-responsive").find("tbody").find(".aaa").css("display","none");
                        var $first=$(".table-responsive").find("tbody").find(".aaa");
                        for(var i=0;i<result.length;i++)
                        {
                            var $tr=$("<tr>");
                            for(var j=0;j<8;j++)
                            {
                                var $td=$("<td>");
                                if(j==0)
                                {
                                    $td.html(result[i].param_id);
                                }else if(j==1)
                                {
                                    $td.html(result[i].name);
                                }else if(j==2)
                                {
                                    $td.html(result[i].param_description);
                                }else if(j==3)
                                {
                                    $td.html(result[i].param_category);
                                }else if(j==4)
                                {
                                    $td.html(result[i].param_type);
                                }else {
                                    $td.html("");
                                }
                                $tr=$tr.append($td);
                            }
                            $tr.insertBefore($first);
                        }
                    }
                });
            });

            // if(this.modelName=="ps.statement.statements")
            // {
            //     var date = new Date();
            //     var month = date.getMonth() + 1;
            //     var self = this;
            //     if (month >= 1 && month <= 9) {
            //         month = "0" + month;
            //     }
            //     var currentdate = date.getFullYear() + month;
            //     alert(1);
            //     var deffiscal = self._rpc({
            //         model: 'ps.statement.statements',
            //         method: 'get_fiscalperiod'
            //     }).then(function (result) {
            //         if (result) {
            //             currentdate = result;
            //         }
            //     });
            // }

            //新建报表按钮
            var self = this;
            this.$buttons.on('click', '.o_list_tender_button_create', function ()
            {
                var date = new Date();
                var month = date.getMonth() + 1;

                if (month >= 1 && month <= 9) {
                    month = "0" + month;
                }
                var currentdate = date.getFullYear() + month;
                var deffiscal = self._rpc({
                    model: 'ps.statement.statements',
                    method: 'get_fiscalperiod'
                }).then(function (result) {
                    if (result)
                    {
                        currentdate = result;
                        $(function()
                        {
                            var $div=$("<div>",{id:"dialog-message",title:"新建报表"});
                            var $paa=$("<p class=\"validateTips\" style=\"color:red\" id=\"validateTips\">").html("所有的表单字段都是必填的。");
                            $div=$div.append($paa);
                            var $p=$("<p>").html("报表编号");
                            $div=$div.append($p);
                            $div=$div.append('<input type=\"text\" name=\"report_code\" id="report_code" /> ');
                            var $p1=$("<p>").html("报表名称");
                            $div=$div.append($p1);
                            $div=$div.append('<input type=\"text\" name=\"report_name\" id="report_name"/> ');
                            var $p2=$("<p>").html("编报时间");
                            $div=$div.append($p2);
                            $div=$div.append('<select style= "height:21px" name="category" id="category">\n' +
                                '\t\t\t<option value ="month" selected = "selected">月报表</option>\n' +
                                '\t\t</select>');
                            var $p3=$("<p>").html("标题行数");
                            $div=$div.append($p3);
                            $div=$div.append('<input type=\"text\" name=\"titlerows\" id="titlerows" value="3"/> ');
                            var $p4=$("<p>").html("表头行数");
                            $div=$div.append($p4);
                            $div=$div.append('<input type=\"text\" name=\"headrows\" id="headrows" value="1"/> ');
                            var $p5=$("<p>").html("表体行数");
                            $div=$div.append($p5);
                            $div=$div.append('<input type=\"text\" name=\"bodyrows\" id="bodyrows" value="30"/> ');
                            var $p6=$("<p>").html("表尾行数");
                            $div=$div.append($p6);
                            $div=$div.append('<input type=\"text\" name=\"tailrows\" id="tailrows" value="2"/> ');
                            var $p7=$("<p>").html("表体列数");
                            $div=$div.append($p7);
                            $div=$div.append('<input type=\"text\" name=\"bodycols\" id="bodycols" value="10"/> ');

                            var report_code = $( "#report_code" );
                            var report_name = $( "#report_name" );
                            var allFields = $( [] ).add( report_code ).add( report_name );

                            function updateTips( t )
                            {
                                // tips
                                $(".validateTips").text( t ).addClass( "ui-state-highlight" );
                                setTimeout(function() {
                                    $(".validateTips").removeClass( "ui-state-highlight", 1500 );
                                }, 500 );
                            }

                            function checkLength( o, n, min, max )
                            {
                                if ( o.val().length > max || o.val().length < min )
                                {
                                    o.addClass( "ui-state-error" );
                                    updateTips( "" + n + " 的长度必须在 " +
                                      min + " 和 " + max + " 之间。" );
                                    return false;
                                } else {
                                    return true;
                                }
                            }

                            function checkRegexp( o, regexp, n )
                            {
                                if ( !( regexp.test( o.val() ) ) )
                                {
                                    o.addClass( "ui-state-error" );
                                    updateTips( n );
                                    return false;
                                } else {
                                    return true;
                                }
                            }

                            $div.dialog({
                                modal: true,
                                buttons: {
                                    确定: function() {
                                        allFields.removeClass( "ui-state-error" );
                                        var code = $("#report_code").val();
                                        var name = $("#report_name").val();
                                        var category = $('#category option:selected').val();//all或者month
                                        var titlerows = $("#titlerows").val();
                                        var headrows = $("#headrows").val();
                                        var bodyrows = $("#bodyrows").val();
                                        var tailrows = $("#tailrows").val();
                                        var bodycols = $("#bodycols").val();

                                        var bValid = true;
                                        var report_code = $( "#report_code" );
                                        var report_name = $( "#report_name" );
                                        bValid = bValid && checkLength( report_code, "报表编号", 3, 4 );
                                        bValid = bValid && checkLength( report_name, "报表名称", 0, 80 );

                                        bValid = bValid && checkRegexp( report_code, /^([0-9a-zA-Z])+$/, "报表编号只允许：字母和数字的组合" );
                                        bValid = bValid && checkRegexp( report_name, /^[a-zA-Z0-9\u4e00-\u9fa5]+$/, "报表名称只允许：汉字，字母和数字的组合" );

                                        if(bValid)
                                        {
                                            // allFields.val( "" ).removeClass( "ui-state-error" );
                                            $( "#report_code" ).removeClass( "ui-state-error" );
                                            $( "#report_name" ).removeClass( "ui-state-error" );
                                            $(".validateTips").text( "所有的表单字段都是必填的。" );

                                            self.do_action
                                            ({
                                                type: 'ir.actions.client',
                                                tag: 'statements',
                                                context : {
                                                    'isnew' : '1',
                                                    'report_code' : code,
                                                    'report_name' : name,
                                                    'report_date' : currentdate,
                                                    'category'  : category,
                                                    'titlerows' : titlerows,
                                                    'headrows' : headrows,
                                                    'bodyrows' : bodyrows,
                                                    'tailrows' : tailrows,
                                                    'bodycols' : bodycols,
                                                },
                                             },
                                             {   on_reverse_breadcrumb: function ()
                                                 {
                                                     self.reload();
                                                     },
                                                 on_close: function ()
                                                 {
                                                     self.reload();
                                                 }
                                             });
                                            $div.empty();
                                            $( this ).dialog( "close" );
                                        }
                                    },
                                    取消: function() {
                                        allFields.val( "" ).removeClass( "ui-state-error" );
                                        $( this ).dialog( "close" );
                                    },
                                }
                            });
                            $('.ui-dialog-buttonpane').find('button:contains("确定")').css({"color":"white","background-color":"#00a09d","border-color":"#00a09d"});
                        });
                    }
                    else {
                        alert('没有找到对应的会计期间，请首先到财务会计中维护会计期间！');
                            // self.do_action({
                            //     name: '财务报表',
                            //     type: 'ir.actions.act_window',
                            //     res_model: 'ps.statement.statements',
                            //     views: [[false, 'list']],
                            //     view_type: 'list',
                            //     view_mode: 'list',
                            //     target: 'current',
                            // });

                        return;
                    }
                });


            });

            //打开报表按钮
            this.$buttons.on('click', '.o_list_tender_button_open', function ()
            {
                var state = self.model.get(self.handle, {raw: true});
                // console.log(state);
                var check_id=[];
                var code = "";
                var name = "";
                var date = "";
                var category = "1";
                var titlerows = 0;
                var headrows = 0;
                var bodyrows = 0;
                var tailrows = 0;
                var bodycols = 0;


                for(var i=0;i<$('tbody .o_list_record_selector input').length;i++)
                {
                    if($('tbody .o_list_record_selector input')[i].checked===true)
                    {
                        check_id.push(state.res_ids[i]);
                        // alert(state.data[i].data.report_code);
                        code = state.data[i].data.report_code;
                        name = state.data[i].data.report_name;
                        date = state.data[i].data.report_date;
                        category = state.data[i].data.category;
                        titlerows = state.data[i].data.title_rows;
                        headrows = state.data[i].data.head_rows;
                        bodyrows = state.data[i].data.body_rows;
                        tailrows = state.data[i].data.tail_rows;
                        bodycols = state.data[i].data.total_cols;
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;
                // alert(check_id);

                if(check_id.length == 1)
                {
                    self.do_action
                    ({
                        type: 'ir.actions.client',
                        tag: 'statements',
                        name: name,
                        context : {
                            'report_code' : code,
                            'report_name' : name,
                            'report_date' : date,
                            'category'  : category,
                            'titlerows' : titlerows,
                            'headrows' : headrows,
                            'bodyrows' : bodyrows,
                            'tailrows' : tailrows,
                            'bodycols' : bodycols,
                        },
                     },
                     {   on_reverse_breadcrumb: function ()
                         {
                             self.reload();
                             },
                         on_close: function ()
                         {
                             self.reload();
                         }
                     });
                }
                else if(check_id.length > 1)
                {
                    $(function()
                    {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("打开功能只能选择一条记录。");
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
                else
                {
                    $(function()
                    {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要打开的记录。");
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

            //删除报表按钮
            this.$buttons.on('click', '.o_list_tender_button_delete', function ()
            {
                var state = self.model.get(self.handle, {raw: true});
                // console.log(state);
                var check_id=[];
                var code = "";
                var name = "";
                var date = "";

                for(var i=0;i<$('tbody .o_list_record_selector input').length;i++)
                {
                    if($('tbody .o_list_record_selector input')[i].checked===true)
                    {
                        check_id.push(state.res_ids[i]);
                        // alert(state.data[i].data.report_code);
                        code = state.data[i].data.report_code;
                        name = state.data[i].data.report_name;
                        date = state.data[i].data.report_date;
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;

                if(check_id.length>0)
                {
                    if(self.modelName=="ps.statement.statements")
                    {
                        var defdelete = self._rpc({
                            model: 'ps.statement.statements',
                            method: 'delete_statements',
                            args: [check_id]
                        }).then(function (result) {
                            if (result)
                            {
                                alert("删除成功。");
                            }
                            else
                            {
                                alert("删除失败，请检查。");
                            }
                            self.reload();
                        });
                    }
                }
                else
                {
                    $(function()
                    {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要删除的记录");
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

            //月末存档按钮
            this.$buttons.on('click', '.o_list_tender_button_monthend', function ()
            {
                var state = self.model.get(self.handle, {raw: true});
                var check_id=[];
                var code = "";
                var name = "";
                var date = "";

                for(var i=0;i<$('tbody .o_list_record_selector input').length;i++)
                {
                    if($('tbody .o_list_record_selector input')[i].checked===true)
                    {
                        check_id.push(state.res_ids[i]);
                        // alert(state.data[i].data.report_code);
                        code = state.data[i].data.report_code;
                        name = state.data[i].data.report_name;
                        date = state.data[i].data.report_date;
                    }
                }
                var ctx = state.context;
                ctx['active_ids'] = check_id;
                // alert(check_id);

                if(check_id.length>0)
                {
                    // alert(self.modelName);
                    if(self.modelName=="ps.statement.statements")
                    {
                        // alert(check_id);
                        var defmonthend = self._rpc({
                            model: 'ps.statement.statements',
                            method: 'monthend',
                            args: [check_id]
                        }).then(function (result) {
                            if (result)
                            {
                                alert("月末存档成功。");
                            }
                            else
                            {
                                alert("月末存档失败，请检查。");
                            }
                            self.reload();
                        });
                    }
                }
                else
                {
                    $(function()
                    {
                        var $div=$("<div>",{id:"dialog-message",title:"提示"});
                        var $p=$("<p>").html("请选择要进行月结的记录");
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
        }
    };

    ListView.include({
        init: function ()
        {
            this._super.apply(this, arguments);
            ImportViewMixin.init.apply(this, arguments);
        },
    });

    ListController.include({
        init: function () {
            this._super.apply(this, arguments);
            ImportControllerMixin.init.apply(this, arguments);
        },

        /**
         * Extends the renderButtons function of ListView by adding an event listener
         * on the import button.
         *
         * @override
         */
        renderButtons: function () {
            this._super.apply(this, arguments); // Sets this.$buttons
            ImportControllerMixin._bindImport.call(this);

            // if(this.modelName!=="ps.statement.statements")
            // {
            //     this.$buttons.find(".o_list_tender_button_create").css("display","none");
            //     this.$buttons.find(".o_list_tender_button_open").css("display","none");
            // }
            if(this.modelName=="ps.statement.statements")
            {
                this.$buttons.find(".o_list_button_add").css("display","none");
                this.$buttons.find(".o_button_import").css("display","none");
                // this.$buttons.find(".o_list_tender_button_create").css("display","inline-block");
                this.$buttons.find(".o_list_tender_button_open").css("display","inline-block");
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

            // if(this.modelName!=="ps.statement.formulas" && this.modelName!=="ps.statement.formula.params" && this.modelName!=="ps.statement.pivot.details" && this.modelName!=="ps.statement.classify.details")
            // {
            //     this.$buttons.find(".o_form_button_fcreateparams").css("display","none");
            // }

            //控制编辑按钮不可用，不成功，必须页面刷新才行
            // if(this.modelName=="ps.statement.formulas")
            // {
            //     var viewType = this.initialState.viewType;
            //     if (viewType == 'form')
            //     {
            //         var type = this.initialState.data['formula_type'];
            //         if (type == '0')
            //         {
            //             this.$buttons.find(".o_form_button_edit").attr("disabled", true);
            //         }
            //         else {
            //             this.$buttons.find(".o_form_button_edit").attr("disabled", false);
            //         }
            //         // console.log(this);
            //         var  flag = window.sessionStorage.getItem("flag");
            //         alert(flag);
            //         if(!flag)
            //         {
            //             alert('hhhhh');
            //             setInterval(function(){
            //                 window.location.reload();
            //             },5000);
            //            window.sessionStorage.setItem("flag","true");
            //         }
            //     }
            // }
        }
    });
});