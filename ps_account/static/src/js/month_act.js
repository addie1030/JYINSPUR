var bool1=true;
var bool2=true;
var bool3=true;
var bool4=true;
$("#first_top").click(function(){
    if(!bool1){
        $("#first_bottom").slideDown();
        $("#one").attr("src","/ps_account/static/src/img/jx.png")
    }else{
        $("#first_bottom").slideUp();
        $("#one").attr("src","/ps_account/static/src/img/jr.png")
    }
    bool1=!bool1;
})
$("#second_top").click(function(){
    if(!bool2){
        $("#second_bottom").slideDown();
        $("#two").attr("src","/ps_account/static/src/img/jx.png")
    }else{
        $("#second_bottom").slideUp();
        $("#two").attr("src","/ps_account/static/src/img/jr.png")
    }
    bool2=!bool2;
})
$("#third_top").click(function(){
    if(!bool3){
        $("#third_bottom").slideDown();
        $("#three").attr("src","/ps_account/static/src/img/jx.png")
    }else{
        $("#third_bottom").slideUp();
        $("#three").attr("src","/ps_account/static/src/img/jr.png")
    }
    bool3=!bool3;
})
$("#forth_top").click(function(){
    if(!bool4){
        $("#forth_bottom").slideDown();
        $("#four").attr("src","/ps_account/static/src/img/jx.png")
    }else{
        $("#forth_bottom").slideUp();
        $("#four").attr("src","/ps_account/static/src/img/jr.png")
    }
    bool4=!bool4;
})
