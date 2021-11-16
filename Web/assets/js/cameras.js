function newCamera() {
    new swal({
        title: 'New Camera',
        html:
            '<div class="form-group">\n' +
            '    <label>IP Camera URL</label>\n' +
            '    <input class="form-control" id="camURL" value="" placeholder="Enter stream URL">\n' +
            '</div>',
        showCancelButton: true,
        confirmButtonText: 'Add Camera',
        showLoaderOnConfirm: true,
        buttonsStyling: false,
        confirmButtonClass: 'btn btn-success btn-xs mr-1',
        cancelButtonClass: 'btn btn-xs ml-1',
        preConfirm: function () {
            return new Promise((resolve, reject) => {

                resolve({
                    camURL: $('input[id="camURL"]').val()
                });


            });
        },
        allowOutsideClick: false
    }).then(function (result) {
        console.log(result)
        new swal({
            title: 'Adding New Camera',
            allowOutsideClick: false
        });
        swal.showLoading();
        $.ajax({
            type:'POST',
            data:{'camURL':result.value.camURL},
            url:'/add_camera',
            success:function(data) {

                if (data.error)
                {
                    swal.close();
                    new swal({
                        title: 'Failed to add Camera.',
                        icon: "error",
                        timer: 5000,
                    });
                    return;
                }

                swal.close();
                cameraSettingHTML(data);
                Swal.fire({
                    icon: 'success',
                    title: 'Camera Added Successfully',
                    text: '',
                    footer: '',
                    heightAuto: false,
                    timer: 5000,
                    allowOutsideClick: false,
                });

                return;
            },
            error: function(xhr, status, error){
                swal.close();
                new swal({
                    title: 'Failed to add Camera. Unknown Error',
                    icon: "error",
                    timer: 5000,
                });
            }
        })
    }).catch(swal.noop)
}

function cameraSettingHTML(cam) {
    let html = `
        <div class="card col-xl-4 col-lg-6 mb-3 col-6">
            <img class="card-img-top mt-2" id="cameraSrc-${cam.camNum}" src="/video_streamer/${cam.camNum}" alt="CCTV-${cam.camNum}">
            <div class="card-body">
                <div class="row">
                    <div class="col-6" id="cameraAction-${cam.camNum}">
                        <a href="#" class="btn btn-primary w-100" id="stopCamera" data-id="${cam.camNum}">Stop</a>
                    </div>
                    <div class="col-6">
                        <a href="#" class="btn btn-danger w-100" id="removeCamera" data-id="${cam.camNum}">Remove</a>
                    </div>
                </div>
            </div>
        </div>`;
    $('#cameraList').append(html);
}

$(document).on('click', '#startCamera', function(e) {
    e.preventDefault();
    startCamera($(this).data('id'));
})

function startCamera(id) {
    $.ajax({
        type:'POST',
        data:{'camID':id,'action':'start'},
        url:'/setcamera',
        success:function(data) {
            $(`#cameraSrc-${id}`).attr('src', `/video_streamer/${id}?time${new Date().getTime()}`)
            $(`#cameraAction-${id}`).html(`<a href="#" class="btn btn-primary w-100" id="stopCamera" data-id="${id}">Stop</a>`)
            console.log(data);
        },
        error: function(xhr, status, error){
            //console.log(data);
        }
    })
}

$(document).on('click', '#stopCamera', function(e) {
    e.preventDefault();
    stopCamera($(this).data('id'));
})

function stopCamera(id) {
    $.ajax({
        type:'POST',
        data:{'camID':id,'action':'stop'},
        url:'/setcamera',
        success:function(data) {
            $(`#cameraAction-${id}`).html(`<a href="#" class="btn btn-success w-100" id="startCamera" data-id="${id}">Start</a>`)
            console.log(data);
        },
        error: function(xhr, status, error){
            //console.log(data);
        }
    })
}