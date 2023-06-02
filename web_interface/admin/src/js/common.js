document.addEventListener("DOMContentLoaded", () => {
    if (CONFIG.debugging) {
        debug('Page loading completed');
        debug('API URL: ' + CONFIG.apiUrl);
    }

    currentDateHandler();
    setTimeout(function () {
        firstLoadContent();
        mainMenuHandler();
        formListener([
            document.getElementById('form-add-employee'),
        ]);

    }, 100);
});

function currentDateHandler() {
    let today = new Date(),
        options = {hour: 'numeric', minute: 'numeric'};
    CONFIG.currentDateContainer.innerHTML = today.toLocaleDateString('ru-RU') +
        ' - ' + today.toLocaleTimeString('ru-RU', options);
    setTimeout(function () {
        currentDateHandler();
    }, 60000);
}

function firstLoadContent() {
    let activeMenu = document.querySelector('#main-menu a.active'),
        id = activeMenu.getAttribute('data-id'),
        url = activeMenu.getAttribute('data-url'),
        handler = activeMenu.getAttribute('data-handler');

    if (id === 'dashboard') {
        shadowsUpdateData(id, url, handler, CONFIG.shadowsUpdateDataTime);
    }

    loadData(CONFIG.apiUrl + url).then(
        response => builderSuccessData(response, id, handler),
        error => errorHandler(error, id, handler)
    );



}

function shadowsUpdateData(id, url, handler, interval) {
    let sectionHidden = document.getElementById(id).classList.contains('hidden') || false;
    setTimeout(function () {
        debug(!sectionHidden);
        if (!sectionHidden) {
            loadData(CONFIG.apiUrl + url).then(
                response => builderSuccessData(response, id, handler, false),
                error => errorHandler(error, id, handler)
            );
        }
        shadowsUpdateData(id, url, handler, interval);
    }, interval);
}

function mainMenuHandler() {
    let mainMenu = document.querySelectorAll('#main-menu a');
    [].forEach.call(mainMenu, function(el) {
        el.onclick = function(e) {
            e.preventDefault();
            let id = el.getAttribute('data-id'),
                url = el.getAttribute('data-url'),
                handler = el.getAttribute('data-handler'),
                sectionsMenu = el.getAttribute('data-section-menu') || false,
                sections = document.querySelectorAll('section.section');

            document.querySelector('#main-menu a.active').classList.remove('active');
            el.classList.add('active');
            [].forEach.call(sections, function(section) {
                section.classList.add('hidden');
            });

            CONFIG.loader.classList.remove('hidden');
            setTimeout(function (){
                if (url) {
                    loadData(CONFIG.apiUrl + url).then(
                        response => builderSuccessData(response, id, handler),
                        error => errorHandler(error, id, handler)
                    ).catch(function () {
                        CONFIG.loader.classList.add('hidden');
                        errorHandler(
                            'loadData catch',
                            id,
                            handler,
                            'Ошибка',
                            'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку'
                        );
                    });
                } else {
                    builderSuccessData(null, id);
                }

                if (sectionsMenu) {
                    sectionMenuHandler(id)
                }

            }, 300);
        }
    });
}

function sectionMenuHandler(containerId) {
    let sectionMenu = document.querySelectorAll('#'+containerId+' .section-menu button');
    [].forEach.call(sectionMenu, function(el) {
        el.onclick = function(e) {
            e.preventDefault();
            let url = el.getAttribute('data-url'),
                handler = el.getAttribute('data-handler'),
                id = el.getAttribute('data-id'),
                expandBtn = el.closest('.expanded-menu-element').querySelector('.expanded-menu'),
                expandContainer = el.closest('.expanded-menu-container'),
                sections = document.querySelectorAll('section.section');

            toggle_visibility(expandBtn, expandContainer.id);
            CONFIG.loader.classList.remove('hidden');
            [].forEach.call(sections, function(section) {
                section.classList.add('hidden');
            });

            setTimeout(function (){
                if (url) {
                    if (id) {
                        containerId = id;
                    }
                    loadData(CONFIG.apiUrl + url).then(
                        response => builderSuccessData(response, containerId, handler),
                        error => errorHandler(error, containerId)
                    );
                } else {
                    if (id) {
                        containerId = id;
                    }
                    builderSuccessData(null, containerId);
                }

            }, 300);
        }
    });
}

