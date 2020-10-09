var green = "green";
var yellow = "yellow";
var red = "red";



$('.sala-icon').on('click',function(){

    var id="#"+$(this).getAttribute(numero)+$(this).getAttribute(fila);
    colore = $(this).getAttribute(color-posto);
    var newcolore;
    if(colore == green) newcolore = yellow;
    else newcolore = green;
    console.log(id);
    $(id+colore).style.visibility = "hidden";
    $(id+newcolore).style.visibility = "visible";
    $(this).attr('colore-posto', newcolore);
});



