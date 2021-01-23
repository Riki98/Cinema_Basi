
$( document ).ready(function() {
    if($('#errorLog').val() != null){
        $('#modalSignin').click();
    }
    $('#inputTitle').val("Inserire titolo");
});

$('#inputTitle').on('click', function (){
    $('#inputTitle').val("");
});





/*
$('.titlefilm').on('click', function(){
  movieComplete =0;
  var movie = { 'title' : $(this).html() }
  if(lastTitolo != movie['title']) {
      if(!emptyDate) cleanDropDate();
      if(!emptyTime) cleanDropTime();
      emptyDate = 0;

      lastTitolo = movie['title'];
      document.getElementById("dropdown-title").innerHTML = movie["title"];
      $.ajax({
          type: 'POST',
          url: '/selectday',
          cache: false,
          contentType: 'application/json',
          processData: false,
          data: JSON.stringify(movie),
          success: on_request_success,
          error: on_request_error
      });
  }

function on_request_success(response) {
    var lenght = 10;
    var data = ""; var inf=11, sup=inf+9;
    for (index in response) {
        if(index >= inf && index <= sup) {
            if (response.hasOwnProperty(index)) {
                data += response[index];
                lenght--;
            }
        }
        if(lenght==0) {
            $('#dayfilm').append('<a class=\"dropdown-item datefilm\" href=\"#\">' + data + '</a>');
            data = "";
            inf = sup + 15;
            sup = inf + 9;
            lenght = 10;
        }
    }
    $('#dropdownMenuLinkFilm').click();
  }

function on_request_error(r, text_status, error_thrown) {
    console.debug('error', text_status + ", " + error_thrown + ":\n" + r.responseText);

}

});

$(document).on('click', '.datefilm', function() {
    movieComplete = 0;
    var movie = {'title': document.getElementById("dropdown-title").innerHTML, 'date': $(this).html()}
    if (lastDate != movie['date']) {
        if(!emptyTime) cleanDropTime();
        emptyTime = 0;

        lastDate = movie['date'];
        document.getElementById("dropdown-day").innerHTML = movie["date"];
        $.ajax({
            type: 'POST',
            url: '/selectime',
            cache: false,
            contentType: 'application/json',
            processData: false,
            data: JSON.stringify(movie),
            success: on_request_success,
            error: on_request_error
        });
    }

    function on_request_success(response) {
        var lenght = 5;
        var time = ""; var inf=13, sup=inf+9;
        for (index in response) {
            if(index >= inf && index <= sup) {
                if (response.hasOwnProperty(index)) {
                    time += response[index];
                    lenght--;
                }
            }
            if(lenght==0) {
                $('#timefilm').append('<a class=\"dropdown-item timefilm\" href=\"#\">' + time + '</a>');
                time = "";
                inf = sup + 15;
                sup = inf + 9;
                lenght = 5;
            }
        }
        $('#dropdownMenuLink').click();
    }

    function on_request_error(r, text_status, error_thrown) {
        console.debug('error', text_status + ", " + error_thrown + ":\n" + r.responseText);

    }

});

$(document).on('click', '.timefilm', function() {
    movieComplete = 1;
    var time = $(this).html();
    document.getElementById("dropdown-time").innerHTML = time;
});

function cleanDropTime(){
    $('.timefilm').remove();
    document.getElementById("dropdown-time").innerHTML = 'Orario';
    emptyTime = 1;
}

function cleanDropDate() {
    $('.datefilm').remove();
    document.getElementById("dropdown-day").innerHTML = 'Giorno';
    emptyDate = 1;
    lastDate = "";
}

$('#prenotazione').on('click', function () {
    var title = $('#dropdown-title').html();
    var day = $('#dropdown-day').html();
    var time = $('#dropdown-time').html();
    var movie = {'title': title, 'date': day, 'time':time }
    if(movieComplete){
    $.ajax({
            type: 'POST',
            url: '/prenotazione',
            cache: false,
            contentType: 'application/json',
            processData: false,
            data: JSON.stringify(movie),
            success: on_request_success,
            error: on_request_error
        });
    }

    function on_request_success(response) {
        console.log("prenotazione in corso, database rende atomica la risorsa?? si bisogna farlo sull'app.py")
    }
    function on_request_error(r, text_status, error_thrown) {
        console.debug('error', text_status + ", " + error_thrown + ":\n" + r.responseText);
    }

});

/* data: JSON.stringify(movie), */