function buttonsHandler(url, containerId, handler, updateService) {
    if (!url || url === '' || !containerId || containerId === '' || !handler || handler === '') {
        if (CONFIG.debugging) {
            errorHandler('Не переданы обязательные параметры', containerId, handler, '', '', [
                'url: ' + url, 'containerId: ' + containerId, 'handler: ' + handler
            ]);
        } else {
            errorHandler(null, containerId, handler, null, null);
        }
        return
    }
    CONFIG.loader.classList.remove('hidden');
    pushData(CONFIG.apiUrl + url, null, 'post').then(
        response => builderSuccessData(response, containerId, handler),
        error => errorHandler(error, containerId)
    );

    if (updateService === true) {
        updateEmployeeData(containerId, handler);
    }
}

function filtersHandler(url, containerId, handler, filterContainerId) {
    if (!url || url === '' || !containerId || containerId === '' || !handler || handler === '' || !filterContainerId) {
        if (CONFIG.debugging) {
            errorHandler('Не переданы обязательные параметры', containerId, handler, '', '', [
                'url: ' + url, 'containerId: ' + containerId, 'handler: ' + handler + 'filterContainerId: ' +
                filterContainerId
            ]);
        } else {
            errorHandler(null, containerId, handler, null, null);
        }
        return
    }

    let inputs = document.querySelectorAll('#' + filterContainerId + ' input, select'),
        filter = {},
        in_format = '';

    if (inputs.length > 0) {
        [].forEach.call(inputs, function(el) {
            if (el.name && el.value) {
                filter[el.name] = el.value
            }
        });
    }
    if (filter['in_format']) {
        in_format = filter['in_format'];
        delete filter['in_format'];
    }
    debug()
    debug(in_format)

    CONFIG.loader.classList.remove('hidden');

    if (in_format) {
        CONFIG.loader.classList.add('hidden');
        window.location = CONFIG.apiUrl + url + '/' + in_format + '?' + new URLSearchParams(filter).toString()
    } else {
        pushData(
            CONFIG.apiUrl + url + '?' + new URLSearchParams(filter).toString(),
            null,
            'get'
        ).then(
            response => builderSuccessData(response, containerId, handler),
            error => errorHandler(error, containerId)
        );
    }

}

