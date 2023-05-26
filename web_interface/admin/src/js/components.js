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
        interval: CONFIG.toastTime
    });

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


// const myDatepicker = new Datepicker(
//     document.querySelector('#' + id),
//     {
//         title: 'Дата',
//         monthsFull: [
//             'Январь',
//             'Февраль',
//             'Март',
//             'Апрель',
//             'Май',
//             'Июнь',
//             'Июль',
//             'Август',
//             'Сентябрь',
//             'Октябрь',
//             'Ноябрь',
//             'Декабрь',
//         ],
//         monthsShort: [
//             'Янв',
//             'Фев',
//             'Март',
//             'Апр',
//             'Май',
//             'Июнь',
//             'Июль',
//             'Авг',
//             'Сен',
//             'Окт',
//             'Ноя',
//             'Дек',
//         ],
//         weekdaysFull: [
//             'Воскресенье',
//             'Понедельник',
//             'Вторник',
//             'Среда',
//             'Четверг',
//             'Пятница',
//             'Суббота',
//         ],
//         weekdaysShort: ['Вос', 'Пон', 'Втор', 'Ср', 'Чет', 'Пят', 'Суб'],
//         weekdaysNarrow: ['В', 'П', 'В', 'С', 'Ч', 'П', 'С'],
//         okBtnText: 'Применить',
//         clearBtnText: 'Очистить',
//         cancelBtnText: 'Закрыть',
//     }
// );
