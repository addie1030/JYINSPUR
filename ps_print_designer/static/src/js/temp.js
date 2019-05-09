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
                oP.setAttribute("class","cell_val");
                oSpan.innerHTML=arr1[0].id;
                oSpan.style.display="none";
                oSpan.setAttribute("class","myid");
                oA.innerHTML=arr1[1].modelName;
                oA.style.display="none";
                oA.setAttribute("class","mymodelname");
                newNode.setAttribute("type","checkbox");
                newNode.setAttribute("class","o_checkbox")
                newNode.value=arr2[i].name;
                oP.appendChild(newNode);
                oP.appendChild(myText);
                oP.appendChild(oSpan);
                oP.appendChild(oA);
                $el[0].appendChild(oP);
            };
            $el[2].children[0].onclick=function(){
                var obj=document.getElementsByClassName("o_checkbox");
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

                var bills = billId.split(',');
                var allKey = []

                $.ajax({
                    url: '/print_format_data',
                    data:JSON.stringify({"params":{"billId":bills,"modelName":modelName,"formatId":formatId}}),
                    dataType: 'json',
                    type: "POST",
                    async: false,
                    contentType: "application/json",
                    success: function (data) {
                        // 获取后台传递的所有单据数据,前台循环遍历向Reportbro服务发送打印请求。这种方式不好。
                         for ( var i = 0; i <data['result'].length; i++){
                            var report = data['result'][i]['report']
                            var fields_data = data['result'][i]['data'];
                            $.ajax({
                                //url: 'https://www.reportbro.com/report/run',
                                url: 'https://print-tools.mypscloud.com/reportbro/report/run',
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
                                    // 获取所有PDF的key值
                                    allKey.push(data.substr(4));
                                },
                                error: function (jqXHR, textStatus, errorThrown) {
                                    alert('服务器响应失败！');
                                }
                            });
                         };
                         window.open('/run?key=' + allKey.toString());
                         // var s = allKey.toString()
                         // console.log(s);
                         // $.ajax({
                         //    url: '/merger_pdf',
                         //    data:JSON.stringify({"params":{"key":allKey}}),
                         //    dataType: 'json',
                         //    type: "get",
                         //    async: false,
                         //    contentType: "application/json",
                         //    success: function (data) {
                         //        console.log(data);
                         //        var response = data['result']
                         //        console.log(response)
                         //        // var headers = response.headers();
                         //        // var blob = new Blob([response.data],{type:'application/pdf'});
                         //        // var link = document.createElement('a');
                         //        // link.href = window.URL.createObjectURL(blob);
                         //        // link.download = "Filename";
                         //        // link.click();
                         //
                         //    }
                         // })
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        alert('error');
                    }
                 });

                // 原打印 begin 2018年9月14日
                // for(i=0;i<bills.length;i++){
                //     $.ajax({
                //         url: '/print_format_data',
                //         data:JSON.stringify({"params":{"billId":bills[i],"modelName":modelName,"formatId":formatId}}),
                //         dataType: 'json',
                //         type: "POST",
                //         async: false,
                //         contentType: "application/json",
                //         success: function (data) {
                //             var report = data['result']['report']
                //             var fields_data = data['result']['data'];
                //             $.ajax({
                //                 url: 'https://www.reportbro.com/report/run',
                //                 data: JSON.stringify({
                //                     report: JSON.parse(report),
                //                     outputFormat: 'pdf',
                //                     data: fields_data,
                //                     isTestData: false
                //                 }),
                //                 type: "PUT",
                //                 async: false,
                //                 contentType: "application/json",
                //                 success: function (data) {
                //                     self.reportKey = data.substr(4);
                //                     allKey.push(data.substr(4));
                //                 },
                //                 error: function (jqXHR, textStatus, errorThrown) {
                //                     alert('服务器响应失败！');
                //                 }
                //             });
                //         },
                //         error: function (jqXHR, textStatus, errorThrown) {
                //             alert('失败！');
                //         }
                //      });
                // }
                // if(allKey.length == 1){
                //     window.open('https://www.reportbro.com/report/run' + '?key=' + allKey[0] + '&outputFormat=pdf' , 'newwindow')
                // }else {
                //     console.log(JSON.stringify({
                //         allKey:allKey
                //     }));
                //     $.ajax({
                //         url: '/merger_pdf',
                //         data:JSON.stringify({"allKey":allKey}),
                //         dataType: 'json',
                //         type: "POST",
                //         async: false,
                //         contentType: "application/json",
                //         success: function (data) {
                //             alert('目前不支持批量打印！');
                //         },
                //         error: function (jqXHR, textStatus, errorThrown) {
                //             alert('失败！');
                //         }
                //      });
                // }
                // 原打印 end


                // $.ajax({
                //     url: '/print_format_data',
                //     data:JSON.stringify({"params":{"billId":billId,"modelName":modelName,"formatId":formatId}}),
                //     dataType: 'json',
                //     type: "POST",
                //     async: false,
                //     contentType: "application/json",
                //     success: function (data) {
                //         var report = data['result']['report']
                //         var fields_data = data['result']['data'];
                //         console.log(report);
                //         console.log(fields_data);
                //         $.ajax({
                //             //url: 'https://www.reportbro.com/report/run',
                //             url: 'http://127.0.0.1:8888/reportbro/report/run',
                //             data: JSON.stringify({
                //                 report: JSON.parse(report),
                //                 outputFormat: 'pdf',
                //                 data: fields_data,
                //                 isTestData: false
                //             }),
                //             type: "PUT",
                //             async: false,
                //             contentType: "application/json",
                //             success: function (data) {
                //                 self.reportKey = data.substr(4);
                //                 //window.open('https://www.reportbro.com/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                //                 window.open('http://localhost:8888/reportbro/report/run' + '?key=' + self.reportKey + '&outputFormat=pdf' , 'newwindow')
                //             },
                //             error: function (jqXHR, textStatus, errorThrown) {
                //                 alert('服务器响应失败！');
                //             }
                //         });
                //     },
                //     error: function (jqXHR, textStatus, errorThrown) {
                //         alert('失败！');
                //     }
                //  });
            }
        },
        render: function () {

        },
    });
    core.action_registry.add('test_template', HomePage);
});