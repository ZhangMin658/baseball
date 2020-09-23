$(document).ready(function () {
    var out_file = "";
    (function getOutData() {
        out_file = $("#download").attr("data");
        setTimeout(function() {
            if (typeof out_file === "undefined" || out_file == "") {
                getOutData();
            } else {
                $("#download").prop('disabled', false);
                $(".circle").css("display","none");
            }
        }, 100);
    })(); 

    $("#download").on('click', function(){
        var url = 'http://localhost:3000/static/uploads/' + out_file;
        var link = document.createElement("a");
        link.download = 'result.avi';
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        delete link;
    });

    $(".start").on('click', function(){
        if($('.circle').css('display') == 'none')
        {
            $(".circle").show();
        }
    });
});