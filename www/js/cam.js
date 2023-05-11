navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia
  || navigator.mozGetUserMedia || navigator.msGetUserMedia;

window.URL = window.URL || window.webkitURL || window.mozURL || window.msURL;

let videoWidth = 320,
    videoHeight = 288,
    videoFrameRate = 20,
    video = document.getElementById('video-player'),
    messageBox = document.getElementById('message-box'),
    front = false,
    canvas = document.getElementById('canvas'),
    stopRecords = false,
    detectUrl = 'http://api.face-control.local:9080/detect',
    diffCanvas = document.getElementById('diff-canvas'),
    captureIntervalTime = 500,
    pixelDiffThreshold = 120,
    scoreThreshold = 50,
    removeMessage = 1000;

canvas.width = videoWidth;
canvas.height = videoHeight;
diffCanvas.width = videoWidth;
diffCanvas.height = videoHeight;

let ctx = canvas.getContext('2d');

function startStream() {
    stopRecords = false;
    if (navigator.webkitGetUserMedia!=null) {
      let options = {
              audio: false,
              video: {
                width: { min: videoWidth, ideal: videoWidth, max: videoWidth },
                height: { min: videoHeight, ideal: videoHeight, max: videoHeight },
                frameRate: { ideal: videoFrameRate, max: videoFrameRate },
                facingMode: (front? "user" : "environment")
              }
            };

        navigator.webkitGetUserMedia(options, function(stream) {
                if (typeof (video.srcObject) !== 'undefined') {
                    video.srcObject = stream;
                } else {
                    video.src = URL.createObjectURL(stream);
                }

                DiffCamEngine.init({
                    stream: stream,
                    motionCanvas: diffCanvas,
                    captureIntervalTime: captureIntervalTime,
                    initSuccessCallback: initSuccess,
                    initErrorCallback: initError,
                    captureCallback: capture,
                    pixelDiffThreshold: pixelDiffThreshold,
                    scoreThreshold: scoreThreshold
                });

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

    fetch(detectUrl, {
        method: 'post',
        body: formData,
        headers: {
            'Access-Control-Allow-Origin':'*',
            'Access-Control-Allow-Methods':'*',
            'Access-Control-Allow-Credentials':'ture',
        },
    }).then((response) => {
        stopRecords = false;
        response.json().then(function(data) {
            if (data.messages.length > 0) {
                data.messages.forEach(function(item, index, array) {
                  if (item === '') {
                    return;
                  }
                  let li = document.createElement('li');
                  li.textContent = item;
                  if (data.employee_id > 0) {
                    li.classList.add('recognition_success');
                  } else if (data.employee_id < 0) {
                    li.classList.add('recognition_error');
                  } else {
                    li.classList.add('recognition_warning');
                  }
                  messageBox.appendChild(li);
                  setTimeout(function(){li.remove();}, removeMessage);
                });
            }

        });
    }).catch((error) => {
        stopRecords = false;
        console.log(error);
    });
}

function flipCam() {
    front = !front;
}

function initSuccess() {
	DiffCamEngine.start();
}

function initError() {
	console.log('Что-то пошло не так.');
}

function capture(payload) {
	//console.log(payload.score);

    if (payload.score > 2) {
        //ctx.drawImage(video, 0, 0, videoWidth, videoHeight);
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0, videoWidth*-1, videoHeight);
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