function dashboardHandler(data, containerId) {
    return new Promise(function(resolve, reject) {
        if (!data || data.list === undefined) {
            reject('Нет данных');
        }

        let container = '<div class="container mx-auto px-4 py-5">',
            children = '',
            currDateString = getCurrentDateString(),
            currDate = new Date(),
            switcher = 'Присутствует',
            switcherColor = 'bg-emerald-500';

        if (data.list.length > 0) {
            container = container + '<ul role="list" class="divide-y divide-gray-100">';
            [].forEach.call(data.list, function(employee) {
                let child = '<li class="flex justify-between gap-x-6 py-5" data-person_id="'+employee.id+'">' +
                    '<div class="flex gap-x-4">' +
                    '   <img class="h-12 w-12 flex-none rounded-full bg-gray-50" ' +
                    '        src="'+CONFIG.apiUrl+'images/persons/'+employee.id+'.jpg" alt="">' +
                    '   <div class="min-w-0 flex-auto">' +
                    '       <p class="text-sm font-semibold leading-6 text-gray-900 text-left">'+employee.display_name+'</p>' +
                    '       <p class="mt-1 truncate text-xs leading-5 text-gray-500 text-left">'+
                    employee.employee_position+
                    '       </p>' +
                    '   </div>' +
                    '</div>';

                let timeGoWork = employee.time_go_work || null;

                if (!timeGoWork) {
                    child = child + '' +
                        '<div class="sm:flex sm:flex-col sm:items-end w-40 min-w-40 text-left">' +
                        '   <p class="text-sm leading-6 text-gray-900">Время прихода: ' +
                        '       <span class="time"><strong>--:--</strong></span>' +
                        '   </p>' +
                        '   <div class="mt-1 flex items-center gap-x-1.5">' +
                        '       <div class="flex-none rounded-full bg-red-500/20 p-1">' +
                        '           <div class="h-1.5 w-1.5 rounded-full bg-red-500"></div>' +
                        '       </div>' +
                        '       <p class="text-xs leading-5 text-gray-500">Отсутствует</p>' +
                        '   </div>' +
                        '</div>' +
                        '</li>';
                    children += child;
                    return;
                }

                let cameOutTime = timeGoWork.came_out_time || '--:--',
                    enteredTime = timeGoWork.entered_time || '--:--';

                if (cameOutTime !== '--:--') {
                    let came_out_time = new Date(currDateString + ' ' + cameOutTime + ':00');
                    if (currDate > came_out_time) {
                        switcher = 'Отсутствует';
                        switcherColor = 'bg-red-500';
                    }
                } else {
                    switcher = 'Присутствует';
                    switcherColor = 'bg-emerald-500';
                    cameOutTime = '--:--'
                }

                child = child + '' +
                    '<div class="sm:flex sm:flex-col sm:items-end w-40 min-w-40 text-left">' +
                    '   <p class="text-sm leading-6 text-gray-900">Время прихода: ' +
                    '       <span class="time"><strong>' + enteredTime + '</strong></span>' +
                    '   </p>' +
                    '   <p class="text-sm leading-6 text-gray-900">Время ухода: ' +
                    '       <span class="time"><strong>' + cameOutTime + '</strong></span>' +
                    '   </p>' +
                    '   <div class="mt-1 flex items-center gap-x-1.5">' +
                    '       <div class="flex-none rounded-full ' + switcherColor + '/20 p-1">' +
                    '           <div class="h-1.5 w-1.5 rounded-full ' + switcherColor + '"></div>' +
                    '       </div>' +
                    '       <p class="text-xs leading-5 text-gray-500">' + switcher + '</p>' +
                    '   </div>' +
                    '</div>' +
                    '</li>';

                children += child;
            });
            children += '</ul>';
        } else {
            children = '<h3 class="text-center mx-auto my-4"> Нет сотрудников</h3>';
        }

        document.querySelector('#dashboard .body').innerHTML = container + children + '</div>';

        resolve(true);
    });
}

function statisticHandler(data, containerId) {
    return new Promise(function(resolve, reject) {
        if (!data || data.list === undefined) {
            reject('Нет данных');
        }

        if (data.list.length > 0) {
            let container = '<div class="container mx-auto px-4 py-5"><div class="flex flex-col">' +
                    '<div class="overflow-x-auto sm:-mx-6 lg:-mx-8">' +
                    '<div class="block min-w-full w-full py-2 sm:px-6 lg:px-8">' +
                    '<div class="overflow-hidden">' +
                    '<table class="block min-w-full w-full text-left text-sm font-light">' +
                    '<thead class="block min-w-full w-full border-b bg-white font-medium ' +
                    'dark:border-neutral-500 dark:bg-neutral-600">' +
                    '<tr class="block min-w-full w-full">' +
                    '<th scope="col" class="text-left w-1/4 px-6 py-4">Дата и время</th>' +
                    '<th scope="col" class="text-left w-full px-6 py-4">ФИО</th>' +
                    '<th scope="col" class="text-left w-1/4 px-6 py-4">Направление</th>' +
                    '</tr></thead><tbody>',
                children = buildChildren(),
                containerEnd = '</tbody></table></div></div></div></div></div>';

            document.querySelector('#statistic .body').innerHTML = container + children + containerEnd;
        } else {
            let container = '<div class="container mx-auto px-4 py-5">' +
                '<h3 class="text-center mx-auto my-4"> Нет статистики</h3>' +
                '</div>';

            document.querySelector('#statistic .body').innerHTML = container;
        }

        function buildChildren() {
            let children = '',
                counter = 0;
            [].forEach.call(data.list, function (employee) {
                let direction = 'Вошел',
                    trBackground = '';
                if (employee.direction === 1) {
                    direction = 'Вышел';
                }

                counter ++

                if (counter % 2 === 0) {
                    trBackground = 'bg-neutral-100';
                } else {
                    trBackground = 'bg-white';
                }

                let child = '' +
                    '<tr class="border-b-2 border-gray-50 ' + trBackground + '">' +
                    '<td class="text-left w-1/4 whitespace-nowrap px-6 py-4">' + employee.visit_date + '</td>' +
                    '<td class="text-left whitespace-nowrap w-full px-6 py-4">' + employee.display_name + '</td>' +
                    '<td class="text-left whitespace-nowrap w-1/4 px-6 py-4">' + direction + '</td>' +
                    '</tr>';
                children += child;
            });

            return children
        }

        resolve(true);
    });
}

