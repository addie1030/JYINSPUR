// 自动勾选第一条打印格式
// Author:caotifu
$(document).ready(function () {
    $(".print_row").eq(0).find("input").attr("checked","checked");
    $(".print_row").eq(0).siblings().find("input").removeAttr("checked","checked");
});

// 打开打印框,单一选择实现
$(".print_row").click(function(){
    var num=$(this).index();
    $(".print_row").eq(num).find("input").attr("checked","checked");
    $(".print_row").eq(num).siblings().find("input").removeAttr("checked","checked");
})
// 开始打印、关闭打印框
$("#btn_print").click(function(){
    window.opener=null;
    window.open('','_self');
    // Author:caotifu
    $("button[class=close]").click();
})