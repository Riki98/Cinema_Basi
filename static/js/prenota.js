var green = "green";
var yellow = "yellow";
var red = "red";

let preonotati = [];
let numPosti = 1;
let numPostiPosizionati = 0;

$(document).ready(function(){
   console.log("JavaScript & JQuery are working!")
});

$('#bottone').on('click', function (){
    alert("DIOCANE");
});

$('#numPosti').on('click',function(){
    numPosti = $(this).val();
    console.log("ciaoo");
    $('.sala td.prenotato').removeClass("prenotato").addClass("libero");
    preonotati = [];
    numPostiPosizionati= 0;
    $("#posti").val(JSON.stringify(preonotati));
});

$('.sala td.libero').on('click',function(){
    let posto = $(this);
    console.log("ciaoo");
    if(numPostiPosizionati>=numPosti){
        alert("n max posti raggiunto");
        return;
    }
    numPostiPosizionati++;

    posto.addClass("prenotato");
    posto.removeClass("libero");

    preonotati.push(posto[0].dataset);
    $("#posti").val(JSON.stringify(preonotati));
});


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