function startEndWorkingStatisticHandler(data, containerId) {
    return new Promise(function(resolve, reject) {
        if (!data || data.list === undefined) {
            reject('Нет данных');
        }

        if (data.list) {
            let container = '<div class="container mx-auto px-4 py-5"><div class="flex flex-col">' +
                    '<div class="overflow-x-auto sm:-mx-6 lg:-mx-8">' +
                    '<div class="block min-w-full w-full py-2 sm:px-6 lg:px-8">' +
                    '<div class="overflow-hidden">' +
                    '<table class="block min-w-full w-full text-left text-sm font-light">' +
                    '<thead class="block min-w-full w-full border-b bg-white font-medium ' +
                    'dark:border-neutral-500 dark:bg-neutral-600">' +
                    '<tr class="flex justify-between flex-nowrap min-w-full w-full">' +
                    '<th scope="col" class="flex-1 text-left w-full px-6 py-4">ФИО</th>' +
                    '<th scope="col" class="text-left w-1/4 px-6 py-4">Пришел</th>' +
                    '<th scope="col" class="text-left w-1/4 px-6 py-4">Ушел</th>' +
                    '</tr></thead><tbody class="block min-w-full w-full">',
                children = buildChildren(),
                containerEnd = '</tbody></table></div></div></div></div></div>';

            document.querySelector('#statistic .body').innerHTML = container + children + containerEnd;
        } else {
            let container = '<div class="container mx-auto px-4 py-5">' +
                '<h3 class="text-center mx-auto my-4"> Нет статистики</h3>' +
                '</div>';

            document.querySelector('#statistic .body').innerHTML = container;
        }


        function buildChildren() {
            let children = '',
                counter = 0,
                trBackground = '';

            Object.keys(data.list).map(function(key) {
                let employee = data.list[key];

                let start_date = employee.stat.start_date || '--:--',
                    end_date = employee.stat.end_date || '--:--';

                counter ++

                if (counter % 2 === 0) {
                    trBackground = 'bg-neutral-100';
                } else {
                    trBackground = 'bg-white';
                }

                let child = '' +
                    '<tr class="flex justify-between flex-nowrap min-w-full w-full border-b-2 border-gray-50 ' + trBackground + '">' +
                    '<td class="flex-1 text-left w-auto whitespace-nowrap px-6 py-4">' + employee.display_name + '</td>' +
                    '<td class="text-left whitespace-nowrap w-1/4 px-6 py-4">' + start_date + '</td>' +
                    '<td class="text-left whitespace-nowrap w-1/4 px-6 py-4">' + end_date + '</td>' +
                    '</tr>';
                children += child;
            });

            return children
        }

        resolve(true);
    });
}

