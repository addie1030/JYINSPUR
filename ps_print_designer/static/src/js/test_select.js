$(".print_row").click(function(){
    var num=$(this).index();
    $(".print_row").eq(num).find("input").attr("checked","checked");
    $(".print_row").eq(num).siblings().find("input").removeAttr("checked","checked");
})
$("#btn_print").click(function(){
    window.opener=null;
    window.open('','_self');
    window.close();
})