var oIpt=document.getElementsByClassName("my_coding")[0];
oIpt.oninput=function(){
    if(oIpt.value.length>5){
        oIpt.value=oIpt.value.slice(0,5);
    };
}
oIpt.onblur=function(){
    var a=oIpt.value.split('').join("-");
    oIpt.value=a;
}
oIpt.onfocus=function(){
    oIpt.value='';
}