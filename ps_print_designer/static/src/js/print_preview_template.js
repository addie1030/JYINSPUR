odoo.define('preview_template',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction')
    var HomePage=AbstractAction.extend({
        template: 'preview.template',
        init: function(parent, params){
            this.name="Print";
            this._super(parent);
            this.params=params;
            var data = params.params;
            var uuu = JSON.parse(data);
            if(uuu == null){
                alert("请先设计格式!")
            }else {
                this._rpc({route:'/print_design_server'}).then(function (stats) {
                    $(document).ready(function() {
                            function saveReport() {
                                var report = $('#reportbro').reportBro('getReport');
                                console.log(report);
                                $.ajax({
                                    url:'/print_design_save',
                                    data:JSON.stringify({
                                       'params':report,
                                    }),
                                    dataType:'json',
                                    type:'POST',
                                    async:false,
                                    contentType:'application/json',
                                    success: function (data) {
                                        alert("保存成功！");
                                    },
                                    error: function (jqXHR, textStatus, errorThrown) {
                                        alert('保存失败！');
                                    }
                                });
                            }
                            $('#reportbro').reportBro({
                                saveCallback: saveReport,
                                //reportServerUrl: "http://localhost:8888/reportbro/report/run",
                                additionalFonts: [
                                    { name: 'Firefly', value: 'firefly'},
                                    { name: 'yahei', value: 'yahei'},
                                ],
                            });
                            var report =
                                uuu
                            ;
                    $('#reportbro').reportBro('load', report);
                    });
                });
            }
            // this._rpc({route:'/print_design_server'}).then(function (stats) {
            //     $(document).ready(function() {
            //             function saveReport() {
            //                 var report = $('#reportbro').reportBro('getReport');
            //                 console.log(report);
            //                 $.ajax({
            //                    url:'/print_design_save',
            //                    data:JSON.stringify({
            //                        'params':report,
            //                    }),
            //                     dataType:'json',
            //                     type:'POST',
            //                     async:false,
            //                     contentType:'application/json',
            //                     success: function (data) {
            //                         alert("保存成功！");
            //                     },
            //                     error: function (jqXHR, textStatus, errorThrown) {
            //                         alert('保存失败！');
            //                     }
            //                 });
            //             }
            //             $('#reportbro').reportBro({
            //                 saveCallback: saveReport,
            //                 //reportServerUrl: "http://localhost:8888/reportbro/report/run",
            //                 additionalFonts: [{ name: 'Firefly', value: 'firefly'}],
            //             });
            //             var report =
            //                 uuu
            //             ;
            //     $('#reportbro').reportBro('load', report);
            //     });
            // });
        },
            events:{
                'click button#btnPrint': 'print',
                'click button#btnRen': 'ren'
            },
            start: function(){

            },
            render: function () {

            },
    });
    core.action_registry.add('preview_template', HomePage);
});