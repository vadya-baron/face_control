function toggle_visibility($this, selectorId) {
    let e = document.getElementById(selectorId),
        arrow = $this.querySelector('.arrow-icon');

    if(e.style.display === 'block') {
        fadeOutEffect(selectorId);
        arrow.style.transform = 'rotate(0deg)';
    } else {
        fadeInEffect(selectorId);
        arrow.style.transform = 'rotate(180deg)';
    }
}

function fadeOutEffect(selectorId) {
    let fadeTarget = document.getElementById(selectorId);
    fadeTarget.style.transition = '0.8s';
    fadeTarget.style.opacity = 0;

    let timerId = setTimeout(function () {
        fadeTarget.style.display = 'none';
    }, 800);
}

function fadeInEffect(selectorId) {
    let fadeTarget = document.getElementById(selectorId);
    fadeTarget.style.display = 'block';
    fadeTarget.style.opacity = 0;
    let timerId = setTimeout(function () {
        fadeTarget.style.transition = '0.8s';
        fadeTarget.style.opacity = 1;
    }, 200);
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
        toast.classList.remove('bg-teal-600');

        toastBody.classList.add('bg-red-500');
        toastBody.classList.remove('bg-teal-500');
    } else {
        toast.classList.add('bg-teal-600');
        toast.classList.remove('bg-red-600');

        toastBody.classList.add('bg-teal-500');
        toastBody.classList.remove('bg-red-500');
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
    let timerId = setTimeout(function () {
        toast.removeAttribute('data-te-toast-show');
        toastTitle.innerHTML = '';
        toastBody.innerHTML = '';
    }, CONFIG.toastTime);
}

function debug(content) {
    console.log(content);
}

async function getHash(str, algo = 'SHA-256') {
    let strBuf = new TextEncoder().encode(str);
    return await crypto.subtle.digest(algo, strBuf)
        .then(hash => {
            window.hash = hash;
            let result = '';
            const view = new DataView(hash);
            for (let i = 0; i < hash.byteLength; i += 4) {
                result += ('00000000' + view.getUint32(i).toString(16)).slice(-8);
            }
            return result;
        });
}

function getCurrentDateString() {
    let mouths = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'],
        dates = ['', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15',
            '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'],
        currentDate = new Date();

    return currentDate.getFullYear()+'-'+mouths[currentDate.getMonth()]+'-'+dates[currentDate.getDate()];
}
