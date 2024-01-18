let interval;
function hi() {
    $.getJSON("/detect", (data) => {
        if (data["face_detected"] == true) {
            if (data["face_recognized"] == true) {
                clearInterval(interval);
                $.get("/whoami", (name, status) => {
                    $("#cam_img").attr("src", "/static/spinner.gif");
                    $("#message").html(`<h3>Wellcome! ${name}</h3>`);
                    setTimeout(()=>{
                        window.location= "/main"
                    }, 2000);
    
                })
            }
            else {
                $("#message").html("<h3>Not recognized</h3>");
            }
        }
        else {
            $("#message").html("<h3>No face detected. Please move closer to the camera</h3>");
        }
    })
}
$(document).ready(()=>{
    interval = setInterval(hi, 1000);
})
