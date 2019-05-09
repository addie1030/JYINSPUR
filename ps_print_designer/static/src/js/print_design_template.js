odoo.define('design_template',function(require){
    "use strict";
    var core = require('web.core');
    // var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction')
    var HomePage=AbstractAction.extend({
        template: 'design.template',
        init: function(parent, params){
            this.name="Print";
            this._super(parent);
            this.params=params;
            var data = params.params.data;
            var id = params.params.id;
            var uuu = JSON.parse(data)
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
                                { name: 'Firefly', value: 'firefly'}
                            ],
                        });
                        var report =
                        {
                              "docElements":[
                              ],
                              "parameters":
                                uuu
                              ,
                              "styles":[],
                              "version":1,
                              "documentProperties":
                                  {
                                      "pageFormat":"A4","pageWidth":"","pageHeight":"","unit":"mm","orientation":"portrait","contentHeight":"","marginLeft":"20","marginTop":"20","marginRight":"20","marginBottom":"10","header":true,"headerSize":"60","headerDisplay":"always","footer":true,"footerSize":"60","footerDisplay":"always","patternLocale":"de","patternCurrencySymbol":id
                                  }
                        };
                $('#reportbro').reportBro('load', report);
                });
            });
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
    core.action_registry.add('design_template', HomePage);
});