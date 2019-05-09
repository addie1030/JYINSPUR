odoo.define('test_template',function(require){
    "use strict";
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction')
    var HomePage=AbstractAction.extend({
        template: 'TestIndex',
        init: function(parent, params){
            this.name="Print";
            this._super(parent);
            this.params = params;

        },
        start: function(){
            // console.log(this.params);
            var arr1=this.params.params.result.bill;
            var arr2=this.params.params.result.format;
            var $el=this.$el;
            for(var i=0;i<arr2.length;i++){
                // var $select=$("<input>","type:checkbox").val(arr[i].name);
                var oP=document.createElement("p");
                var newNode = document.createElement("input");
                var myText=document.createTextNode(arr2[i].name);
                var oSpan=document.createElement("span");
                var oA=document.createElement("a");
                oP.setAttribute("class","print_row");
                oSpan.innerHTML=arr1[0].id;
                oSpan.style.display="none";
                oSpan.setAttribute("class","myid");
                oA.innerHTML=arr1[1].modelName;
                oA.style.display="none";
                oA.setAttribute("class","mymodelname");
                newNode.setAttribute("type","checkbox");
                newNode.setAttribute("class","myval")
                newNode.value=arr2[i].name;
                oP.appendChild(newNode);
                oP.appendChild(myText);
                oP.appendChild(oSpan);
                oP.appendChild(oA);
                $el[0].appendChild(oP);
            };
            // console.log($el)
            $el[2].children[0].onclick=function(){
                var obj=document.getElementsByClassName("myval");
                var oid=document.getElementsByClassName("myid");
                var omodelname=document.getElementsByClassName("mymodelname");
                var check_val=[];
                for(var i=0;i<obj.length;i++){
                    if(obj[i].checked){
                        check_val.push(obj[i].value);
                        var formatId = obj[i].value;
                        check_val.push(oid[0].innerText);
                        check_val.push(omodelname[0].innerText);
                    }
                }
                var billId = oid[0].innerText;
                var modelName = omodelname[0].innerText;
                // console.log();
                console.log(JSON.stringify({"billId":billId,"modelName":modelName,"formatId":formatId}));
                $.ajax({
                    url: '/print_format_data',
                    data:JSON.stringify({"params":{"billId":billId,"modelName":modelName,"formatId":formatId}}),
                    dataType: 'json',
                    type: "POST",
                    async: false,
                    contentType: "application/json",
                    success: function (data) {
                        var report = data['result']['report']
                        var fields_data = data['result']['data'];
                        console.log(report);
                        console.log(fields_data);
                        $.ajax({
                            url: 'https://www.reportbro.com/report/run',
                            //url: 'http://127.0.0.1:8888/reportbro/report/run',
                            data: JSON.stringify({
                                report: JSON.parse(report),
                                outputFormat: 'pdf',
                                data: fields_data,
                                isTestData: false
                            }),
                            type: "PUT",
                            async: false,
                            contentType: "application/json",
                            success: function (data) {
                                self.reportKey = data.substr(4);
                                window.open('https://www.reportbro.com/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                                //window.open('http://localhost:8888/reportbro/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                            },
                            error: function (jqXHR, textStatus, errorThrown) {
                                alert('服务器响应失败！');
                            }
                        });
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        alert('失败！');
                    }
                 });
                window.close();
                // $('#btn_print').click();
            }
        },
        render: function () {

        },
    });
    core.action_registry.add('test_template', HomePage);
});