function addEmployeeHandler(data, containerId) {
    return new Promise(function(resolve, reject) {
        if (!data || data.employee === undefined || data.employee.id === undefined) {
            reject('Нет данных');
        } else {
            toast(
                'Пользователь добавлен',
                '<ul><li>ФИО: ' + data.employee.display_name + '</li>' +
                '<li>Должность: ' + data.employee.employee_position + '</li></ul>',
                'success'
            );
            updateEmployeeData(containerId, 'addEmployeeHandler');
        }

        resolve(true);
    });
}

function employeesHandler(data, containerId) {
    return new Promise(function(resolve, reject) {
        if (!data || data.list === undefined) {
            reject('Нет данных');
        }

        let container = '<div class="container mx-auto px-4 py-5">',
            children = '';

        if (data.list.length > 0) {
            container += '<ul role="list" class="divide-y divide-gray-100">';

            [].forEach.call(data.list, function(employee) {
                let buttonBlock = '';
                let buttonMoveTrash = '';
                if (employee.status === 2) {
                    buttonBlock = '<button type="submit" class="inline-flex items-center gap-x-1 text-sm font-semibold ' +
                        'leading-6 text-gray-900 inline-flex w-full justify-center rounded-md bg-gray-800 px-3 ' +
                        'py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 sm:ml-3 sm:w-auto"' +
                        ' onclick="buttonsHandler(\'employees/blocked-employee?id=' + employee.id + '\', \'' + containerId +
                        '\', \'employeesHandler\', true)">' +
                        'Разблокировать' +
                        '   </button>';
                } else if (employee.status === 3) {
                    buttonBlock = '<button type="submit" class="inline-flex items-center gap-x-1 text-sm font-semibold ' +
                        'leading-6 text-gray-900 inline-flex w-full justify-center rounded-md bg-gray-800 px-3 ' +
                        'py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 sm:ml-3 sm:w-auto"' +
                        ' onclick="buttonsHandler(\'employees/blocked-employee?id=' + employee.id + '\', \'' + containerId +
                        '\', \'employeesHandler\', true)">' +
                        '   Восстановить' +
                        '   </button>';
                } else {
                    buttonBlock = '<button type="submit" class="inline-flex items-center gap-x-1 text-sm font-semibold ' +
                        'leading-6 text-gray-900 inline-flex w-full justify-center rounded-md bg-gray-800 px-3 ' +
                        'py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 sm:ml-3 sm:w-auto"' +
                    ' onclick="buttonsHandler(\'employees/blocked-employee?id=' + employee.id + '\', \'' + containerId +
                    '\', \'employeesHandler\', true)">' +
                    '   Блокировать' +
                    '   </button>';

                    buttonMoveTrash = '<button type="submit" class="inline-flex items-center gap-x-1 text-sm font-semibold ' +
                        'leading-6 text-gray-900 inline-flex w-full justify-center rounded-md bg-gray-800 px-3 ' +
                        'py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 sm:ml-3 sm:w-auto"' +
                        ' onclick="buttonsHandler(\'employees/move-trash-employee?id=' + employee.id + '\', \'' + containerId +
                        '\', \'employeesHandler\', true)">' +
                        'В корзину' +
                        '   </button>';
                }
                let child = '<li class="flex justify-between gap-x-6 py-5" data-person_id="'+employee.id+'">' +
                    '<div class="flex gap-x-4">' +
                    '   <img class="h-12 w-12 flex-none rounded-full bg-gray-50" ' +
                    '        src="'+CONFIG.apiUrl+'images/persons/'+employee.id+'.jpg" alt="">' +
                    '   <div class="min-w-0 flex-auto">' +
                    '       <p class="text-sm font-semibold leading-6 text-gray-900 text-left">'+employee.display_name+'</p>' +
                    '       <p class="mt-1 truncate text-xs leading-5 text-gray-500 text-left">'+
                    employee.employee_position+
                    '       </p>' +
                    '   </div>' +
                    '</div>' +
                    '<div class="employee-buttons sm:flex sm:flex-row min-w-40">' + buttonBlock + buttonMoveTrash +
                    '   <button type="submit" class="inline-flex items-center gap-x-1 text-sm font-semibold ' +
                    'leading-6 text-gray-900 inline-flex w-full justify-center rounded-md bg-gray-800 px-3 ' +
                    'py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-600 sm:ml-3 sm:w-auto"' +
                    ' onclick="buttonsHandler(\'employees/remove-employee?id=' + employee.id + '\', \'' + containerId +
                    '\', \'employeesHandler\', true)">' +
                    '   Удалить' +
                    '   </button>' +
                    '</div>' +
                    '</li>';

                children += child;
            });
            children += '</ul>';
        } else {
            children = '<h3 class="text-center mx-auto my-4"> Нет сотрудников</h3>';
        }

        document.querySelector('#employees .body').innerHTML = container + children + '</div>';

        resolve(true);
    });
}

