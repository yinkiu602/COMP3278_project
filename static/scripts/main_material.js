$(document).ready(() => {
    target = document.getElementById("upcoming_content");
    $.getJSON("/fetch_material", (data) => {
        for (i in data) {
            $("#upcoming_content").append(`<button class="collapse" type="button">${i}    ${data[i]["Room"]}    ${data[i]["Start time"]}-${data[i]["End time"]}</button>`)
            let display_text = "<b>Room:</b> " + data[i]["Room"] + "<br>" + "<b>Time:</b> " + data[i]["Start time"] + "-" + data[i]["End time"] + "<br>";
            if (data[i]["zoom_link"] != "") {
                display_text += "<b>Zoom Link: </b>" + `<a href='${data[i]["zoom_link"]}'>${data[i]["zoom_link"]}</a>` + "<br>";
            }
            display_text += "<b>Material:</b> ";
            $("#upcoming_content").append(`<p class='collapse_content'>${display_text}</p>`);
            if (data[i]["Material"].length == 0) {
                $(".collapse_content").last().append("No material available");
            }
            else {
                for (let j = 0; j < data[i]["Material"].length; j++) {
                    if (j == 0) {
                        $(".collapse_content").last().append(`${data[i]["Material"][j]["type"]} <br> <menu>`);
                    }
                    else {
                        if (data[i]["Material"][j]["type"] != data[i]["Material"][j - 1]["type"]) {
                            $(".collapse_content").last().append("</menu>" + data[i]["Material"][j]["type"] + "<menu>");
                        }
                    }
                    $(".collapse_content").last().append(`<li> <a href='${data[i]["Material"][j]["link"]}'>${data[i]["Material"][j]["name"]}</a></li>`);
                }
                $(".collapse_content").last().append("</menu>");
            }
        }
        $(".collapse").click(function () {
            $(this).next().slideToggle("slow");
        });
    });
});
