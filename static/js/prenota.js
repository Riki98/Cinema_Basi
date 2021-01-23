var green = "green";
var yellow = "yellow";
var red = "red";

let preonotati = [];


$('#btnReset').on('click',function(){
    $('.sala td.prenotato').removeClass("prenotato").addClass("libero");
    preonotati = [];
    $("#posti").val(JSON.stringify(preonotati));
});

$('.sala td.libero').on('click',function(){
    let posto = $(this);
    posto.addClass("prenotato");
    posto.removeClass("libero");
    preonotati.push(posto[0].dataset);
    $("#posti").val(JSON.stringify(preonotati));
});