function loadData(url) {
    return new Promise(function(resolve, reject) {
        if (!url) {
            reject('Не передан URL');
        }
        fetch(url, {
            method: 'get',
            headers: {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin':'*',
                'Access-Control-Allow-Methods':'*',
                'Access-Control-Allow-Credentials':'ture',
                'Content-Type': 'application/json',
                'AuthKey': CONFIG.apiKey,
            },
        }).then((response) => {
            resolve(response);
        }).catch((error) => {
            reject(error);
        });
    });
}

function pushData(url, formData, method) {
    return new Promise(function(resolve, reject) {
        if (!url) {
            reject('Не передан URL');
        }
        let headers = {'AuthKey': CONFIG.apiKey},
            params = {
                method: method || 'get',
                headers: headers,
            };

        if (formData) {
            params['body'] = formData;
        }

        if (CONFIG.debugging) {
            debug(params)
        }

        fetch(url, params).then((response) => {
            resolve(response);
        }).catch((error) => {
            CONFIG.loader.classList.add('hidden');
            if (CONFIG.debugging) {
                errorHandler(error);
            } else {
                errorHandler();
            }
            reject(error);
        });
    });
}

function processForm(form) {
    if (form.preventDefault) {
        form.preventDefault();
    }
    let inputs = form.target.elements || null,
        method = form.target.method || null,
        url = form.target.getAttribute('data-url') || null,
        id = form.target.getAttribute('data-id') || null,
        handler = form.target.getAttribute('data-handler') || null,
        data = {},
        emptyInputs = [];

    if (!inputs || !url || !id || !handler) {
        if (CONFIG.debugging) {
            errorHandler(
                'processForm',
                id,
                handler,
                'В форме нет обязательных данных',
                '<ul><li>url : '+url+'</li><li>id : '+id+'</li><li>handler : '+handler+'</li>' +
                '<li>method : '+method+'</li><li>inputs : '+inputs+'</li></ul>'
            )
        } else {
            errorHandler('', '', '', 'Ошибка',
                'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку'
            );
        }
    }

    if (!method) {
        method = 'get';
    }

    [].forEach.call(inputs, function (input) {
        let name = input.getAttribute('name') || null,
            value;

        if (!name) {
            return;
        }

        if (input.type === 'file') {
            value = input.files;
        } else {
            value = input.value || '';
            value = value.trim();
        }

        if (input.getAttribute('required') && input.type !== 'file' && value === '') {
            emptyInputs.push(input.getAttribute('placeholder') || name);
        }
        data[name] = value;
    });

    if (emptyInputs.length > 0) {
        toast(
            'Заполните обязательные поля',
            '<ul><li>' + emptyInputs.join('</li>') + '</li></ul>',
            'error'
        );
    }

    const formData = new FormData(form.target);

    CONFIG.loader.classList.remove('hidden');
    pushData(CONFIG.apiUrl + url, formData, method).then(
        response => {
            builderSuccessData(response, id, handler);
            form.target.reset();
        },
        error => errorHandler(error, id, handler)
    );

    return false;
}

function formListener(forms) {
    [].forEach.call(forms, function(form) {
        if (form.attachEvent) {
            form.attachEvent("submit", processForm);
        } else {
            form.addEventListener("submit", processForm);
        }
    });
}


