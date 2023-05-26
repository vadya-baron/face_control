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

    let toastIcon = '<svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="info-circle" ' +
            'class="mr-2 h-4 w-4 fill-current" role="img" xmlns="http://www.w3.org/2000/svg" ' +
            'viewBox="0 0 512 512"><path fill="currentColor" ' +
            'd="M256 8C119.043 8 8 119.083 8 256c0 136.997 111.043 248 248 248s248-111.003 248-248C504 119.083 ' +
            '392.957 8 256 8zm0 110c23.196 0 42 18.804 42 42s-18.804 42-42 42-42-18.804-42-42 18.804-42 ' +
            '42-42zm56 254c0 6.627-5.373 12-12 12h-88c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 ' +
            '12-12h12v-64h-12c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 12-12h64c6.627 0 12 5.373 12 ' +
            '12v100h12c6.627 0 12 5.373 12 12v24z"></path></svg> ';

    if (CONFIG.debugging) {
        title = 'DEBUG: ' + title
    }
    new Toast({
        title: '<div class="flex">' + toastIcon + title + '</div>',
        text: body,
        theme: action,
        autoHide: true,
        addContainer: false,
        intervalBetweenMessages: 2000,
        interval: CONFIG.toastTime
    });
}
