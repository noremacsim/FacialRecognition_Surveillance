//TODO: Update and Improve Function
function addCamera() {
    new swal({
        title: 'Adding New Camera',
        allowOutsideClick: false
    });
    swal.showLoading();
    //getting selected option from dropdowns

    //TODO: Change to form and get submited form value's
    var camURL = document.getElementById("camURL").value;
    var e1 = document.getElementById("application");
    var application = e1.options[e1.selectedIndex].value;
    var e2 = document.getElementById("detectionMethod");
    var detectionMethod = e2.options[e2.selectedIndex].value;
    var fpstweak = document.getElementById("fpstweak");

    alertstyle = "alert-success";


    var icon = '<i class="fa fa-video-camera fa-3x" aria-hidden="true"></i>'
    var icondiv = '<div class="product-info">' + icon  +'</div>'

    if(detectionMethod == "opencv"){
        dlibDetection = false;
    }
    else{
        dlibDetection = true;
    }

    if(fpstweak == "checked"){
        fpstweak = true;
    }
    else{
        fpstweak = false;
    }

    $('#addcam').html('<i class="fa fa-spin fa-cog fa-3x fa-fw" style="font-size:12px;"></i> Adding Camera');

    console.log("Front end logging:"  + camURL + " " + application + " " + detectionMethod + " FPS Tweak: " + fpstweak);
    $.ajax({
        type: "POST",
        url: "/add_camera",
        data : {'camURL': camURL, 'application': application, 'detectionMethod': dlibDetection, 'fpstweak': fpstweak},
        success: function(cam) {
            $('#facialBlock').show();
            $('#controlPanel').hide();
            swal.close()
            let html = `<div class="col-12">
                                <img src="/video_streamer/${cam.camNum}" id="${cam.camNum}" class="rounded mx-auto d-block" alt="camera-${cam.camNum}">
                            </div>`;
            $('#surveillance_panel').append(html)
            console.log(cam);
            $('#addcam').html('Add Camera');

        },
        error: function(error) {
            console.log(error);
        }
    });


}


$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/surveillance');

    socket.on('system_monitoring', function(json) {

        console.log("System Monitoring: " + json);
        var systemState = JSON.parse(json);
        var i = 0;
        for (; i < systemState.processingFPS.length;i++) {
            // document.getElementById( "camera_" + i + "_fps").text = systemState.processing_fps[i];
            $("#camera_" + i + "_fps").html(systemState.processingFPS[i]);


        }

        $('#memory_usage').attr('style', "width: " + systemState.memory + "%;");
        $('#cpu_usage').attr('style', "width: " + systemState.cpu + "%;");
    });

    socket.on("connect_error", (err) => {
        console.log(`connect_error due to ${err.message}`);
    });


});