function updateEmployeeData(containerId, handler) {
    setTimeout(function () {
        pushData(CONFIG.apiUrl + CONFIG.updateEmployeeDataUrl, null, 'post').then(
            response => function () {
                response.json().then(function(data) {
                    if (CONFIG.debugging) {
                        if (data.messages) {
                            messagesHandler(data.messages, containerId, handler)
                        } else {
                            debug('updateEmployeeData: ');
                            debug(data);
                        }
                    }
                });
            },
            error => errorHandler(error, containerId)
        );
    }, 1000);
}

function builderSuccessData(response, containerId, handler, showContainer) {
    let container = document.querySelector('#' + containerId);
    if (showContainer !== false) {
        showContainer = true
    }
    if (!container) {
        errorHandler(
            'Нет контейнера',
            containerId,
            handler,
            'Ошибка',
            'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку'
        )
        return;
    }
    if (container.length === 0) {
        if (showContainer) {
            container.classList.remove('hidden');
        }

        CONFIG.loader.classList.add('hidden');
        errorHandler(
            'Нет контейнера',
            containerId,
            handler,
            'Ошибка',
            'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку'
        )
        return;
    }
    if (!response || !handler) {
        if (showContainer) {
            container.classList.remove('hidden');
        }
        CONFIG.loader.classList.add('hidden');
        return;
    }

    try {
        response.json().then(function(data) {
            if (CONFIG.debugging) {
                debug('builderSuccessData: ');
                debug(data);
            }

            try {
                let commonHandler = eval(handler);
                if (data.messages) {
                    messagesHandler(data.messages, containerId, handler)
                }
                commonHandler(data, containerId).then(
                    function () {
                        if (CONFIG.debugging) {
                            toast(
                                'Секция: ' + containerId,
                                'Данные успешно загружены <br/> Обработчик: ' + handler,
                                'success'
                            );
                        }
                        if (showContainer) {
                            container.classList.remove('hidden');
                        }
                        CONFIG.loader.classList.add('hidden');
                    },
                    error => errorHandler(
                        error,
                        containerId,
                        handler,
                        'Ошибка',
                        'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку',
                        data.messages
                    )
                );
            } catch (err) {
                if (showContainer) {
                    container.classList.remove('hidden');
                }
                CONFIG.loader.classList.add('hidden');
                errorHandler(
                    err,
                    containerId,
                    handler,
                    'Ошибка',
                    'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку'
                );
            }
        });
    } catch (e) {
        debug(e)
    }
}

function errorHandler(error, containerId, handler, title, body, messages) {
    CONFIG.loader.classList.add('hidden');
    if (!title) {
        title = 'Ошибка';
    }
    if (!body) {
        body = 'Попробуйте перезагрузить страницу или обратитесь в техническую поддержку';
    }

    let mess = '';
    if (messages) {
        mess = '<br/> Сообщения: <br/><ul><li>' + messages.join('</li><li>') + '</li></ul>';
    }

    if (CONFIG.debugging) {
        debug(error);
        debug(containerId);
        toast(
            'Секция: ' + containerId,
            'Обработчик: ' + handler + '<br/> Ошибка: <br/>' + error + mess,
            'error'
        );
    } else {
        toast(title, body + mess , 'error');
    }
}

function messagesHandler(messages, containerId, handler, title) {
    CONFIG.loader.classList.add('hidden');
    if (!title) {
        title = 'Сообщения';
    }
    if (!messages || messages.length === 0) {
        return;
    }
    if (CONFIG.debugging) {
        debug(messages);
        debug(containerId);
        toast(
            'Секция: ' + containerId,
            'Обработчик: ' + handler + '<br/> Сообщения: <br/>' +
            '<ul><li>' + messages.join('</li><li>') + '</li></ul>',
            'success'
        );
    } else {
        toast(title, '<ul><li>' + messages.join('</li>') + '</li></ul>', 'success');
    }
}
