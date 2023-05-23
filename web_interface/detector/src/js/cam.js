document.addEventListener("DOMContentLoaded", () => {
    if (CONFIG.debugging) {
        debug('Page loading completed');
        debug('API URL: ' + CONFIG.apiUrl);
    }

    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia
        || navigator.mozGetUserMedia || navigator.msGetUserMedia;

    window.URL = window.URL || window.webkitURL || window.mozURL || window.msURL;
});

let video = document.getElementById('video-player'),
    front = false,
    canvas = document.getElementById('canvas'),
    stopRecords = false,
    diffCanvas = document.getElementById('diff-canvas');

canvas.width = CONFIG.videoWidth;
canvas.height = CONFIG.videoHeight;
diffCanvas.width = CONFIG.videoWidth;
diffCanvas.height = CONFIG.videoHeight;

let ctx = canvas.getContext('2d');

function startStream() {
    stopRecords = false;
    if (navigator.getUserMedia!=null) {
      let options = {
              audio: false,
              video: {
                width: {min: CONFIG.videoWidth, ideal: CONFIG.videoWidth, max: CONFIG.videoWidth},
                height: {min: CONFIG.videoHeight, ideal: CONFIG.videoHeight, max: CONFIG.videoHeight},
                frameRate: {ideal: CONFIG.videoFrameRate, max: CONFIG.videoFrameRate},
                facingMode: (front? "user" : "environment")
              }
            };

        navigator.getUserMedia(options, function(stream) {
                if (typeof (video.srcObject) !== 'undefined') {
                    video.srcObject = stream;
                } else {
                    video.src = URL.createObjectURL(stream);
                }

                DiffCamEngine.init({
                    stream: stream,
                    motionCanvas: diffCanvas,
                    captureIntervalTime: CONFIG.captureIntervalTime,
                    initSuccessCallback: initSuccess,
                    initErrorCallback: initError,
                    captureCallback: capture,
                    pixelDiffThreshold: CONFIG.pixelDiffThreshold,
                    scoreThreshold: CONFIG.scoreThreshold
                });
                document.querySelector('.bg-video').classList.add('hidden');
                document.getElementById('start-stream').classList.add('active');
                document.getElementById('stop-stream').classList.remove('active');
                document.getElementById('stop-stream').addEventListener('click', function () {
                    stream.getVideoTracks().forEach(function (track) {
                        track.stop();
                    });
                    DiffCamEngine.stop();
                    stopRecords = true;
                    video.srcObject = null;
                    video.src = '';
                    window.location.reload();
                });
            },
            function(e) {console.log(e);}
        );
    }
}

function postImgToServer(file) {
    stopRecords = true;
    let formData = new FormData();
    formData.append("file", file);

    fetch(CONFIG.apiUrl + CONFIG.detectUrl, {
        method: 'post',
        body: formData,
        headers: {
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Methods':'*',
            'Access-Control-Allow-Credentials':'ture',
            'AuthKey': CONFIG.apiKey,
        },
    }).then((response) => {
        stopRecords = false;
        response.json().then(function(data) {
            if (data.messages.length > 0) {
                let title = '',
                    action = 'success',
                    body = '<ul>',
                    child = '',
                    bodyEnd = '</ul>';


                if (data.employee_id > 0) {
                    action = 'success';
                    title = 'Успешная идентификация';
                    child = child + '<li>' +
                        '<img class="img" src="'+CONFIG.apiUrl+'images/persons/' + data.employee_id + '.jpg" />' +
                        '</li>'
                } else if (data.employee_id < 0) {
                    title = 'Доступ запрещен';
                    action = 'error';
                } else {
                    title = 'Повторите идентификацию';
                    action = 'warning';
                }
                data.messages.forEach(function(item, index, array) {
                    if (item === '') {
                        return;
                    }
                    child = child + '<li>' + item + '</li>';
                });

                setTimeout(function () {
                    body = body + child + bodyEnd;
                    toast(title, body, action)
                }, 100);
            }

        });
    }).catch((error) => {
        stopRecords = false;
        debug(error);
        if (CONFIG.debugging) {
            toast('Ошибка', error, 'error')
        }
    });
}

function flipCam() {
    front = !front;
}

function initSuccess() {
	DiffCamEngine.start();
}

function initError() {
	debug('Что-то пошло не так.');
}

function capture(payload) {
	//console.log(payload.score);

    if (payload.score > 2) {
        //ctx.drawImage(video, 0, 0, CONFIG.videoWidth, CONFIG.videoHeight);
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, CONFIG.videoWidth*-1, CONFIG.videoHeight);
        ctx.restore();

        var imgData = canvas.toDataURL(),
        blobBin = atob(imgData.split(',')[1]);
        var array = [];
        for(let i = 0; i < blobBin.length; i++) {
            array.push(blobBin.charCodeAt(i));
        }
        let file = new Blob([new Uint8Array(array)], {type: 'image/png'});

        if (!stopRecords) {
            postImgToServer(file);
        }

        //var img = document.getElementById('img');
        //img.src = imgData;
    }
}

function debug(text) {
    console.log(text);
}

function toast(title, body, action) {
    if (!body || body === '') {
        return;
    }

    let toast = document.querySelector('#toast'),
        toastTitle = document.querySelector('#toast #toast-title'),
        toastBody = document.querySelector('#toast #toast-body'),
        toastClose = document.querySelector('#toast #toast-close');

    if (action === 'error') {
        toast.classList.add('bg-red-600');
        toastBody.classList.add('bg-red-500');

        toast.classList.remove('bg-teal-600');
        toastBody.classList.remove('bg-teal-500');
        toast.classList.remove('bg-yellow-600');
        toastBody.classList.remove('bg-yellow-500');
    } else if (action === 'warning') {
        toast.classList.add('bg-yellow-600');
        toastBody.classList.add('bg-yellow-500');

        toast.classList.remove('bg-teal-600');
        toastBody.classList.remove('bg-teal-500');
        toast.classList.remove('bg-red-600');
        toastBody.classList.remove('bg-red-500');
    } else {
        toast.classList.add('bg-teal-600');
        toastBody.classList.add('bg-teal-500');

        toast.classList.remove('bg-red-600');
        toastBody.classList.remove('bg-red-500');
        toast.classList.remove('bg-yellow-600');
        toastBody.classList.remove('bg-yellow-500');
    }

    if (CONFIG.debugging) {
        title = 'DEBUG: ' + title
    }
    toastTitle.innerHTML = title;
    toastBody.innerHTML = body;
    toast.setAttribute('data-te-toast-show', '');

    toastClose.onclick = function() {
        toast.removeAttribute('data-te-toast-show');
        toastTitle.innerHTML = '';
        toastBody.innerHTML = '';
    };
    setTimeout(function () {
        toast.removeAttribute('data-te-toast-show');
        toastTitle.innerHTML = '';
        toastBody.innerHTML = '';
    }, CONFIG.toastTime);
}
